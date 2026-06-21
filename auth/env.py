"""Load Coros credentials from ~/.config/coros-mcp/.env only (never from project/vault cwd)."""

import contextlib
import os
import stat
import sys
from pathlib import Path

from dotenv import dotenv_values, load_dotenv

from auth import paths

_COROS_ENV_KEYS = ("COROS_EMAIL", "COROS_PASSWORD", "COROS_REGION", "COROS_ACCESS_TOKEN", "COROS_TIMEZONE")

_LOADED = False


def is_inside_git_repo(path: Path) -> bool:
    for candidate in [path, *path.parents]:
        if (candidate / ".git").exists():
            return True
    return False


def _env_has_coros_secrets(env_path: Path) -> bool:
    if not env_path.is_file():
        return False
    values = dotenv_values(env_path)
    return bool(values.get("COROS_PASSWORD") or values.get("COROS_ACCESS_TOKEN"))


def _extract_coros_lines(env_path: Path) -> list[str]:
    lines: list[str] = []
    for raw in env_path.read_text().splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        key = stripped.split("=", 1)[0].strip()
        if key in _COROS_ENV_KEYS:
            lines.append(raw)
    return lines


def _write_config_env(lines: list[str]) -> None:
    paths.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with contextlib.suppress(OSError):
        os.chmod(paths.CONFIG_DIR, stat.S_IRWXU)
    paths.ENV_FILE.write_text("\n".join(lines) + "\n")
    with contextlib.suppress(OSError):
        os.chmod(paths.ENV_FILE, stat.S_IRUSR | stat.S_IWUSR)


def _maybe_migrate_legacy_env(legacy_project_dir: Path | None) -> None:
    if paths.ENV_FILE.exists():
        return
    if legacy_project_dir is None:
        return
    legacy_env = legacy_project_dir / ".env"
    lines = _extract_coros_lines(legacy_env)
    if not lines:
        return
    _write_config_env(lines)
    print(
        f"coros-mcp: migrated credentials from {legacy_env} to {paths.ENV_FILE}. "
        f"Remove {legacy_env} to avoid accidental git commits.",
        file=sys.stderr,
    )


def _warn_unsafe_env_locations(*env_paths: Path) -> None:
    for env_path in env_paths:
        if not _env_has_coros_secrets(env_path):
            continue
        if is_inside_git_repo(env_path.parent):
            print(
                f"coros-mcp: warning: {env_path} contains Coros secrets inside a git "
                f"repository. Move credentials to {paths.ENV_FILE} or run 'coros-mcp auth', "
                f"then delete {env_path}.",
                file=sys.stderr,
            )


def load_coros_env(*, legacy_project_dir: Path | None = None) -> None:
    global _LOADED
    _maybe_migrate_legacy_env(legacy_project_dir)

    paths.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if paths.ENV_FILE.is_file():
        load_dotenv(paths.ENV_FILE)

    warn_paths: list[Path] = []
    if legacy_project_dir is not None:
        warn_paths.append(legacy_project_dir / ".env")
    warn_paths.append(Path.cwd() / ".env")
    _warn_unsafe_env_locations(*warn_paths)

    _LOADED = True
