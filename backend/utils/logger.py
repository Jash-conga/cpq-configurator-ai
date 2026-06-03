"""
backend/utils/logger.py

Structured logging setup for the Conga CPQ AI Agent.
All agent decisions, tool calls, JSON mutations, and Salesforce operations are logged here.
"""

import logging
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any


LOG_DIR = Path(os.getenv("LOG_DIR", "backend/logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG").upper()

_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
}


def _build_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already configured

    logger.setLevel(_LEVEL_MAP.get(LOG_LEVEL, logging.DEBUG))

    # ── Console handler (rich-coloured) ──────────────────────────────────────
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%H:%M:%S",
        )
    )

    # ── File handler (JSON lines) ─────────────────────────────────────────────
    log_file = LOG_DIR / f"agent_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter("%(message)s"))

    logger.addHandler(console)
    logger.addHandler(file_handler)
    return logger


class StructuredLogger:
    """
    Thin wrapper that writes JSON-lines to the file handler and a
    human-readable line to the console handler.
    """

    def __init__(self, name: str):
        self._logger = _build_logger(name)
        self._name = name

    def _emit(self, level: str, event: str, **kwargs: Any):
        payload = {
            "ts": datetime.utcnow().isoformat(),
            "logger": self._name,
            "level": level,
            "event": event,
            **kwargs,
        }
        log_fn = getattr(self._logger, level.lower(), self._logger.info)
        log_fn(json.dumps(payload))

    # ── Public helpers ────────────────────────────────────────────────────────

    def debug(self, event: str, **kw):
        self._emit("DEBUG", event, **kw)

    def info(self, event: str, **kw):
        self._emit("INFO", event, **kw)

    def warning(self, event: str, **kw):
        self._emit("WARNING", event, **kw)

    def error(self, event: str, **kw):
        self._emit("ERROR", event, **kw)

    def agent_decision(self, decision: str, **kw):
        self._emit("INFO", "agent_decision", decision=decision, **kw)

    def tool_call(self, tool: str, inputs: dict, result: Any):
        self._emit("DEBUG", "tool_call", tool=tool, inputs=inputs, result=str(result)[:500])

    def json_mutation(self, operation: str, object_name: str, uuid: str, snapshot: dict):
        self._emit(
            "INFO",
            "running_json_mutation",
            operation=operation,
            object_name=object_name,
            record_uuid=uuid,
            snapshot_size=len(json.dumps(snapshot)),
        )

    def salesforce_op(self, operation: str, object_name: str, payload: dict, result: Any):
        self._emit(
            "INFO",
            "salesforce_operation",
            operation=operation,
            object_name=object_name,
            payload_keys=list(payload.keys()),
            result=str(result)[:500],
        )


# ── Module-level convenience getters ─────────────────────────────────────────

def get_logger(name: str) -> StructuredLogger:
    return StructuredLogger(name)
