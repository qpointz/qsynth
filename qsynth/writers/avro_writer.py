from pandas import DataFrame
import pandavro

from qsynth.writers.base import Writer
from qsynth.writers import register_writer


@register_writer('avro')
class AvroWriter(Writer):
    def init_writer(self, init_path):
        print(f"Init Avro writer on {init_path}")

    def write(self, path, pd: DataFrame, model_name, schema_name, model, writeparams={}):
        Writer.ensure_path(path)
        pandavro.to_avro(path, pd, **writeparams)


