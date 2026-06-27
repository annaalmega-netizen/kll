"""Этап 2-3: очистка данных и построение признаков.

`FeatureEngineer` создаёт несколько осмысленных производных признаков,
связанных с исследовательским вопросом (интенсивность и «пассивность»
использования ИИ), а `build_preprocessor` собирает sklearn-ColumnTransformer
для масштабирования числовых и кодирования категориальных признаков.
"""
from __future__ import annotations

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import Config
from .logger import get_logger

logger = get_logger("preprocessing")

# Сценарии использования ИИ, считающиеся «пассивными» (потребление готового
# результата) — гипотеза EDA: они сильнее вредят сохранности знаний.
PASSIVE_USE_CASES = {"Direct_Answer_Generation", "Summarizing_Reading"}


class FeatureEngineer:
    """Строит производные признаки. Не имеет состояния обучения -> применим
    одинаково к train и к новым данным (важно для приложения-предсказателя)."""

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # Доля времени на ИИ от всего учебного времени: насколько студент
        # «полагается» на ИИ вместо традиционной учёбы.
        total_study = df["Weekly_GenAI_Hours"] + df["Traditional_Study_Hours"]
        df["AI_Study_Ratio"] = df["Weekly_GenAI_Hours"] / total_study.replace(0, 1)

        # Интенсивность на инструмент: много часов при малом числе инструментов
        # = глубокая зависимость от ограниченного набора ИИ.
        if "Tool_Diversity" in df.columns:
            df["Hours_Per_Tool"] = df["Weekly_GenAI_Hours"] / df["Tool_Diversity"].clip(lower=1)

        # Флаг «пассивного» сценария использования.
        if "Primary_Use_Case" in df.columns:
            df["Is_Passive_Use"] = (
                df["Primary_Use_Case"].isin(PASSIVE_USE_CASES).astype(int)
            )

        return df


def split_feature_types(df: pd.DataFrame, config: Config) -> tuple[list[str], list[str]]:
    """Разделить колонки на числовые и категориальные, исключив цель и
    служебные колонки."""
    exclude = set(config.drop_columns) | {config.target}
    feature_cols = [c for c in df.columns if c not in exclude]

    numeric = [c for c in feature_cols if pd.api.types.is_numeric_dtype(df[c])]
    # bool трактуем как категорию для наглядного one-hot.
    categorical = [c for c in feature_cols if c not in numeric]
    logger.info("Числовых признаков: %d, категориальных: %d", len(numeric), len(categorical))
    return numeric, categorical


def build_preprocessor(numeric: list[str], categorical: list[str]) -> ColumnTransformer:
    """ColumnTransformer: StandardScaler для чисел, OneHot для категорий."""
    numeric_pipe = Pipeline([("scaler", StandardScaler())])
    categorical_pipe = Pipeline(
        [("onehot", OneHotEncoder(handle_unknown="ignore"))]
    )
    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipe, numeric),
            ("cat", categorical_pipe, categorical),
        ]
    )
