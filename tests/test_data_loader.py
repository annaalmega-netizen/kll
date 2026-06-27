"""Тесты этапа чтения и валидации данных."""
import pandas as pd
import pytest

from genai_retention.config import Config
from genai_retention.data_loader import DataLoader
from genai_retention.exceptions import DataLoadError, DataValidationError


def test_load_reads_valid_csv(tmp_path, sample_df):
    path = tmp_path / "data.csv"
    sample_df.to_csv(path, index=False)
    loader = DataLoader(Config())

    df = loader.load(path)

    assert len(df) == len(sample_df)
    assert "Skill_Retention_Score" in df.columns


def test_load_missing_file_raises():
    loader = DataLoader(Config())
    with pytest.raises(DataLoadError):
        loader.load("/nonexistent/path/data.csv")


def test_validate_missing_required_column(tmp_path, sample_df):
    bad = sample_df.drop(columns=["Weekly_GenAI_Hours"])
    path = tmp_path / "bad.csv"
    bad.to_csv(path, index=False)
    loader = DataLoader(Config())

    with pytest.raises(DataValidationError):
        loader.load(path)


def test_validate_empty_dataframe(tmp_path):
    path = tmp_path / "empty.csv"
    pd.DataFrame(columns=["Skill_Retention_Score"]).to_csv(path, index=False)
    loader = DataLoader(Config())

    with pytest.raises(DataValidationError):
        loader.load(path)
