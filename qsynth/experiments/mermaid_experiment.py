"""Mermaid ER diagram write experiment."""
from qsynth.experiments.write_experiment import WriteExperiment
from qsynth.experiments import register_experiment
from qsynth.writers.mermaid_writer import ErMermaidModelWriter


@register_experiment('mermaid')
class ErMermaidModelWriteExperiment(WriteExperiment):
    """Experiment to write ER model in Mermaid diagram format."""
    
    def get_writer(self):
        return ErMermaidModelWriter()

