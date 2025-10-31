"""CSV write experiment."""
from qsynth.experiments.write_experiment import WriteExperiment
from qsynth.experiments import register_experiment
from qsynth.writers.csv_writer import CsvWriter


@register_experiment('csv')
class CsvWriteExperiment(WriteExperiment):
    """Experiment to write data in CSV format."""
    
    def get_writer(self):
        return CsvWriter()

