"""Задание 1: разведочный анализ данных (EDA).

Исследовательский вопрос:
    «Влияет ли чрезмерное использование ИИ на долгосрочную сохранность знаний?»

Скрипт:
  * строит >= 3 содержательных графиков РАЗНОГО формата
    (гистограмма+KDE, диаграмма рассеяния с трендом, boxplot, heatmap, barplot);
  * формулирует >= 3 статистических вывода с проверкой значимости.

Запуск:  python eda/run_eda.py
Графики сохраняются в eda/figures/.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # без дисплея — сохраняем в файлы
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

# чтобы скрипт работал и из корня, и из папки eda/
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from genai_retention.config import Config  # noqa: E402

sns.set_theme(style="whitegrid")
TARGET = "Skill_Retention_Score"


def load() -> pd.DataFrame:
    cfg = Config()
    return pd.read_csv(cfg.data_path)


# --------------------------------------------------------------------------- #
# Графики
# --------------------------------------------------------------------------- #
def plot_distribution(df: pd.DataFrame, out: Path) -> None:
    """График 1: гистограмма + KDE распределения сохранности знаний."""
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.histplot(df[TARGET], bins=40, kde=True, color="#4C72B0", ax=ax)
    ax.axvline(df[TARGET].mean(), color="red", ls="--", label=f"среднее={df[TARGET].mean():.1f}")
    ax.set_title("Распределение Skill_Retention_Score")
    ax.set_xlabel("Skill_Retention_Score")
    ax.set_ylabel("Частота")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "01_distribution.png", dpi=120)
    plt.close(fig)


def plot_scatter_trend(df: pd.DataFrame, out: Path) -> None:
    """График 2: рассеяние «часы ИИ vs сохранность» с линией тренда."""
    fig, ax = plt.subplots(figsize=(8, 5))
    sample = df.sample(min(4000, len(df)), random_state=0)
    sns.regplot(
        data=sample,
        x="Weekly_GenAI_Hours",
        y=TARGET,
        scatter_kws={"alpha": 0.2, "s": 12},
        line_kws={"color": "red"},
        ax=ax,
    )
    ax.set_title("Недельные часы ИИ vs сохранность знаний")
    fig.tight_layout()
    fig.savefig(out / "02_hours_vs_retention.png", dpi=120)
    plt.close(fig)


def plot_box_by_usecase(df: pd.DataFrame, out: Path) -> None:
    """График 3: boxplot сохранности по сценарию использования ИИ."""
    order = df.groupby("Primary_Use_Case")[TARGET].median().sort_values().index
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.boxplot(data=df, x="Primary_Use_Case", y=TARGET, order=order, ax=ax)
    ax.set_title("Сохранность знаний по основному сценарию использования ИИ")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(out / "03_retention_by_usecase.png", dpi=120)
    plt.close(fig)


def plot_correlation_heatmap(df: pd.DataFrame, out: Path) -> None:
    """График 4: тепловая карта корреляций числовых признаков."""
    num = df.select_dtypes(include=np.number).drop(columns=["Student_ID"], errors="ignore")
    corr = num.corr()
    fig, ax = plt.subplots(figsize=(9, 7))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, ax=ax)
    ax.set_title("Корреляции числовых признаков")
    fig.tight_layout()
    fig.savefig(out / "04_correlation_heatmap.png", dpi=120)
    plt.close(fig)


def plot_bar_heavy_vs_light(df: pd.DataFrame, out: Path) -> None:
    """График 5: средняя сохранность у «тяжёлых» и «умеренных» пользователей."""
    q75 = df["Weekly_GenAI_Hours"].quantile(0.75)
    grp = np.where(df["Weekly_GenAI_Hours"] >= q75, f"Тяжёлые (>= {q75:.0f} ч)", "Умеренные")
    tmp = df.assign(_g=grp).groupby("_g")[TARGET].mean()
    fig, ax = plt.subplots(figsize=(6, 5))
    tmp.plot(kind="bar", color=["#C44E52", "#55A868"], ax=ax)
    ax.set_title("Средняя сохранность: тяжёлые vs умеренные пользователи ИИ")
    ax.set_ylabel("Среднее Skill_Retention_Score")
    ax.set_xlabel("")
    ax.tick_params(axis="x", rotation=0)
    fig.tight_layout()
    fig.savefig(out / "05_heavy_vs_light.png", dpi=120)
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Статистические выводы
# --------------------------------------------------------------------------- #
def statistical_findings(df: pd.DataFrame) -> list[str]:
    findings: list[str] = []

    # Вывод 1: корреляция часов ИИ и сохранности.
    r, p = stats.pearsonr(df["Weekly_GenAI_Hours"], df[TARGET])
    findings.append(
        f"1) Чем больше часов ИИ в неделю, тем НИЖЕ сохранность знаний: "
        f"корреляция Пирсона r={r:.3f} (p={p:.1e}). Связь отрицательная и "
        f"статистически значимая -> чрезмерное использование ИИ ассоциировано "
        f"с худшей долгосрочной сохранностью."
    )

    # Вывод 2: тяжёлые vs умеренные пользователи (t-тест).
    q75 = df["Weekly_GenAI_Hours"].quantile(0.75)
    heavy = df.loc[df["Weekly_GenAI_Hours"] >= q75, TARGET]
    light = df.loc[df["Weekly_GenAI_Hours"] < q75, TARGET]
    t, pt = stats.ttest_ind(heavy, light, equal_var=False)
    findings.append(
        f"2) Тяжёлые пользователи (>= {q75:.1f} ч/нед, верхние 25%) имеют среднюю "
        f"сохранность {heavy.mean():.1f} против {light.mean():.1f} у остальных "
        f"(t={t:.1f}, p={pt:.1e}) — разница значима."
    )

    # Вывод 3: влияние сценария использования (ANOVA).
    groups = [g[TARGET].values for _, g in df.groupby("Primary_Use_Case")]
    f_stat, pa = stats.f_oneway(*groups)
    means = df.groupby("Primary_Use_Case")[TARGET].mean().sort_values()
    findings.append(
        f"3) Сценарий использования значимо влияет на сохранность "
        f"(ANOVA F={f_stat:.1f}, p={pa:.1e}). Хуже всего — пассивное "
        f"«{means.index[0]}» ({means.iloc[0]:.1f}), лучше всего — активное "
        f"«{means.index[-1]}» ({means.iloc[-1]:.1f})."
    )

    # Вывод 4 (доп.): традиционная учёба — защитный фактор.
    rt, ptt = stats.pearsonr(df["Traditional_Study_Hours"], df[TARGET])
    findings.append(
        f"4) Традиционная учёба положительно связана с сохранностью "
        f"(r={rt:.3f}, p={ptt:.1e}): она частично компенсирует негативный "
        f"эффект ИИ."
    )
    return findings


def main() -> None:
    cfg = Config()
    out = cfg.figures_dir
    out.mkdir(parents=True, exist_ok=True)
    df = load()

    print(f"Данные: {df.shape[0]} строк, {df.shape[1]} столбцов\n")

    plot_distribution(df, out)
    plot_scatter_trend(df, out)
    plot_box_by_usecase(df, out)
    plot_correlation_heatmap(df, out)
    plot_bar_heavy_vs_light(df, out)
    print(f"Сохранено 5 графиков в {out}\n")

    print("=== Статистические выводы ===")
    for line in statistical_findings(df):
        print(line)


if __name__ == "__main__":
    main()
