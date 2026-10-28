"""
Command line for the operations done by hand: database setup, VAPID keys, test push, collection.

Run ``python cli.py --help`` for the list of commands.
"""

import argparse
import json
import sys
from pathlib import Path

from core.config import settings
from core.database import SessionLocal, engine
from enums.listing_kind import ListingKind
from enums.source_run_status import SourceRunStatus
from migrations.run_migrations import MigrationRunner
from models.breed import Breed
from seeders.run_seeders import SeederRunner
from services.auth_service import AuthService
from services.collection_runner import CentraleCanineRunReport, collection_runner
from services.collectors.centrale_canine import CentraleCanineCollector, CentraleCanineError
from services.collectors.raw_listing import RawListing
from services.push_service import push_service
from services.scc_reference_sync import scc_reference_sync
from services.vapid_key_generator import VapidKeyGenerator


class CommandLine:
    """Parses the arguments and runs the matching command."""

    def build_parser(self) -> argparse.ArgumentParser:
        """
        Describe the commands.

        Returns:
            The argument parser.
        """
        parser = argparse.ArgumentParser(prog="cli.py", description="La Bonne Truffe — commandes à la main")
        commands = parser.add_subparsers(dest="command", required=True)
        commands.add_parser("init-db", help="Appliquer les migrations puis les seeders")
        commands.add_parser("vapid-keys", help="Générer une paire de clés VAPID à coller dans .env")
        commands.add_parser("push-test", help="Envoyer une notification de test à l'utilisateur du .env")
        collect = commands.add_parser("collect", help="Relever la Centrale Canine maintenant et afficher les portées")
        collect.add_argument(
            "--save-raw",
            type=Path,
            metavar="DOSSIER",
            help="Enregistrer chaque page JSON reçue dans ce dossier (fixtures de test)",
        )
        commands.add_parser(
            "scc-sync", help="Lire les identifiants de département et de variété sur la page Centrale Canine"
        )
        return parser

    def init_database(self) -> int:
        """
        Apply the pending migrations, then the seeders.

        Returns:
            Exit code.
        """
        applied = MigrationRunner(engine).run()
        print("Migrations appliquées : " + (", ".join(applied) if applied else "aucune, base à jour"))
        db = SessionLocal()
        try:
            for seeder_name, created_count in SeederRunner.run(db).items():
                print(f"Seeder {seeder_name} : {created_count} ligne(s) créée(s)")
        finally:
            db.close()
        return 0

    def print_vapid_keys(self) -> int:
        """
        Print a new VAPID key pair in ``.env`` format.

        Returns:
            Exit code.
        """
        key_pair = VapidKeyGenerator.generate()
        print(f"VAPID_PUBLIC_KEY={key_pair.public_key}")
        print(f"VAPID_PRIVATE_KEY_B64={key_pair.private_key_b64}")
        return 0

    def send_test_push(self) -> int:
        """
        Push a test notification to every browser of the ``.env`` user.

        Returns:
            Exit code: 1 when the user is missing or nothing was delivered.
        """
        db = SessionLocal()
        try:
            user = AuthService.get_user_by_email(db, settings.admin_email)
            if user is None:
                print(f"Aucun utilisateur {settings.admin_email} : lancer d'abord « python cli.py init-db ».")
                return 1
            result = push_service.send(
                db, user.id, "La Bonne Truffe", "Notification de test : la truffe est à l'affût.", "/"
            )
        finally:
            db.close()
        print(f"Délivrées : {result.delivered}, échouées : {result.failed}")
        for detail in result.details:
            print(f"  {detail}")
        return 0 if result.delivered > 0 else 1

    def collect_centrale_canine(self, raw_pages_directory: Path | None) -> int:
        """
        Run a Centrale Canine collection now and print the litters found.

        Args:
            raw_pages_directory: Folder where each received JSON page is written, if given.

        Returns:
            Exit code: 1 when the run failed.
        """
        db = SessionLocal()
        try:
            report = collection_runner.run_centrale_canine(db, CentraleCanineCollector())
            self._print_run_report(report)
            if raw_pages_directory is not None:
                self._save_raw_pages(report, raw_pages_directory)
            return 0 if report.source_run.status == SourceRunStatus.OK else 1
        finally:
            db.close()

    def sync_scc_references(self) -> int:
        """
        Read the breed page of every breed and fill the missing department and variety identifiers.

        Returns:
            Exit code: 1 when a page could not be read.
        """
        collector = CentraleCanineCollector()
        db = SessionLocal()
        try:
            breeds = db.query(Breed).filter(Breed.is_active.is_(True), Breed.scc_slug.is_not(None)).all()
            for breed in breeds:
                try:
                    html = collector.fetch_breed_page_html(breed.scc_slug or "")
                except CentraleCanineError as error:
                    print(f"{breed.name_fr} : {error}")
                    return 1
                result = scc_reference_sync.sync(db, breed, html)
                print(f"{breed.name_fr} : {len(result.department_term_ids_set)} département(s) renseigné(s)")
                for variety_label, variety_id in result.variety_ids_set.items():
                    print(f"  variété « {variety_label} » = {variety_id}")
                for status_option in result.birth_statuses:
                    print(f"  filtre Portées : « {status_option.label} » = {status_option.value or '(vide)'}")
            return 0
        finally:
            db.close()

    @staticmethod
    def _print_run_report(report: CentraleCanineRunReport) -> None:
        """
        Print the outcome of a run and one line per litter found.

        Args:
            report: The run report.
        """
        source_run = report.source_run
        if report.plan.departments_without_term_id:
            print(
                "Départements sans identifiant Centrale Canine, non relevés : "
                + ", ".join(report.plan.departments_without_term_id)
                + " (lancer « python cli.py scc-sync »)"
            )
        if source_run.status != SourceRunStatus.OK:
            print(f"Relevé en échec : {source_run.error_message}")
            return
        print(
            f"Relevé terminé : {source_run.listings_seen} portée(s) vue(s), "
            f"{source_run.listings_new} nouvelle(s), {source_run.listings_changed} modifiée(s), "
            f"{len(report.summary.deactivated_listing_ids)} disparue(s)."
        )
        for listing in sorted(report.collection.listings, key=CommandLine._listing_sort_key):
            print("  " + CommandLine._describe_listing(listing))

    @staticmethod
    def _listing_sort_key(listing: RawListing) -> tuple[str, str]:
        """
        Order the litters by department, then by birth or mating date.

        Args:
            listing: A listing found.

        Returns:
            The sort key.
        """
        known_date = listing.birth_date or listing.mating_date
        return (listing.department_code or "", known_date.isoformat() if known_date else "")

    @staticmethod
    def _describe_listing(listing: RawListing) -> str:
        """
        One readable line per litter; an unknown fact is written « ? », never guessed.

        Args:
            listing: A listing found.

        Returns:
            The line.
        """
        if listing.kind == ListingKind.LITTER_BORN:
            status = f"née le {listing.birth_date or '?'}, {listing.male_count} ♂ {listing.female_count} ♀"
        else:
            status = f"à naître, saillie du {listing.mating_date or '?'}"
        return (
            f"[{listing.department_code}] {listing.color_text or 'couleur ?'} · {status} · "
            f"père {listing.sire_name or '?'} ({listing.sire_rating or '?'}/6), "
            f"mère {listing.dam_name or '?'} ({listing.dam_rating or '?'}/6) · {listing.external_url or ''}"
        )

    @staticmethod
    def _save_raw_pages(report: CentraleCanineRunReport, directory: Path) -> None:
        """
        Write each received JSON page as is, to record real fixtures.

        Args:
            report: The run report.
            directory: Destination folder, created if needed.
        """
        directory.mkdir(parents=True, exist_ok=True)
        for raw_page in report.collection.raw_pages:
            file_name = f"{raw_page.scc_slug}_{raw_page.department_code}_page_{raw_page.page_number}.json"
            (directory / file_name).write_text(
                json.dumps(raw_page.payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        print(f"{len(report.collection.raw_pages)} page(s) JSON enregistrée(s) dans {directory}")

    def run(self, arguments: list[str]) -> int:
        """
        Run the command named in the arguments.

        Args:
            arguments: Command-line arguments, program name excluded.

        Returns:
            Exit code.
        """
        parsed = self.build_parser().parse_args(arguments)
        if parsed.command == "collect":
            return self.collect_centrale_canine(parsed.save_raw)
        handlers = {
            "init-db": self.init_database,
            "vapid-keys": self.print_vapid_keys,
            "push-test": self.send_test_push,
            "scc-sync": self.sync_scc_references,
        }
        return handlers[parsed.command]()


if __name__ == "__main__":
    sys.exit(CommandLine().run(sys.argv[1:]))
