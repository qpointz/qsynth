from pandas import DataFrame

from qsynth.writers.base import Writer
from qsynth.writers import register_writer
from qsynth.main import clean_type_name


@register_writer('ermodel')
class ErModelWriter(Writer):
    def __init__(self):
        self.last_path = None
        self.refs = []
        self.models = {}

    def init_writer(self, init_path):
        pass

    def write(self, path, pd: DataFrame, model_name, schema_name, model, writeparams={}):
        self.last_path = path
        sc = [schema for schema in model.model.schemas if schema.name == schema_name][0]
        names = [x.name for x in sc.attributes]
        types = [str(x.kind) for x in list(pd.dtypes)]
        a = list(zip(names, types))
        for at in sc.attributes:
            if at.type=="${ref}":
                self.refs.append({'p': at.params.dataset, 'pa':at.params.attribute,'c' : schema_name, 'ca': at.name, 'cord': (at.params.cord or "1-*")})
        self.models.update({schema_name:a})

    def finalize_writer(self):
        Writer.ensure_path(self.last_path)
        with (open(self.last_path, "w") as tf):
            tf.write("@startuml\n")
            tf.write("skinparam linetype ortho\n")
            tf.write("left to right direction\n")
            for k,v in self.models.items():
                tf.write('entity "' +  k +'" {\n')
                for a in v:
                    tf.write(f"\t{a[0]}: {a[1]}\n")
                tf.write("}\n")
            for r in self.refs:
                tf.write('"'+r['p']+'" ')
                c = r['cord'].replace('1','||').replace('-','..').replace('*','|{')

                tf.write(f" {c} ")
                tf.write(' "'+r['c']+'"\n')

            tf.write("@enduml\n")
            tf.close()


