#!/usr/bin/env python3
"""
Edit one or more fields in a YAML file in-place.
Reads file path and JSON edits from command-line args (passed by GitHub Actions).
"""
import json
import os
import sys
from pathlib import Path

import yaml


def set_nested(data: dict, path: str, value) -> None:
    """Set a nested key from dot-separated path, creating intermediate dicts if needed."""
    keys = path.strip().split(".")
    if not keys or not keys[0]:
        raise ValueError(f"Invalid empty path: {path!r}")
    current = data
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    current[keys[-1]] = value


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: edit_yaml.py <file> <edits_json>", file=sys.stderr)
        return 1

    file_path = sys.argv[1]
    edits_json = sys.argv[2]

    workspace = os.environ.get("GITHUB_WORKSPACE")
    if workspace:
        base = Path(workspace).resolve()
        path_to_use = (base / file_path).resolve()
        try:
            path_to_use.relative_to(base)
        except ValueError:
            print(f"Error: file path must be under GITHUB_WORKSPACE: {file_path}", file=sys.stderr)
            return 1
    else:
        path_to_use = Path(file_path).resolve()

    if not path_to_use.exists():
        print(f"Error: file not found: {path_to_use}", file=sys.stderr)
        return 1

    try:
        edits = json.loads(edits_json)
    except json.JSONDecodeError as e:
        print(f"Error: invalid edits JSON: {e}", file=sys.stderr)
        return 1

    if not isinstance(edits, list):
        print("Error: edits must be a JSON array", file=sys.stderr)
        return 1

    try:
        with open(path_to_use, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except (OSError, yaml.YAMLError) as e:
        print(f"Error reading YAML: {e}", file=sys.stderr)
        return 1

    if data is None:
        data = {}

    if not isinstance(data, dict):
        print("Error: YAML root must be a mapping (dict)", file=sys.stderr)
        return 1

    for i, item in enumerate(edits):
        if not isinstance(item, dict):
            print(f"Error: edit[{i}] must be an object with 'path' and 'value'", file=sys.stderr)
            return 1
        path_key = item.get("path")
        value = item.get("value")
        if path_key is None or path_key == "":
            print(f"Error: edit[{i}] has missing or empty 'path'", file=sys.stderr)
            return 1
        try:
            set_nested(data, path_key, value)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    try:
        with open(path_to_use, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    except OSError as e:
        print(f"Error writing YAML: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
