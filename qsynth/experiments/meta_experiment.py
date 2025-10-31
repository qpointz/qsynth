"""Metadata descriptor write experiment."""
from qsynth.experiments.write_experiment import WriteExperiment
from qsynth.experiments import register_experiment
from qsynth.writers.meta_writer import MetaDescriptorWriter


@register_experiment('meta')
class MetaDescriptorExperiment(WriteExperiment):
    """Experiment to write metadata descriptor YAML."""
    
    def get_writer(self):
        return MetaDescriptorWriter()

