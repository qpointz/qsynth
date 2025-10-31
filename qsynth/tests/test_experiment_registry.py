"""Tests for experiment registry system."""
import pytest

from qsynth.experiments import (
    get_experiment_class,
    list_experiment_types,
    register_experiment,
    Experiment,
)
from qsynth.models import Model


def test_registry_lists_all_types():
    """Test that registry lists all experiment types."""
    types = list_experiment_types()
    assert len(types) > 0
    assert 'csv' in types
    assert 'parquet' in types
    assert 'sql' in types
    assert 'cron_feed' in types
    assert 'mermaid' in types


def test_registry_gets_experiment_class():
    """Test that registry can get experiment classes."""
    csv_class = get_experiment_class('csv')
    assert csv_class is not None
    assert issubclass(csv_class, Experiment)


def test_registry_rejects_unknown_type():
    """Test that registry raises error for unknown types."""
    with pytest.raises(ValueError, match="Unknown experiment type"):
        get_experiment_class('unknown_type_xyz')


def test_custom_experiment_registration():
    """Test that custom experiments can be registered."""
    @register_experiment('test_custom')
    class CustomExperiment(Experiment):
        def run(self):
            pass
    
    # Should be able to get it back
    cls = get_experiment_class('test_custom')
    assert cls == CustomExperiment
    
    # Should appear in list
    types = list_experiment_types()
    assert 'test_custom' in types


def test_experiment_instantiates_correctly():
    """Test that experiments can be instantiated from registry."""
    models = [Model(name="test", schemas=[])]
    
    csv_class = get_experiment_class('csv')
    experiment = csv_class(
        config={'type': 'csv', 'path': 'test.csv'},
        models=models
    )
    
    assert experiment.models == models
    assert experiment.path_template == 'test.csv'

