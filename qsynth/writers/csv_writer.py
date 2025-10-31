from pandas import DataFrame

from qsynth.writers.base import Writer
from qsynth.writers import register_writer


@register_writer('csv')
class CsvWriter(Writer):
    def init_writer(self, init_path):
        print(f"Init CSV writer on {init_path}")

    def write(self, path, pd: DataFrame, model_name, schema_name, model, writeparams={}):
        Writer.ensure_path(path)
        pd.to_csv(path, **writeparams)


