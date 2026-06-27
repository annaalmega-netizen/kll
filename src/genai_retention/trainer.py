"""Этап 4: обучение и оценка моделей.

`Trainer` собирает полный sklearn-Pipeline (препроцессор + модель), обучает
его и считает метрики. Он работает с `ModelStrategy` (паттерн Strategy),
поэтому не зависит от конкретного алгоритма.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline

from .logger import get_logger
from .models import ModelStrategy

logger = get_logger("trainer")


@dataclass
class EvalResult:
    """Результат оценки одной модели."""

    name: str
    rmse: float
    mae: float
    r2: float
    pipeline: Pipeline

    def as_metrics(self) -> dict[str, float]:
        return {"rmse": self.rmse, "mae": self.mae, "r2": self.r2}


class Trainer:
    """Обучает связку препроцессор+модель и оценивает её на тесте."""

    def __init__(self, preprocessor: ColumnTransformer, random_state: int = 42):
        self.preprocessor = preprocessor
        self.random_state = random_state

    def train(
        self,
        strategy: ModelStrategy,
        X_train: pd.DataFrame,
        y_train: pd.Series,
    ) -> Pipeline:
        """Собрать и обучить полный pipeline для заданной стратегии."""
        logger.info("Обучение модели '%s' на %d объектах", strategy.name, len(X_train))
        estimator = strategy.build(self.random_state)
        pipe = Pipeline(
            steps=[
                ("preprocessor", self.preprocessor),
                ("model", estimator),
            ]
        )
        pipe.fit(X_train, y_train)
        return pipe

    def evaluate(
        self,
        name: str,
        pipe: Pipeline,
        X_test: pd.DataFrame,
        y_test: pd.Series,
    ) -> EvalResult:
        """Посчитать RMSE/MAE/R2 на тестовой выборке."""
        preds = pipe.predict(X_test)
        rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
        mae = float(mean_absolute_error(y_test, preds))
        r2 = float(r2_score(y_test, preds))
        logger.info("Метрики '%s': RMSE=%.3f MAE=%.3f R2=%.3f", name, rmse, mae, r2)
        return EvalResult(name=name, rmse=rmse, mae=mae, r2=r2, pipeline=pipe)
