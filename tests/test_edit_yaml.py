"""Unit tests for edit_yaml module."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

# Add project root to path for edit_yaml import
sys.path.insert(0, str(Path(__file__).parent.parent))

from edit_yaml import set_nested


# --- set_nested unit tests ---


def test_set_nested_simple_key():
    data = {"a": 1}
    set_nested(data, "a", 2)
    assert data == {"a": 2}


def test_set_nested_nested_existing():
    data = {"x": {"y": 1}}
    set_nested(data, "x.y", 2)
    assert data == {"x": {"y": 2}}


def test_set_nested_creates_intermediate():
    data = {}
    set_nested(data, "a.b.c", 1)
    assert data == {"a": {"b": {"c": 1}}}


def test_set_nested_empty_path_raises():
    with pytest.raises(ValueError, match="Invalid empty path"):
        set_nested({}, "", 1)


def test_set_nested_path_with_spaces():
    data = {}
    set_nested(data, " a.b ", 1)
    assert data == {"a": {"b": 1}}


def test_set_nested_preserves_types():
    data = {}
    set_nested(data, "n", 3)
    set_nested(data, "b", True)
    set_nested(data, "s", "hello")
    assert data == {"n": 3, "b": True, "s": "hello"}


# --- main integration tests (via subprocess) ---


def _run_edit_yaml(file_path: str, edits: list) -> subprocess.CompletedProcess:
    """Run edit_yaml.py without GITHUB_WORKSPACE so tmp_path (outside repo) is allowed."""
    edits_json = json.dumps(edits)
    root = Path(__file__).parent.parent
    script = root / "edit_yaml.py"
    env = {k: v for k, v in os.environ.items() if k != "GITHUB_WORKSPACE"}
    return subprocess.run(
        [sys.executable, str(script), file_path, edits_json],
        capture_output=True,
        text=True,
        cwd=str(root),
        env=env,
    )


def test_main_success(tmp_path):
    yaml_file = tmp_path / "values.yaml"
    yaml_file.write_text("image:\n  tag: latest\nreplicaCount: 1\n")

    result = _run_edit_yaml(str(yaml_file), [{"path": "image.tag", "value": "v1.0"}])

    assert result.returncode == 0
    data = yaml.safe_load(yaml_file.read_text())
    assert data["image"]["tag"] == "v1.0"


def test_main_file_not_found(tmp_path):
    result = _run_edit_yaml(str(tmp_path / "nonexistent.yaml"), [{"path": "a", "value": 1}])

    assert result.returncode == 1
    assert "Error: file not found" in result.stderr


def test_main_invalid_json(tmp_path):
    yaml_file = tmp_path / "values.yaml"
    yaml_file.write_text("a: 1\n")

    env = {k: v for k, v in os.environ.items() if k != "GITHUB_WORKSPACE"}
    result = subprocess.run(
        [sys.executable, str(Path(__file__).parent.parent / "edit_yaml.py"), str(yaml_file), "{"],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
        env=env,
    )

    assert result.returncode == 1
    assert "Error: invalid edits JSON" in result.stderr


def test_main_path_outside_workspace(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    yaml_file = tmp_path / "outside.yaml"
    yaml_file.write_text("a: 1\n")

    env = {**os.environ, "GITHUB_WORKSPACE": str(workspace)}
    result = subprocess.run(
        [sys.executable, str(Path(__file__).parent.parent / "edit_yaml.py"), "../outside.yaml", '[{"path":"a","value":2}]'],
        capture_output=True,
        text=True,
        cwd=str(workspace),
        env=env,
    )

    assert result.returncode == 1
    assert "Error: file path must be under GITHUB_WORKSPACE" in result.stderr


def test_main_multiple_edits(tmp_path):
    yaml_file = tmp_path / "values.yaml"
    yaml_file.write_text("image:\n  tag: latest\nreplicaCount: 1\n")

    edits = [
        {"path": "image.tag", "value": "test-v1.0"},
        {"path": "replicaCount", "value": 3},
    ]
    result = _run_edit_yaml(str(yaml_file), edits)

    assert result.returncode == 0
    data = yaml.safe_load(yaml_file.read_text())
    assert data["image"]["tag"] == "test-v1.0"
    assert data["replicaCount"] == 3
