"""Helpers for invoking R scripts from backend services."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess

from app.core.config import get_settings
from app.core.exceptions import BadRequest


R_SCRIPT_DIR = Path(__file__).with_name("r_scripts")


def get_r_script_path(name: str) -> Path:
    path = R_SCRIPT_DIR / name
    if not path.exists():
        raise BadRequest(f"未找到 R 脚本模板: {name}")
    return path


def load_r_script(name: str) -> str:
    return get_r_script_path(name).read_text(encoding="utf-8")


def run_rscript(args: list[str], error_message: str) -> subprocess.CompletedProcess[str]:
    settings = get_settings()
    command = [settings.RSCRIPT_COMMAND, *args]
    env = os.environ.copy()
    env["MEDICODE_R_AUTO_INSTALL_ENABLED"] = "true" if settings.R_AUTO_INSTALL_ENABLED else "false"
    env["MEDICODE_R_PACKAGE_REPO"] = settings.R_PACKAGE_REPO

    try:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )
    except FileNotFoundError as exc:
        raise BadRequest(
            f"{error_message}：未找到 Rscript。请检查 `.env` 中的 `RSCRIPT_COMMAND` 是否指向有效的 Rscript.exe。"
        ) from exc
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        stdout = (exc.stdout or "").strip()
        detail = stderr or stdout
        if detail:
            detail = detail.replace("\r", " ").replace("\n", " ")
            tail = detail[-400:] if len(detail) > 400 else detail
            raise BadRequest(f"{error_message}：{tail}") from exc
        raise BadRequest(error_message) from exc
