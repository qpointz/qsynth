"""Experiments package for qsynth - modular experiment types."""
from typing import Dict, Type
from qsynth.experiments.base import Experiment


# Registry for experiment types
_EXPERIMENT_REGISTRY: Dict[str, Type[Experiment]] = {}


def register_experiment(experiment_type: str):
    """Decorator to register an experiment class."""
    def decorator(cls: Type[Experiment]):
        _EXPERIMENT_REGISTRY[experiment_type] = cls
        return cls
    return decorator


def get_experiment_class(experiment_type: str) -> Type[Experiment]:
    """Get experiment class by type name."""
    cls = _EXPERIMENT_REGISTRY.get(experiment_type)
    if cls is None:
        raise ValueError(f"Unknown experiment type: {experiment_type}")
    return cls


def list_experiment_types() -> list[str]:
    """List all registered experiment types."""
    return sorted(_EXPERIMENT_REGISTRY.keys())


# Import all experiment modules to trigger registration
from qsynth.experiments import (  # noqa: E402
    csv_experiment,
    parquet_experiment,
    avro_experiment,
    sql_experiment,
    ermodel_experiment,
    mermaid_experiment,
    llm_prompt_experiment,
    meta_experiment,
    cron_feed_experiment,
)

# Import base for convenience
from qsynth.experiments.base import Experiment  # noqa: E402

__all__ = [
    'Experiment',
    'register_experiment',
    'get_experiment_class',
    'list_experiment_types',
]

