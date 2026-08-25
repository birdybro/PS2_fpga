#!/usr/bin/env python3
"""Validate the required GitHub Actions verification contract."""

from pathlib import Path

import yaml

WORKFLOW_PATH = Path(__file__).resolve().parent.parent / ".github/workflows/ci.yml"
REQUIRED_TRIGGERS = {"push", "pull_request", "workflow_dispatch"}
REQUIRED_COMMANDS = (
    "make lint",
    "make build",
    "make unit",
    "make differential",
    "make randomized",
    "make integration",
    "make regression",
)
VERILATOR_IMAGE = "verilator/verilator:v5.050"
SAFE_DIRECTORY_COMMAND = 'git config --global --add safe.directory "$GITHUB_WORKSPACE"'


def main() -> int:
    workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    triggers = set(workflow.get("on", {}))
    if triggers != REQUIRED_TRIGGERS:
        msg = f"CI triggers {sorted(triggers)} do not match {sorted(REQUIRED_TRIGGERS)}"
        raise ValueError(msg)

    if workflow.get("permissions") != {"contents": "read"}:
        msg = "CI must use read-only repository permissions"
        raise ValueError(msg)

    verification = workflow["jobs"]["verification"]
    if verification["container"]["image"] != VERILATOR_IMAGE:
        msg = f"CI must pin the Verilator container to {VERILATOR_IMAGE}"
        raise ValueError(msg)

    steps = verification["steps"]
    run_commands = {step.get("run", "").strip() for step in steps}
    missing = [command for command in REQUIRED_COMMANDS if command not in run_commands]
    if missing:
        msg = f"CI is missing required commands: {', '.join(missing)}"
        raise ValueError(msg)
    if SAFE_DIRECTORY_COMMAND not in run_commands:
        raise ValueError("container CI must trust only the mounted GitHub workspace")

    action_uses = {step.get("uses", "") for step in steps}
    if not any(action.startswith("actions/checkout@") for action in action_uses):
        raise ValueError("CI is missing actions/checkout")
    if not any(action.startswith("actions/setup-python@") for action in action_uses):
        raise ValueError("CI is missing actions/setup-python")

    print(
        f"CI workflow: {len(REQUIRED_COMMANDS)} required commands, "
        f"{len(REQUIRED_TRIGGERS)} triggers, pinned Verilator"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
