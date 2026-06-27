"""Тесты ключевых этапов: признаки, фабрика моделей, сквозной прогон."""
import pytest

from genai_retention.config import Config
from genai_retention.exceptions import ModelNotTrainedError, UnknownModelError
from genai_retention.models import ModelFactory, ModelStrategy
from genai_retention.predictor import RetentionPredictor
from genai_retention.preprocessing import FeatureEngineer
from genai_retention.pipeline import TrainingPipeline


def test_feature_engineer_adds_derived_columns(sample_df):
    out = FeatureEngineer().transform(sample_df)
    for col in ["AI_Study_Ratio", "Hours_Per_Tool", "Is_Passive_Use"]:
        assert col in out.columns
    # доля времени на ИИ всегда в [0, 1]
    assert out["AI_Study_Ratio"].between(0, 1).all()


def test_model_factory_creates_known_strategies():
    strat = ModelFactory.create("random_forest")
    assert isinstance(strat, ModelStrategy)
    assert strat.name == "random_forest"


def test_model_factory_unknown_raises():
    with pytest.raises(UnknownModelError):
        ModelFactory.create("does_not_exist")


def test_pipeline_end_to_end(tmp_path, sample_df):
    """Полный прогон на маленьких данных: обучение -> сохранение -> предсказание."""
    data_path = tmp_path / "data.csv"
    sample_df.to_csv(data_path, index=False)

    cfg = Config(
        data_path=data_path,
        artifacts_dir=tmp_path / "artifacts",
        models_to_train=("linear", "decision_tree"),
    )

    result = TrainingPipeline(cfg).run()

    assert result.best_name in {"linear", "decision_tree"}
    assert cfg.model_path.exists()
    assert cfg.metrics_path.exists()

    # сохранённая модель пригодна для инференса на новой записи
    predictor = RetentionPredictor(cfg).load()
    record = sample_df.drop(columns=["Skill_Retention_Score"]).iloc[0].to_dict()
    preds = predictor.predict(record)
    assert len(preds) == 1
    assert isinstance(preds[0], float)


def test_predictor_requires_loaded_model():
    with pytest.raises(ModelNotTrainedError):
        RetentionPredictor().predict({"Weekly_GenAI_Hours": 10})
