"""Qsynth - Programmatic synthetic data generation."""
from qsynth.models import Model, Schema, Attribute, RowSpec
from qsynth.main import MultiModelsFaker, Experiments
from qsynth.experiments import get_experiment_class, register_experiment
from qsynth.writers import get_writer, register_writer

__all__ = [
    # Core classes
    'Model',
    'Schema',
    'Attribute',
    'RowSpec',
    'MultiModelsFaker',
    'Experiments',
    # Utility functions
    'get_experiment_class',
    'register_experiment',
    'get_writer',
    'register_writer',
]

__version__ = '0.1.0'

