"""SQL write experiment."""
from qsynth.experiments.write_experiment import WriteExperiment
from qsynth.experiments import register_experiment
from qsynth.writers.sql_writer import SqlWriter


@register_experiment('sql')
class SqlWriteExperiment(WriteExperiment):
    """Experiment to write data as SQL DDL and INSERT statements."""
    
    def get_writer(self):
        return SqlWriter()

