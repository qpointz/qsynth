"""ER Model (PlantUML) write experiment."""
from qsynth.experiments.write_experiment import WriteExperiment
from qsynth.experiments import register_experiment
from qsynth.writers.ermodel_writer import ErModelWriter
from qsynth.experiments.write_experiment import WriteExperiment
from qsynth.experiments import register_experiment
from qsynth.writers.ermodel_writer import ErModelWriter


@register_experiment('ermodel')
class ErModelWriteExperiment(WriteExperiment):
    """Experiment to write ER model in PlantUML format."""
    
    def get_writer(self):
        return ErModelWriter()


@register_experiment('plantuml')
class PlantUmlWriteExperiment(WriteExperiment):
    """Alias for ER model experiment (PlantUML format)."""
    
    def get_writer(self):
        return ErModelWriter()

