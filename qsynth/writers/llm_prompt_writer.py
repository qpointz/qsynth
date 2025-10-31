from pandas import DataFrame

from qsynth.writers.base import Writer
from qsynth.writers import register_writer


@register_writer('llm-prompt')
class LLMPromptWriter(Writer):
    def __init__(self):
        self.last_path = None
        self.refs = []
        self.models = {}
        self.table_descriptions ={}
        self.write_params={}

    def init_writer(self, init_path):
        pass

    def write(self, path, pd: DataFrame, model_name, schema_name, model, writeparams={}):
        self.last_path = path
        self.write_params.update(writeparams)
        sc = [schema for schema in model.model.schemas if schema.name == schema_name][0]
        names = [x.name for x in sc.attributes]
        types = [str(x.kind) for x in list(pd.dtypes)]
        descriptions = [x.description for x in sc.attributes]
        a = list(zip(names, types, descriptions))
        for at in sc.attributes:
             if at.type=="${ref}":
                 self.refs.append({'p': at.params.dataset, 'pa':at.params.attribute,'c' : schema_name, 'ca': at.name, 'cord': (at.params.cord or "1-*")})
        self.models.update({schema_name:a})
        self.table_descriptions.update({schema_name: sc.description})

    def finalize_writer(self):
        Writer.ensure_path(self.last_path)
        with (open(self.last_path, "w") as tf):
            prolog = self.write_params.get('prologue')
            if prolog:
                tf.write(prolog)
            else:
                tf.write("You are SQL bot: Use following database model")

            tf.write("\nTables:\n")
            for k,v in self.models.items():
                tf.write('\t' + k+ ':')
                tdesc = self.table_descriptions.get(k)
                if tdesc:
                    tf.write(f"- {tdesc}")
                tf.write('\n')
                for a in v:
                    tf.write(f"\t\t- {a[0]}:{a[1]}")
                    if a[2]:
                        tf.write(f" - {a[2]}")
                    tf.write("\n")
                tf.write("\n")

            tf.write("Relations:\n")
            for r in self.refs:
                tf.write('\t' + r['p']+'.'+r['pa'] +f" -({r['cord']})-" + r['c']+'.'+r['ca']+'\n')

            rules = self.write_params.get('rules')
            if (rules):
                tf.write("\nRules:\n")
                if (isinstance(rules, str)):
                    tf.write(f"{rules}\n")
                if (isinstance(rules, list)):
                    for v in rules:
                        formated = str(v).replace('\n', '\n\t\t ')
                        tf.write(f"\t -{formated}\n")

            epilog = self.write_params.get('epilogue')
            if epilog:
                tf.write(epilog)

            tf.close()


