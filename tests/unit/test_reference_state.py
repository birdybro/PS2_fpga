"""Directed tests for reference provenance and clean-room policy."""

from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from scripts.check_references import validate_references

REPO_ROOT = Path(__file__).resolve().parents[2]


def load_catalog() -> dict:
    """Load a fresh copy of the repository reference catalog."""
    return yaml.safe_load((REPO_ROOT / "references.yaml").read_text(encoding="utf-8"))


def load_document() -> str:
    """Load the human-readable source catalog."""
    return (REPO_ROOT / "REFERENCES.md").read_text(encoding="utf-8")


@pytest.mark.unit
def test_repository_reference_catalog_is_valid() -> None:
    """Keep source metadata, clean-room policy, and documentation synchronized."""
    assert validate_references(load_catalog(), load_document()) == []


@pytest.mark.unit
def test_reference_catalog_rejects_duplicate_ids() -> None:
    """Prevent ambiguous provenance references."""
    catalog = deepcopy(load_catalog())
    catalog["references"].append(deepcopy(catalog["references"][0]))

    errors = validate_references(catalog, load_document())
    assert any("duplicate reference IDs" in error for error in errors)


@pytest.mark.unit
def test_reference_catalog_requires_all_prohibited_material_classes() -> None:
    """Do not allow a catalog edit to weaken the legal exclusion policy."""
    catalog = deepcopy(load_catalog())
    catalog["policy"]["prohibited_material"].remove("confidential-documentation")

    errors = validate_references(catalog, load_document())
    assert any("confidential-documentation" in error for error in errors)


@pytest.mark.unit
def test_reference_catalog_rejects_unsafe_url_and_stale_documentation() -> None:
    """Require public HTTPS links and a synchronized human-readable entry."""
    catalog = deepcopy(load_catalog())
    reference = catalog["references"][0]
    reference["url"] = "https://user:password@example.invalid/reference"
    document = load_document().replace(f"<!-- ref:{reference['id']} -->", "")

    errors = validate_references(catalog, document)
    assert any("without credentials" in error for error in errors)
    assert any("REFERENCES.md is missing markers" in error for error in errors)
