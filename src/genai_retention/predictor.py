"""Загрузка сохранённой модели и предсказание на новых данных.

Этот модуль — мост между обученным пайплайном (Задание 3) и приложением
(Задание 5): он переиспользует тот же `FeatureEngineer`, что и при обучении,
поэтому новые данные обрабатываются идентично.
"""
from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd

from .config import Config
from .exceptions import ModelNotTrainedError
from .logger import get_logger
from .preprocessing import FeatureEngineer

logger = get_logger("predictor")


class RetentionPredictor:
    """Обёртка над сохранённым sklearn-пайплайном для инференса."""

    def __init__(self, config: Config | None = None):
        self.config = config or Config()
        self.engineer = FeatureEngineer()
        self._pipeline = None

    def load(self, path: Path | None = None) -> "RetentionPredictor":
        path = Path(path) if path is not None else self.config.model_path
        if not path.exists():
            raise ModelNotTrainedError(
                f"Модель не найдена: {path}. Сначала запустите обучение "
                f"(python -m genai_retention.pipeline)."
            )
        self._pipeline = joblib.load(path)
        logger.info("Модель загружена из %s", path)
        return self

    def predict(self, data: pd.DataFrame | dict) -> list[float]:
        """Предсказать Skill_Retention_Score для одной записи (dict) или
        нескольких (DataFrame)."""
        if self._pipeline is None:
            raise ModelNotTrainedError("Модель не загружена. Вызовите load().")

        df = pd.DataFrame([data]) if isinstance(data, dict) else data.copy()
        df = self.engineer.transform(df)
        preds = self._pipeline.predict(df)
        return [float(p) for p in preds]
