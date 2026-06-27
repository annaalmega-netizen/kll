"""Задание 5: консольное приложение для использования модели.

Переиспользует сохранённую модель и код пайплайна (FeatureEngineer +
RetentionPredictor) из предыдущих заданий.

Примеры:
    # предсказание по CSV (как в обучающем датасете, без целевой колонки)
    python app/cli.py --input new_students.csv

    # предсказание по одному студенту через флаги
    python app/cli.py --weekly-genai-hours 25 --traditional-study-hours 5 \
        --tool-diversity 2 --major STEM --year Junior \
        --use-case Direct_Answer_Generation --skill Beginner \
        --policy Strict_Ban --paid false --pre-gpa 3.2 --dependency 8 --anxiety 6

    # интерактивный режим (вопрос-ответ)
    python app/cli.py --interactive
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from genai_retention.exceptions import ModelNotTrainedError, PipelineError  # noqa: E402
from genai_retention.logger import get_logger  # noqa: E402
from genai_retention.predictor import RetentionPredictor  # noqa: E402

logger = get_logger("cli")

# Поля, которые ожидает модель (производные признаки строит FeatureEngineer).
RAW_FIELDS = {
    "Major_Category": "STEM",
    "Year_of_Study": "Junior",
    "Pre_Semester_GPA": 3.2,
    "Weekly_GenAI_Hours": 8.0,
    "Primary_Use_Case": "Ideation",
    "Prompt_Engineering_Skill": "Intermediate",
    "Tool_Diversity": 3,
    "Paid_Subscription": False,
    "Traditional_Study_Hours": 12.0,
    "Perceived_AI_Dependency": 4,
    "Institutional_Policy": "Allowed_With_Citation",
    "Anxiety_Level_During_Exams": 4,
    "Post_Semester_GPA": 3.3,
    "Burnout_Risk_Level": "Medium",
}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Предсказание Skill_Retention_Score")
    p.add_argument("--input", type=str, help="CSV-файл с новыми студентами")
    p.add_argument("--model", type=str, help="путь к сохранённой модели (.joblib)")
    p.add_argument("--interactive", action="store_true", help="интерактивный ввод")

    # одиночный ввод через флаги
    p.add_argument("--major", dest="Major_Category")
    p.add_argument("--year", dest="Year_of_Study")
    p.add_argument("--pre-gpa", dest="Pre_Semester_GPA", type=float)
    p.add_argument("--weekly-genai-hours", dest="Weekly_GenAI_Hours", type=float)
    p.add_argument("--use-case", dest="Primary_Use_Case")
    p.add_argument("--skill", dest="Prompt_Engineering_Skill")
    p.add_argument("--tool-diversity", dest="Tool_Diversity", type=int)
    p.add_argument("--paid", dest="Paid_Subscription")
    p.add_argument("--traditional-study-hours", dest="Traditional_Study_Hours", type=float)
    p.add_argument("--dependency", dest="Perceived_AI_Dependency", type=int)
    p.add_argument("--policy", dest="Institutional_Policy")
    p.add_argument("--anxiety", dest="Anxiety_Level_During_Exams", type=int)
    p.add_argument("--post-gpa", dest="Post_Semester_GPA", type=float)
    p.add_argument("--burnout", dest="Burnout_Risk_Level")
    return p


def _coerce_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "да"}


def record_from_args(args: argparse.Namespace) -> dict:
    """Собрать запись из флагов, недостающие поля — из значений по умолчанию."""
    rec = dict(RAW_FIELDS)
    for field in RAW_FIELDS:
        val = getattr(args, field, None)
        if val is not None:
            rec[field] = val
    rec["Paid_Subscription"] = _coerce_bool(rec["Paid_Subscription"])
    return rec


def record_interactive() -> dict:
    rec = dict(RAW_FIELDS)
    print("Введите значения (Enter = значение по умолчанию в скобках):")
    for field, default in RAW_FIELDS.items():
        raw = input(f"  {field} [{default}]: ").strip()
        if not raw:
            continue
        if isinstance(default, bool):
            rec[field] = _coerce_bool(raw)
        elif isinstance(default, int):
            rec[field] = int(raw)
        elif isinstance(default, float):
            rec[field] = float(raw)
        else:
            rec[field] = raw
    return rec


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    model_path = Path(args.model) if args.model else None

    try:
        predictor = RetentionPredictor().load(model_path)

        if args.input:
            df = pd.read_csv(args.input)
            preds = predictor.predict(df)
            df_out = df.copy()
            df_out["Predicted_Skill_Retention_Score"] = [round(p, 2) for p in preds]
            print(df_out.to_string(index=False))
            print(f"\nОбработано записей: {len(preds)}; "
                  f"среднее предсказание: {sum(preds) / len(preds):.2f}")
            return 0

        record = record_interactive() if args.interactive else record_from_args(args)
        pred = predictor.predict(record)[0]
        print(json.dumps(
            {"input": record, "predicted_skill_retention_score": round(pred, 2)},
            ensure_ascii=False,
            indent=2,
        ))
        return 0

    except ModelNotTrainedError as exc:
        print(f"[Ошибка] {exc}", file=sys.stderr)
        return 2
    except (PipelineError, FileNotFoundError, ValueError) as exc:
        print(f"[Ошибка] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(run())
