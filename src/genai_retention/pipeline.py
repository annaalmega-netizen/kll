"""Воспроизводимый пайплайн (Задание 3).

Связывает все этапы в один воспроизводимый процесс:
    чтение -> обработка/признаки -> обучение нескольких моделей ->
    выбор лучшей -> сохранение результатов.

Запуск:  python -m genai_retention.pipeline
"""
from __future__ import annotations

import json
from dataclasses import dataclass

import joblib
import pandas as pd
from sklearn.model_selection import train_test_split

from .config import Config
from .data_loader import DataLoader
from .exceptions import PipelineError
from .logger import get_logger
from .models import ModelFactory
from .preprocessing import FeatureEngineer, build_preprocessor, split_feature_types
from .trainer import EvalResult, Trainer

logger = get_logger("pipeline")


@dataclass
class PipelineResult:
    best_name: str
    results: list[EvalResult]
    model_path: str

    def summary(self) -> dict:
        return {
            "best_model": self.best_name,
            "models": {r.name: r.as_metrics() for r in self.results},
        }


class TrainingPipeline:
    """Оркестратор всех этапов обучения."""

    def __init__(self, config: Config | None = None):
        self.config = config or Config()
        self.loader = DataLoader(self.config)
        self.engineer = FeatureEngineer()

    # --- отдельные этапы (каждый — самостоятельный, тестируемый шаг) ---

    def read_data(self) -> pd.DataFrame:
        return self.loader.load()

    def build_features(self, df: pd.DataFrame) -> pd.DataFrame:
        return self.engineer.transform(df)

    def split(self, df: pd.DataFrame):
        target = self.config.target
        feature_df = df.drop(columns=[target])
        y = df[target]
        return train_test_split(
            feature_df,
            y,
            test_size=self.config.test_size,
            random_state=self.config.random_state,
        )

    # --- полный прогон ---

    def run(self) -> PipelineResult:
        cfg = self.config
        cfg.artifacts_dir.mkdir(parents=True, exist_ok=True)

        try:
            df = self.read_data()
            df = self.build_features(df)

            X_train, X_test, y_train, y_test = self.split(df)

            numeric, categorical = split_feature_types(df, cfg)
            preprocessor = build_preprocessor(numeric, categorical)
            trainer = Trainer(preprocessor, random_state=cfg.random_state)

            results: list[EvalResult] = []
            for name in cfg.models_to_train:
                strategy = ModelFactory.create(name)
                pipe = trainer.train(strategy, X_train, y_train)
                results.append(trainer.evaluate(name, pipe, X_test, y_test))

            if not results:
                raise PipelineError("Не обучено ни одной модели")

            # Лучшая модель = минимум по основной метрике (rmse/mae) либо
            # максимум по r2.
            metric = cfg.primary_metric
            best = (
                max(results, key=lambda r: r.r2)
                if metric == "r2"
                else min(results, key=lambda r: getattr(r, metric))
            )
            logger.info("Лучшая модель: %s (%s=%.3f)", best.name, metric, getattr(best, metric))

            self._save(best, results)
            return PipelineResult(
                best_name=best.name,
                results=results,
                model_path=str(cfg.model_path),
            )
        except PipelineError:
            raise
        except Exception as exc:  # неожиданные ошибки оборачиваем единообразно
            logger.exception("Сбой пайплайна")
            raise PipelineError(str(exc)) from exc

    def _save(self, best: EvalResult, results: list[EvalResult]) -> None:
        cfg = self.config
        joblib.dump(best.pipeline, cfg.model_path)
        logger.info("Модель сохранена: %s", cfg.model_path)

        metrics = {
            "best_model": best.name,
            "primary_metric": cfg.primary_metric,
            "target": cfg.target,
            "models": {r.name: r.as_metrics() for r in results},
        }
        cfg.metrics_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False))
        logger.info("Метрики сохранены: %s", cfg.metrics_path)


def main() -> None:
    result = TrainingPipeline().run()
    print(json.dumps(result.summary(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
