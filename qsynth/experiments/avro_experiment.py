"""Avro write experiment."""
from qsynth.experiments.write_experiment import WriteExperiment
from qsynth.experiments import register_experiment
from qsynth.writers.avro_writer import AvroWriter


@register_experiment('avro')
class AvroWriteExperiment(WriteExperiment):
    """Experiment to write data in Avro format."""
    
    def get_writer(self):
        return AvroWriter()

