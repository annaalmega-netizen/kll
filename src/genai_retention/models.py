"""Модели ML + два паттерна проектирования (Задание 4).

Паттерн 1 — STRATEGY (поведенческий):
    `ModelStrategy` задаёт единый интерфейс (build/name) для разных алгоритмов
    регрессии. Тренер работает с абстракцией, не зная конкретного класса
    модели, и алгоритм можно подменить «на лету» без правки кода обучения.

Паттерн 2 — FACTORY METHOD (порождающий):
    `ModelFactory.create(name)` инкапсулирует создание нужной стратегии по
    строковому ключу. Добавление новой модели = регистрация в фабрике, без
    изменений в пайплайне и приложении.

Паттерны из РАЗНЫХ групп (поведенческий + порождающий), как требует задание.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from sklearn.base import RegressorMixin
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor

from .exceptions import UnknownModelError
from .logger import get_logger

logger = get_logger("models")


# --------------------------------------------------------------------------- #
# Паттерн STRATEGY (поведенческий)
# --------------------------------------------------------------------------- #
class ModelStrategy(ABC):
    """Абстрактная стратегия модели регрессии."""

    #: человекочитаемое имя стратегии
    name: str = "abstract"

    @abstractmethod
    def build(self, random_state: int) -> RegressorMixin:
        """Создать новый sklearn-эстиматор этой стратегии."""
        raise NotImplementedError


class LinearRegressionStrategy(ModelStrategy):
    """Простая, интерпретируемая базовая линия."""

    name = "linear"

    def build(self, random_state: int) -> RegressorMixin:
        return LinearRegression()


class RandomForestStrategy(ModelStrategy):
    """Ансамбль деревьев: ловит нелинейности и взаимодействия признаков."""

    name = "random_forest"

    def build(self, random_state: int) -> RegressorMixin:
        return RandomForestRegressor(
            n_estimators=200,
            max_depth=None,
            min_samples_leaf=5,
            n_jobs=-1,
            random_state=random_state,
        )


class DecisionTreeStrategy(ModelStrategy):
    """Одно дерево: запасная стратегия / демонстрация расширяемости фабрики."""

    name = "decision_tree"

    def build(self, random_state: int) -> RegressorMixin:
        return DecisionTreeRegressor(max_depth=8, random_state=random_state)


# --------------------------------------------------------------------------- #
# Паттерн FACTORY METHOD (порождающий)
# --------------------------------------------------------------------------- #
class ModelFactory:
    """Фабрика стратегий моделей по строковому ключу."""

    _registry: dict[str, type[ModelStrategy]] = {
        LinearRegressionStrategy.name: LinearRegressionStrategy,
        RandomForestStrategy.name: RandomForestStrategy,
        DecisionTreeStrategy.name: DecisionTreeStrategy,
    }

    @classmethod
    def create(cls, name: str) -> ModelStrategy:
        try:
            strategy_cls = cls._registry[name]
        except KeyError:
            raise UnknownModelError(
                f"Неизвестная модель {name!r}. Доступны: {sorted(cls._registry)}"
            ) from None
        logger.info("Фабрика создаёт стратегию модели: %s", name)
        return strategy_cls()

    @classmethod
    def available(cls) -> list[str]:
        return sorted(cls._registry)
