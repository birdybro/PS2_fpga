#!/usr/bin/env python3
"""Reject tracked build products, caches, firmware, and media images."""

import subprocess
from pathlib import PurePosixPath

FORBIDDEN_COMPONENTS = {
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "bios",
    "build",
    "firmware",
    "obj_dir",
    "sim_build",
}
FORBIDDEN_SUFFIXES = {
    ".chd",
    ".fst",
    ".iso",
    ".lxt",
    ".pyc",
    ".vcd",
    ".wav",
}


def main() -> int:
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    tracked = [PurePosixPath(raw.decode()) for raw in completed.stdout.split(b"\0") if raw]
    forbidden = [
        path
        for path in tracked
        if FORBIDDEN_COMPONENTS.intersection(path.parts)
        or path.suffix.lower() in FORBIDDEN_SUFFIXES
    ]
    if forbidden:
        print("Forbidden generated or copyrighted paths are tracked:")
        for path in forbidden:
            print(f"  {path}")
        return 1

    print(f"tracked-file hygiene: {len(tracked)} paths checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
