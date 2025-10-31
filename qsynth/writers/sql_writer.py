from pandas import DataFrame

from qsynth.writers.base import Writer
from qsynth.writers import register_writer
from qsynth.models import Schema


@register_writer('sql')
class SqlWriter(Writer):
    def __init__(self):
        self.last_path = None
        self.lines = []

    def init_writer(self, init_path):
        print(f"Init SQL writer on {init_path}")

    @staticmethod
    def to_sql_type(dk):
        match dk:
            case 'i':
                return 'INT'
            case 'O':
                return 'VARCHAR'
            case 'f':
                return 'DECIMAL(15,4)'
            case 'M':
                return 'DATE'
            case _:
                raise Exception(f"Unknown type kind {dk}")

    def _get_columns_definition(dataset_schema: Schema, pd):
        attrs = []

        for tp, x in list(zip(list(pd.dtypes), dataset_schema.attributes)):
            attrs.append(f"{x.name} {SqlWriter.to_sql_type(tp.kind)} NOT NULL\n")
        return "\t "+ "\t,".join(attrs)

    def _write_insert(self, dataset_schema: Schema, pd, row):
        attrs = ",".join([x.name for x in dataset_schema.attributes])

        type = [ x.kind for x in list(pd.dtypes)]
        values = list(zip(type, list(row)))

        def encode(k,o):
            match k:
                case 'O':
                    return "'" + str(o).replace("'", "''") + "'"
                case _ :
                    return str(o)

        enc = ",".join([encode(x[0],x[1]) for x in values])
        return f"INSERT INTO {dataset_schema.name} ({attrs}) VALUES ({enc});"

    def write(self, path, pd: DataFrame, model_name, schema_name, model, writeparams={}):
        self.last_path = path
        sc = [schema for schema in model.model.schemas if schema.name == schema_name]
        if not sc or len(sc) == 0:
            return
        dataset_schema = sc[0]
        self.lines.append(f"//=========== {model_name} {schema_name} ==========")
        self.lines.append(f"DROP TABLE IF EXISTS {schema_name};")

        self.lines.append(f"CREATE TABLE {schema_name} (")
        self.lines.append(SqlWriter._get_columns_definition(dataset_schema, pd))
        self.lines.append(f");")
        for index, row in pd.iterrows():
            self.lines.append(self._write_insert(dataset_schema, pd, row))

    def finalize_writer(self):
        Writer.ensure_path(self.last_path)
        with open(self.last_path, "w") as tf:
            tf.write("\n".join(self.lines))


