#!/usr/bin/env python3
"""Verify the stable repository subsystem boundaries."""

from pathlib import Path

REQUIRED_DIRECTORIES = (
    ".github/workflows",
    "docs",
    "reference/common",
    "reference/ee",
    "reference/gs",
    "reference/vu",
    "rtl/common",
    "rtl/dmac",
    "rtl/ee/cop0",
    "rtl/ee/fpu",
    "rtl/ee/mmi",
    "rtl/ee/r5900",
    "rtl/gif",
    "rtl/gs",
    "rtl/intc",
    "rtl/iop",
    "rtl/ipu",
    "rtl/memory",
    "rtl/sif",
    "rtl/spu2",
    "rtl/timers",
    "rtl/vif",
    "rtl/vu",
    "scripts",
    "sim/debug",
    "sim/loaders",
    "sim/models",
    "software/baremetal",
    "software/demos",
    "software/ee_tests",
    "software/gs_tests",
    "software/vu_tests",
    "tests/differential",
    "tests/integration",
    "tests/randomized",
    "tests/regression",
    "tests/system",
    "tests/unit",
)


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    missing = [path for path in REQUIRED_DIRECTORIES if not (root / path).is_dir()]
    if missing:
        print("Missing required project directories:")
        for path in missing:
            print(f"  {path}")
        return 1

    print(f"project structure: {len(REQUIRED_DIRECTORIES)} required directories present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
