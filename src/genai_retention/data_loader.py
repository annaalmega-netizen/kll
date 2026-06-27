"""Этап 1: чтение и валидация данных."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import Config
from .exceptions import DataLoadError, DataValidationError
from .logger import get_logger

logger = get_logger("data_loader")

# Минимальный набор колонок, без которых пайплайн не имеет смысла.
REQUIRED_COLUMNS = {
    "Student_ID",
    "Weekly_GenAI_Hours",
    "Perceived_AI_Dependency",
    "Traditional_Study_Hours",
    "Skill_Retention_Score",
}


class DataLoader:
    """Читает CSV и выполняет базовую валидацию схемы/качества."""

    def __init__(self, config: Config):
        self.config = config

    def load(self, path: Path | None = None) -> pd.DataFrame:
        path = Path(path) if path is not None else self.config.data_path
        logger.info("Чтение данных из %s", path)

        if not path.exists():
            raise DataLoadError(f"Файл данных не найден: {path}")

        try:
            df = pd.read_csv(path)
        except Exception as exc:  # pragma: no cover - редкий путь чтения
            raise DataLoadError(f"Не удалось прочитать CSV {path}: {exc}") from exc

        self._validate(df)
        logger.info("Загружено строк: %d, столбцов: %d", df.shape[0], df.shape[1])
        return df

    def _validate(self, df: pd.DataFrame) -> None:
        """Проверка обязательных колонок и непустоты."""
        if df.empty:
            raise DataValidationError("Датасет пуст")

        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise DataValidationError(f"Отсутствуют обязательные колонки: {sorted(missing)}")

        if self.config.target not in df.columns:
            raise DataValidationError(f"Нет целевой колонки {self.config.target!r}")
