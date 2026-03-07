"""Helpers for invoking R scripts from backend services."""

from __future__ import annotations

import subprocess

from app.core.config import get_settings
from app.core.exceptions import BadRequest


def run_rscript(args: list[str], error_message: str) -> subprocess.CompletedProcess[str]:
    command = [get_settings().RSCRIPT_COMMAND, *args]

    try:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
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
            raise BadRequest(f"{error_message}：{detail[:400]}") from exc
        raise BadRequest(error_message) from exc
