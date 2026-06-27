"""Конфигурация пайплайна.

Все настраиваемые параметры собраны в одном неизменяемом dataclass, чтобы
этапы пайплайна не «зашивали» пути и константы внутри логики и решение
оставалось воспроизводимым.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# Корень проекта = на два уровня выше этого файла (src/genai_retention/config.py)
PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Config:
    """Единая точка конфигурации пайплайна."""

    # --- Пути ---
    data_path: Path = PROJECT_ROOT / "data" / "ai_student_impact_dataset.csv"
    artifacts_dir: Path = PROJECT_ROOT / "artifacts"
    figures_dir: Path = PROJECT_ROOT / "eda" / "figures"

    # --- Задача ML ---
    target: str = "Skill_Retention_Score"
    # Признаки, которые нельзя подавать в модель (идентификатор + утечка цели).
    drop_columns: tuple[str, ...] = ("Student_ID",)

    # --- Разбиение / воспроизводимость ---
    test_size: float = 0.2
    random_state: int = 42

    # --- Какие модели обучать (имена для фабрики моделей) ---
    models_to_train: tuple[str, ...] = ("linear", "random_forest")

    # --- Главная метрика для выбора лучшей модели (меньше = лучше) ---
    primary_metric: str = "rmse"

    # Явные списки признаков заполняются автоматически в препроцессинге,
    # но могут быть переопределены здесь при необходимости.
    numeric_features: tuple[str, ...] = field(default_factory=tuple)
    categorical_features: tuple[str, ...] = field(default_factory=tuple)

    @property
    def model_path(self) -> Path:
        return self.artifacts_dir / "model.joblib"

    @property
    def metrics_path(self) -> Path:
        return self.artifacts_dir / "metrics.json"
