import os
from pathlib import Path

import pytest

from coros_mcp.auth import paths
from coros_mcp.auth.env import is_inside_git_repo, load_coros_env


@pytest.fixture
def config_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    config_dir = tmp_path / "coros-mcp"
    config_dir.mkdir()
    monkeypatch.setattr(paths, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(paths, "ENV_FILE", config_dir / ".env")
    monkeypatch.setattr(paths, "CREDENTIALS_FILE", config_dir / "auth.enc")
    yield config_dir


class TestLoadCorosEnv:
    def test_loads_only_config_env_not_project_env(
        self, tmp_path: Path, config_home: Path, monkeypatch: pytest.MonkeyPatch
    ):
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".env").write_text("COROS_PASSWORD=from_project\n")
        (config_home / ".env").write_text("COROS_EMAIL=from_config@example.com\n")

        monkeypatch.chdir(project_dir)
        monkeypatch.delenv("COROS_EMAIL", raising=False)
        load_coros_env(legacy_project_dir=project_dir)

        assert os.environ.get("COROS_EMAIL") == "from_config@example.com"
        assert os.environ.get("COROS_PASSWORD") is None

    def test_migrates_legacy_project_env(self, tmp_path: Path, config_home: Path, capsys):
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".env").write_text(
            "COROS_EMAIL=user@example.com\nCOROS_PASSWORD=secret\nCOROS_REGION=eu\n"
        )

        load_coros_env(legacy_project_dir=project_dir)

        migrated = (config_home / ".env").read_text()
        assert "COROS_EMAIL=user@example.com" in migrated
        assert "COROS_PASSWORD=secret" in migrated
        err = capsys.readouterr().err
        assert "migrated credentials" in err
        assert str(project_dir / ".env") in err

    def test_warns_on_secrets_in_git_repo(
        self, tmp_path: Path, config_home: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ):
        repo = tmp_path / "vault"
        repo.mkdir()
        (repo / ".git").mkdir()
        (repo / ".env").write_text("COROS_PASSWORD=leaked\n")

        monkeypatch.chdir(repo)
        load_coros_env(legacy_project_dir=None)

        err = capsys.readouterr().err
        assert "warning" in err
        assert "git" in err

    def test_does_not_overwrite_existing_process_env(
        self, config_home: Path, monkeypatch: pytest.MonkeyPatch
    ):
        (config_home / ".env").write_text("COROS_EMAIL=from_file@example.com\n")
        monkeypatch.setenv("COROS_EMAIL", "from_process@example.com")

        load_coros_env()

        assert os.environ.get("COROS_EMAIL") == "from_process@example.com"


class TestIsInsideGitRepo:
    def test_detects_git_in_parent(self, tmp_path: Path):
        repo = tmp_path / "vault"
        repo.mkdir()
        (repo / ".git").mkdir()
        nested = repo / "coros-mcp"
        nested.mkdir()
        assert is_inside_git_repo(nested) is True

    def test_false_outside_git(self, tmp_path: Path):
        assert is_inside_git_repo(tmp_path) is False
