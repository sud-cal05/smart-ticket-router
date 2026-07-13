"""Loads and validates taxonomy.yaml once at import. A bad taxonomy fails here,
loudly, rather than silently misrouting tickets later."""

from pathlib import Path

import yaml

_TAXONOMY_PATH = Path(__file__).parent.parent / "taxonomy.yaml"


def load_taxonomy() -> dict:
    with open(_TAXONOMY_PATH) as f:
        taxonomy = yaml.safe_load(f)

    valid_teams = set(taxonomy["teams"])
    for name, cat in taxonomy["categories"].items():
        if cat["team"] not in valid_teams:
            raise ValueError(
                f"Category '{name}' maps to unknown team '{cat['team']}'. "
                f"Valid teams: {valid_teams}"
            )
    return taxonomy


TAXONOMY = load_taxonomy()
CATEGORY_NAMES = list(TAXONOMY["categories"].keys())
