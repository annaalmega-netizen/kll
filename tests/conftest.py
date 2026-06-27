"""Общие фикстуры для тестов и настройка путей импорта."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Небольшой синтетический датасет той же схемы, что и реальный."""
    rng = np.random.default_rng(0)
    n = 200
    return pd.DataFrame(
        {
            "Student_ID": np.arange(100001, 100001 + n),
            "Major_Category": rng.choice(["STEM", "Business", "Arts"], n),
            "Year_of_Study": rng.choice(["Freshman", "Junior", "Graduate"], n),
            "Pre_Semester_GPA": rng.uniform(1.2, 4.0, n).round(2),
            "Weekly_GenAI_Hours": rng.uniform(0, 40, n).round(2),
            "Primary_Use_Case": rng.choice(
                ["Ideation", "Direct_Answer_Generation", "Debugging/Troubleshooting"], n
            ),
            "Prompt_Engineering_Skill": rng.choice(["Beginner", "Advanced"], n),
            "Tool_Diversity": rng.integers(1, 6, n),
            "Paid_Subscription": rng.choice([True, False], n),
            "Traditional_Study_Hours": rng.uniform(1, 36, n).round(2),
            "Perceived_AI_Dependency": rng.integers(1, 11, n),
            "Institutional_Policy": rng.choice(
                ["Allowed_With_Citation", "Strict_Ban"], n
            ),
            "Anxiety_Level_During_Exams": rng.integers(1, 11, n),
            "Post_Semester_GPA": rng.uniform(1.0, 4.0, n).round(2),
            "Skill_Retention_Score": rng.uniform(10, 100, n).round(2),
            "Burnout_Risk_Level": rng.choice(["Low", "Medium", "High"], n),
        }
    )
