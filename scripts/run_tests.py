#!/usr/bin/env python3
"""Run a named pytest layer and enforce result-integrity rules."""

import argparse
import os
from pathlib import Path
import subprocess
import sys
from xml.etree import ElementTree


SUITE_MARKERS = {
    "test": None,
    "unit": "unit",
    "differential": "differential",
    "randomized": "randomized",
    "integration": "integration",
    "regression": None,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("suite", choices=SUITE_MARKERS)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--build-root", type=Path, default=Path("build"))
    return parser.parse_args()


def audit_results(report: Path) -> tuple[int, int, int, int]:
    """Return test, failure, error, and skip counts from a JUnit report."""
    root = ElementTree.parse(report).getroot()
    tests = len(root.findall(".//testcase"))
    failures = len(root.findall(".//failure"))
    errors = len(root.findall(".//error"))
    skipped = len(root.findall(".//skipped"))
    return tests, failures, errors, skipped


def main() -> int:
    args = parse_args()
    build_root = args.build_root.resolve()
    results_dir = build_root / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    report = results_dir / f"pytest-{args.suite}.xml"

    command = [
        sys.executable,
        "-m",
        "pytest",
        f"--junitxml={report}",
    ]
    marker = SUITE_MARKERS[args.suite]
    if marker is not None:
        command.extend(("-m", marker))

    environment = os.environ.copy()
    environment["RANDOM_SEED"] = str(args.seed)
    environment["PS2_BUILD_ROOT"] = str(build_root)
    completed = subprocess.run(command, env=environment, check=False)
    if completed.returncode != 0:
        return completed.returncode

    tests, failures, errors, skipped = audit_results(report)
    print(
        f"{args.suite} result audit: "
        f"tests={tests} failures={failures} errors={errors} skipped={skipped}"
    )
    if tests == 0:
        print(f"{args.suite}: no tests were collected", file=sys.stderr)
        return 5
    if failures or errors or skipped:
        print(f"{args.suite}: result-integrity gate failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
