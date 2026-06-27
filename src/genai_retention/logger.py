"""Настройка логирования.

Единая фабрика логгеров: одинаковый формат во всех модулях, без дублей
обработчиков при повторных вызовах.
"""
from __future__ import annotations

import logging
import sys

_LOG_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
_configured = False


def get_logger(name: str = "genai_retention", level: int = logging.INFO) -> logging.Logger:
    """Вернуть настроенный логгер.

    Конфигурируем корневой обработчик один раз (idempotent), чтобы при
    многократном импорте модулей не появлялись повторяющиеся строки логов.
    """
    global _configured
    if not _configured:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(_LOG_FORMAT))
        root = logging.getLogger("genai_retention")
        root.setLevel(level)
        root.addHandler(handler)
        root.propagate = False
        _configured = True

    logger = logging.getLogger(f"genai_retention.{name}" if name != "genai_retention" else name)
    logger.setLevel(level)
    return logger
