import yaml
from pandas import DataFrame

from qsynth.writers.base import Writer
from qsynth.writers import register_writer


@register_writer('meta')
class MetaDescriptorWriter(Writer):
    def __init__(self):
        self.last_path = None
        self.write_params={}
        self.tables = []
        self.refs = []
        self.model_name = ""

    def init_writer(self, init_path):
        pass

    def write(self, path, pd: DataFrame, model_name, schema_name, model, writeparams={}):
        self.last_path = path
        self.model_name = model_name
        self.write_params.update(writeparams)
        sc = [schema for schema in model.model.schemas if schema.name == schema_name][0]
        names = [x.name for x in sc.attributes]
        types = [Writer.to_sql_type(x.kind) for x in list(pd.dtypes)] if hasattr(Writer, 'to_sql_type') else [str(x.kind) for x in list(pd.dtypes)]
        descriptions = [x.description for x in sc.attributes]
        a = list(zip(names, types, descriptions))
        attrs = []
        for o in a:
            da = {"name": o[0], "type":str(o[1]).lower(), "description": o[2]}
            attrs.append(da)
        self.tables.append({"name":schema_name, "attributes" : attrs})

        for at in sc.attributes:
            if at.type=="${ref}":
                if at.params and at.params.dataset and at.params.attribute:
                    self.refs.append({"parent": {"table" : at.params.dataset, "attribute" : at.params.attribute }, 'child': {"table" : schema_name, 'attribute': at.name}, "cardinality" : (at.params.cord or "1-*")})

    def finalize_writer(self):
        Writer.ensure_path(self.last_path)
        fm = {"schemas" : [{"name": self.model_name, "tables": self.tables, "references": self.refs}] }
        with (open(self.last_path, "w") as tf):
            yaml.dump(fm, tf, default_flow_style=False, sort_keys=False)


