"""Pages of a litter and of its dogs at the Centrale Canine, shaped like the real JSON, without network."""

from typing import Any

import httpx

from services.collectors.scc_dogs import SccDogCollector

# The recorded gold litter 4333817 (Élevage D): its page, its parents, its registered puppies.
GOLD_LITTER_SCC_ID = "2834593"
GOLD_FATHER_NODE_ID = "3692569"
GOLD_MOTHER_NODE_ID = "3606226"
GOLD_FATHER_DOG_ID = "7000001"
GOLD_MOTHER_DOG_ID = "7000002"
GOLD_PUPPY_IDS = ("8000001", "8000002", "8000003")

# The recorded litter 4320577 of the colour bundle 159 (Élevage C): a black and tan father, a gold mother.
BUNDLE_LITTER_SCC_ID = "2832966"
BUNDLE_FATHER_NODE_ID = "1542322"
BUNDLE_MOTHER_NODE_ID = "3127968"
BUNDLE_FATHER_DOG_ID = "7000003"
BUNDLE_MOTHER_DOG_ID = "7000004"

# The recorded expected litter 4337070 (Élevage A), not born yet: two gold parents, no puppy registered.
EXPECTED_LITTER_SCC_ID = "2834968"
EXPECTED_FATHER_NODE_ID = "2895638"
EXPECTED_MOTHER_NODE_ID = "2804897"
EXPECTED_FATHER_DOG_ID = "7000005"
EXPECTED_MOTHER_DOG_ID = "7000006"

EMPTY_LITTER_PAGE: dict[str, Any] = {"main_content": {}, "node": {}, "dogs": []}


def dog_node(node_id: str, dog_id: str, name: str, is_male: bool) -> dict[str, Any]:
    """
    The node of a parent as a litter page lists it.

    Args:
        node_id: The Drupal node identifier the litter references.
        dog_id: The LOF Select identifier of the dog.
        name: Its name, in capitals as published.
        is_male: Its sex.

    Returns:
        The node.
    """
    return {
        "n_type": "dog",
        "n_dog_id": dog_id,
        "n_name": name,
        "n_gender": is_male,
        "n_identifier": "250000000000000",
        "n_lof": "000000/00000",
        "url": f"/chien/{name.lower().replace(' ', '-')}-{dog_id}",
    }


def puppy_entry(dog_id: str, name: str, identifier: str) -> dict[str, Any]:
    """
    One registered puppy of the ``dogs`` block.

    Args:
        dog_id: The LOF Select identifier of the puppy.
        name: Its name, in capitals as published.
        identifier: Its chip.

    Returns:
        The entry.
    """
    return {"n_id": identifier, "n_name": name, "n_description": "", "url": f"{name.lower()}-{dog_id}"}


def litter_page(
    scc_litter_id: str,
    father_node_id: str,
    father_dog_id: str,
    mother_node_id: str,
    mother_dog_id: str,
    males: list[dict[str, Any]],
    females: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    The page of a litter: its parents as nodes, its registered puppies by sex.

    Args:
        scc_litter_id: ``n_litter_id``.
        father_node_id: The node the litter references for its father.
        father_dog_id: The father's LOF Select identifier.
        mother_node_id: The node the litter references for its mother.
        mother_dog_id: The mother's LOF Select identifier.
        males: Registered male puppies.
        females: Registered female puppies.

    Returns:
        The page.
    """
    return {
        "main_content": {
            "n_id": f"4{scc_litter_id}",
            "n_litter_id": [int(scc_litter_id)],
            "n_father": [int(father_node_id)],
            "n_mother": [int(mother_node_id)],
            "n_father_name": "Père de test",
            "n_mother_name": "Mère de test",
            "url": f"/portee/{scc_litter_id}",
        },
        "node": {
            father_node_id: dog_node(father_node_id, father_dog_id, "PÈRE DE TEST", True),
            mother_node_id: dog_node(mother_node_id, mother_dog_id, "MÈRE DE TEST", False),
        },
        "dogs": {
            "male": {f"n{entry['url']}": entry for entry in males},
            "female": {f"n{entry['url']}": entry for entry in females},
        },
    }


def dog_page(
    dog_id: str,
    name: str,
    is_male: bool,
    color_code: str,
    health_codes: list[str],
    rating: str = "1",
    birth_date: str = "05/07/2026",
    sire_id: str | None = None,
    dam_id: str | None = None,
) -> dict[str, Any]:
    """
    The page of a dog, with the owner block the collector must never keep.

    Args:
        dog_id: The LOF Select identifier.
        name: Its name, in capitals as published.
        is_male: Its sex.
        color_code: ``couleur`` as LOF Select writes it.
        health_codes: Codes of its health tests.
        rating: ``cotation``.
        birth_date: ``dateNaissance``, French.
        sire_id: Its father's identifier, if known.
        dam_id: Its mother's identifier, if known.

    Returns:
        The page.
    """
    return {
        "url": f"/chien/{name.lower().replace(' ', '-')}-{dog_id}",
        "breeder": {"u_farming_affix": "DU CLOS DE TEST"},
        "ws": {
            "chien": {
                "id": int(dog_id),
                "nom": name,
                "affixe": "DU CLOS DE TEST",
                "nomComplet": f"{name.title()} du Clos de Test",
                "sexeMale": "O" if is_male else "N",
                "dateNaissance": birth_date,
                "cotation": rating,
                "puce": f"2500000000{dog_id}",
                "idVariete": 345,
                "couleur": color_code,
                "numLof": f"3{dog_id[-5:]}",
                "adn": [{"code": "DNA", "empreinte": "O"}],
                "santes": [{"code": code, "libelle": code} for code in health_codes],
                "pere": {"id": int(sire_id), "couleur": "F.Or."} if sire_id else None,
                "mere": {"id": int(dam_id), "couleur": "F.Cl."} if dam_id else None,
                "proprio": {"denomination": "PROPRIÉTAIRE DE TEST", "nomMail1": "jamais@garde.fr", "mobile": "0600"},
            },
            "race": {"nom": "Cocker spaniel anglais"},
        },
    }


def recorded_litter_pages() -> dict[str, dict[str, Any]]:
    """The pages of the two litters of the tests, by ``n_litter_id``."""
    return {
        GOLD_LITTER_SCC_ID: litter_page(
            GOLD_LITTER_SCC_ID,
            GOLD_FATHER_NODE_ID,
            GOLD_FATHER_DOG_ID,
            GOLD_MOTHER_NODE_ID,
            GOLD_MOTHER_DOG_ID,
            males=[puppy_entry(GOLD_PUPPY_IDS[0], "BALTI", "250000000000001")],
            females=[
                puppy_entry(GOLD_PUPPY_IDS[1], "BELLA", "250000000000002"),
                puppy_entry(GOLD_PUPPY_IDS[2], "BONNIE", "250000000000003"),
            ],
        ),
        BUNDLE_LITTER_SCC_ID: litter_page(
            BUNDLE_LITTER_SCC_ID,
            BUNDLE_FATHER_NODE_ID,
            BUNDLE_FATHER_DOG_ID,
            BUNDLE_MOTHER_NODE_ID,
            BUNDLE_MOTHER_DOG_ID,
            males=[],
            females=[],
        ),
        EXPECTED_LITTER_SCC_ID: litter_page(
            EXPECTED_LITTER_SCC_ID,
            EXPECTED_FATHER_NODE_ID,
            EXPECTED_FATHER_DOG_ID,
            EXPECTED_MOTHER_NODE_ID,
            EXPECTED_MOTHER_DOG_ID,
            males=[],
            females=[],
        ),
    }


def recorded_dog_pages() -> dict[str, dict[str, Any]]:
    """The pages of the parents and the puppies of the tests, by LOF Select identifier."""
    return {
        GOLD_FATHER_DOG_ID: dog_page(GOLD_FATHER_DOG_ID, "PÈRE GOLD", True, "F.Or.", ["FN-1.1", "LocE-e/e"], "4"),
        GOLD_MOTHER_DOG_ID: dog_page(GOLD_MOTHER_DOG_ID, "MÈRE GOLD", False, "F.Cl.", ["PRCD-1.1"], "2"),
        GOLD_PUPPY_IDS[0]: dog_page(GOLD_PUPPY_IDS[0], "BALTI", True, "F.Or.", [], "0"),
        GOLD_PUPPY_IDS[1]: dog_page(GOLD_PUPPY_IDS[1], "BELLA", False, "F.Or.", [], "0"),
        GOLD_PUPPY_IDS[2]: dog_page(GOLD_PUPPY_IDS[2], "BONNIE", False, "F.Fo.", [], "0"),
        BUNDLE_FATHER_DOG_ID: dog_page(BUNDLE_FATHER_DOG_ID, "PÈRE NOIR", True, "Noi. Mar.Fau.", ["LocE-E/e"], "3"),
        BUNDLE_MOTHER_DOG_ID: dog_page(BUNDLE_MOTHER_DOG_ID, "MÈRE GOLD", False, "F.Or.", [], "1"),
        EXPECTED_FATHER_DOG_ID: dog_page(EXPECTED_FATHER_DOG_ID, "PÈRE DORÉ", True, "F.Or.", ["LocE-e/e"], "2"),
        EXPECTED_MOTHER_DOG_ID: dog_page(EXPECTED_MOTHER_DOG_ID, "MÈRE DORÉE", False, "F.Cl.", [], "1"),
    }


def answer_dog_request(request: httpx.Request) -> httpx.Response:
    """
    Serve a litter or a dog page like the real endpoints; an unknown litter is an empty one, an unknown dog a 404.

    Args:
        request: The collector's request.

    Returns:
        The JSON page.
    """
    path = request.url.path
    identifier = path.rsplit("/", 1)[1]
    if "/api/litter/" in path:
        return httpx.Response(200, json=recorded_litter_pages().get(identifier, EMPTY_LITTER_PAGE))
    page = recorded_dog_pages().get(identifier)
    if page is None:
        return httpx.Response(404)
    return httpx.Response(200, json=page)


def dog_collector_serving(requests: list[httpx.Request] | None = None) -> SccDogCollector:
    """
    A collector that gets the pages above, without pausing between pages.

    Args:
        requests: Filled with every request sent, when given.

    Returns:
        The collector.
    """

    def answer(request: httpx.Request) -> httpx.Response:
        """
        Record the request and serve its page.

        Args:
            request: The collector's request.

        Returns:
            The JSON page.
        """
        if requests is not None:
            requests.append(request)
        return answer_dog_request(request)

    return SccDogCollector(http_client=httpx.Client(transport=httpx.MockTransport(answer)), sleep=lambda _seconds: None)
