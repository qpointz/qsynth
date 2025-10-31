"""Parquet write experiment."""
from qsynth.experiments.write_experiment import WriteExperiment
from qsynth.experiments import register_experiment
from qsynth.writers.parquet_writer import ParquetWriter


@register_experiment('parquet')
class ParquetWriteExperiment(WriteExperiment):
    """Experiment to write data in Parquet format."""
    
    def get_writer(self):
        return ParquetWriter()

