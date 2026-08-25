#!/usr/bin/env python3
"""Validate reference metadata, clean-room policy, and documentation links."""

import re
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = REPO_ROOT / "references.yaml"
DOCUMENT_PATH = REPO_ROOT / "REFERENCES.md"
REFERENCE_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DOCUMENT_MARKER = re.compile(r"<!-- ref:([a-z0-9]+(?:-[a-z0-9]+)*) -->")
REQUIRED_FIELDS = {
    "id",
    "title",
    "url",
    "source_class",
    "role",
    "subsystems",
    "license",
    "source_code_consulted",
    "redistribution",
    "consulted_sections",
    "notes",
}
REQUIRED_PROHIBITIONS = {
    "bios-images",
    "game-images",
    "proprietary-sdk-material",
    "leaked-source-code",
    "confidential-documentation",
    "cryptographic-keys",
    "circumvention-material",
}
ALLOWED_SOURCE_CLASSES = {
    "official-publication",
    "official-project",
    "independent-documentation",
    "public-archive",
    "public-mailing-list",
    "tool-documentation",
}
ALLOWED_ROLES = {"architecture", "toolchain", "verification"}
ALLOWED_REDISTRIBUTION = {"link-only", "dependency-cache"}


def _validate_policy(policy: Any) -> list[str]:
    """Validate the repository-wide legal and provenance policy."""
    if not isinstance(policy, dict):
        return ["policy must be a mapping"]
    errors: list[str] = []
    prohibited = policy.get("prohibited_material")
    if not isinstance(prohibited, list):
        errors.append("policy.prohibited_material must be a list")
    else:
        missing = sorted(REQUIRED_PROHIBITIONS - set(prohibited))
        if missing:
            errors.append(f"policy is missing prohibited material: {', '.join(missing)}")
    if policy.get("local_cache_policy") != "untracked-only":
        errors.append("policy.local_cache_policy must be untracked-only")
    if policy.get("emulator_source_policy") != "license-review-required":
        errors.append("policy.emulator_source_policy must require license review")
    return errors


def _validate_string_fields(reference_id: str, reference: dict[str, Any]) -> list[str]:
    """Validate scalar text fields and enumerated classifications."""
    errors: list[str] = []
    for field in ("title", "url", "license", "notes"):
        if not isinstance(reference[field], str) or not reference[field].strip():
            errors.append(f"{reference_id}.{field} must be a nonempty string")
    if reference["source_class"] not in ALLOWED_SOURCE_CLASSES:
        errors.append(f"{reference_id}.source_class is invalid")
    if reference["role"] not in ALLOWED_ROLES:
        errors.append(f"{reference_id}.role is invalid")
    if reference["redistribution"] not in ALLOWED_REDISTRIBUTION:
        errors.append(f"{reference_id}.redistribution is invalid")
    return errors


def _validate_reference(index: int, reference: Any) -> tuple[list[str], str | None]:
    """Validate one catalog entry."""
    location = f"references[{index}]"
    if not isinstance(reference, dict):
        return [f"{location} must be a mapping"], None
    missing = REQUIRED_FIELDS - reference.keys()
    if missing:
        return [f"{location} is missing fields: {', '.join(sorted(missing))}"], None

    reference_id = reference["id"]
    if not isinstance(reference_id, str) or not REFERENCE_ID.fullmatch(reference_id):
        return [f"{location}.id is invalid: {reference_id!r}"], None

    errors = _validate_string_fields(reference_id, reference)
    url = urlsplit(reference["url"]) if isinstance(reference["url"], str) else None
    if url is None or url.scheme != "https" or not url.netloc or url.username is not None:
        errors.append(f"{reference_id}.url must be a public HTTPS URL without credentials")
    if not isinstance(reference["source_code_consulted"], bool):
        errors.append(f"{reference_id}.source_code_consulted must be boolean")
    for field in ("subsystems", "consulted_sections"):
        values = reference[field]
        if not isinstance(values, list) or not values:
            errors.append(f"{reference_id}.{field} must be a nonempty list")
        elif not all(isinstance(value, str) and value.strip() for value in values):
            errors.append(f"{reference_id}.{field} contains an invalid value")
        elif len(values) != len(set(values)):
            errors.append(f"{reference_id}.{field} contains duplicates")
    if (
        isinstance(reference["license"], str)
        and reference["license"].lower().startswith("not specified")
        and reference["redistribution"] != "link-only"
    ):
        errors.append(f"{reference_id} with unspecified license must remain link-only")
    return errors, reference_id


def _validate_document_markers(ids: list[str], document_text: str) -> list[str]:
    """Require a unique human-readable catalog marker for every source."""
    markers = DOCUMENT_MARKER.findall(document_text)
    errors: list[str] = []
    duplicates = sorted(marker for marker, count in Counter(markers).items() if count > 1)
    if duplicates:
        errors.append(f"duplicate REFERENCES.md markers: {', '.join(duplicates)}")
    missing = sorted(set(ids) - set(markers))
    if missing:
        errors.append(f"REFERENCES.md is missing markers: {', '.join(missing)}")
    unknown = sorted(set(markers) - set(ids))
    if unknown:
        errors.append(f"REFERENCES.md has unknown markers: {', '.join(unknown)}")
    return errors


def validate_references(data: Any, document_text: str) -> list[str]:
    """Return all catalog, policy, and documentation errors."""
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        return ["schema_version must be 1"]
    errors = _validate_policy(data.get("policy"))
    references = data.get("references")
    if not isinstance(references, list) or not references:
        return [*errors, "references must be a nonempty list"]

    ids: list[str] = []
    for index, reference in enumerate(references):
        entry_errors, reference_id = _validate_reference(index, reference)
        errors.extend(entry_errors)
        if reference_id is not None:
            ids.append(reference_id)
    duplicates = sorted(reference_id for reference_id, count in Counter(ids).items() if count > 1)
    if duplicates:
        errors.append(f"duplicate reference IDs: {', '.join(duplicates)}")
    errors.extend(_validate_document_markers(ids, document_text))
    return errors


def main() -> int:
    data = yaml.safe_load(CATALOG_PATH.read_text(encoding="utf-8"))
    document_text = DOCUMENT_PATH.read_text(encoding="utf-8")
    errors = validate_references(data, document_text)
    if errors:
        print("Reference catalog validation failed:")
        for error in errors:
            print(f"  {error}")
        return 1
    print(f"reference catalog: {len(data['references'])} sources and clean-room policy valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
