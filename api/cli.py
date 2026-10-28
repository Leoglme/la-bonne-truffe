"""
Command line for the operations done by hand: database setup, VAPID keys, test push.

Run ``python cli.py --help`` for the list of commands.
"""

import argparse
import sys

from core.config import settings
from core.database import SessionLocal, engine
from migrations.run_migrations import MigrationRunner
from seeders.run_seeders import SeederRunner
from services.auth_service import AuthService
from services.push_service import push_service
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

    def run(self, arguments: list[str]) -> int:
        """
        Run the command named in the arguments.

        Args:
            arguments: Command-line arguments, program name excluded.

        Returns:
            Exit code.
        """
        parsed = self.build_parser().parse_args(arguments)
        handlers = {
            "init-db": self.init_database,
            "vapid-keys": self.print_vapid_keys,
            "push-test": self.send_test_push,
        }
        return handlers[parsed.command]()


if __name__ == "__main__":
    sys.exit(CommandLine().run(sys.argv[1:]))
