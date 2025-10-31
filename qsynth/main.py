import argparse
import sys

import fastavro
import numpy
from croniter import croniter
from datetime import datetime
import numbers
from faker import Faker
from faker_airtravel import AirTravelProvider
from faker_marketdata import MarketDataProvider
from faker_vehicle import VehicleProvider
import random
import yaml
from pathlib import Path
from collections import namedtuple
import pandas as pd
from pandas import DataFrame
from qsynth.provider import QsynthProviders
from qsynth.models import Model, Schema, Attribute, RowSpec
from typing import List
import re

def create_faker(**kwargs):
    faker = Faker(**kwargs)
    faker.add_provider(AirTravelProvider)
    faker.add_provider(MarketDataProvider)
    faker.add_provider(VehicleProvider)
    faker.add_provider(QsynthProviders)
    return faker


class SqlWriter:
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

    def _get_columns_definition(dataset_schema, pd):
        attrs = []

        for tp, x in list(zip(list(pd.dtypes), dataset_schema.attributes)):
            attrs.append(f"{x.name} {SqlWriter.to_sql_type(tp.kind)} NOT NULL\n")
        return "\t "+ "\t,".join(attrs)

    def _write_insert(self, dataset_schema, pd, row):
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
        #list(zip(list(pd.dtypes), dataset_schema['attributes'])):


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
        from qsynth.writers.base import Writer
        Writer.ensure_path(self.last_path)
        with open(self.last_path, "w") as tf:
            tf.write("\n".join(self.lines))

def clean_type_name(s):
    typec = r"\([^)]+\)"
    return re.sub(typec, '', str(s).lower())

class MetaDescriptorWriter:
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
        types = [SqlWriter.to_sql_type(x.kind) for x in list(pd.dtypes)]
        descriptions = [x.description for x in sc.attributes]
        a = list(zip(names, types, descriptions))
        attrs = []
        for o in a:
            da = {"name": o[0], "type":clean_type_name(o[1]), "description": o[2]}
            attrs.append(da)
        self.tables.append({"name":schema_name, "attributes" : attrs})

        for at in sc.attributes:
            if at.type == "${ref}":
                if at.params and at.params.dataset and at.params.attribute:
                    self.refs.append({"parent": {"table" : at.params.dataset, "attribute" : at.params.attribute }, 'child': {"table" : schema_name, 'attribute': at.name}, "cardinality" : (at.params.cord or "1-*")})


    def finalize_writer(self):
        from qsynth.writers.base import Writer
        Writer.ensure_path(self.last_path)
        fm = {"schemas" : [{"name": self.model_name, "tables": self.tables, "references": self.refs}] }
        with (open(self.last_path, "w") as tf):
            yaml.dump(fm, tf, default_flow_style=False, sort_keys=False)


class LLMPromptWriter:
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
        types = [SqlWriter.to_sql_type(x.kind) for x in list(pd.dtypes)]
        descriptions = [x.description for x in sc.attributes]
        a = list(zip(names, types, descriptions))
        for at in sc.attributes:
             if at.type == "${ref}":
                 if at.params and at.params.dataset and at.params.attribute:
                     self.refs.append({'p': at.params.dataset, 'pa': at.params.attribute,'c' : schema_name, 'ca': at.name, 'cord': (at.params.cord or "1-*")})
        self.models.update({schema_name:a})
        self.table_descriptions.update({schema_name: sc.description})
        # removed debug print

    def finalize_writer(self):
        from qsynth.writers.base import Writer
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

class ErMermaidModelWriter:

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
        types = [SqlWriter.to_sql_type(x.kind) for x in list(pd.dtypes)]
        a = list(zip(names, types))
        for at in sc.attributes:
            if at.type=="${ref}":
                if at.params and at.params.dataset and at.params.attribute:
                    self.refs.append({'p': at.params.dataset, 'pa': at.params.attribute,'c' : schema_name, 'ca': at.name, 'cord': (at.params.cord or "1-*")})
        self.models.update({schema_name:a})
        # removed debug print

    def finalize_writer(self):

        from qsynth.writers.base import Writer
        Writer.ensure_path(self.last_path)
        with (open(self.last_path, "w") as tf):
            tf.write("erDiagram\n")
            for k,v in self.models.items():
                tf.write(k +' {\n')
                for a in v:
                    typename = clean_type_name(a[1])
                    tf.write(f"\t{typename} {a[0]}\n")
                tf.write("}\n")
            for r in self.refs:
                tf.write(''+r['p']+' ')
                c = r['cord'].replace('1','||').replace('-','--').replace('*','o{')

                tf.write(f" {c}")
                tf.write(' '+r['c']+':has\n')
            tf.close()

class ErModelWriter:

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
        types = [SqlWriter.to_sql_type(x.kind) for x in list(pd.dtypes)]
        a = list(zip(names, types))
        for at in sc.attributes:
            if at.type == "${ref}":
                if at.params and at.params.dataset and at.params.attribute:
                    self.refs.append({'p': at.params.dataset, 'pa': at.params.attribute,'c' : schema_name, 'ca': at.name, 'cord': (at.params.cord or "1-*")})
        self.models.update({schema_name:a})
        # removed debug print

    def finalize_writer(self):
        from qsynth.writers.base import Writer
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



def get_writer(name):
    from qsynth.writers import get_writer as _gw
    return _gw(name)


AttributeG = namedtuple("AttributeG", "key gen params")


class MultiModelsFaker:

    def __init__(self, models):
        self.models = {}
        for m in models:
            # Parse dict to Pydantic model
            model_obj = Model(**m) if isinstance(m, dict) else m
            self.models.update({model_obj.name: MultiModelsFaker.ModelFaker(model_obj)})

    def explain(self):
        print(self.models)

    def generate_all(self):
        for k, m in self.models.items():
            m.generate()

    class ModelFaker:
        def __init__(self, model: Model):
            self.model: Model = model
            self.generated = {}

        def generate(self):
            self.generated = {}
            locale = self.model.locales if isinstance(self.model.locales, str) else self.model.locales[0]
            faker = create_faker(locale=locale)
            for schema in self.model.schemas:
                r = self.__generate_schema(faker, schema)
                key = schema.name
                self.generated.update({key: r})

        def __resolve_gen(self, f, attr: Attribute):
            gn = attr.type
            if gn == "${ref}":
                if not attr.params or not attr.params.dataset or not attr.params.attribute:
                    raise ValueError(f"${ref} type requires params.dataset and params.attribute")
                ds = attr.params.dataset
                col = attr.params.attribute
                pd = self.generated[ds]

                def g(*args, **kwargs):
                    return random.choice(list(pd[col].values))

                return g
            elif hasattr(f, gn):
                g = getattr(f, gn)
                return g
            else:
                raise ValueError(f"Unknown generator {gn}")

        def __generate_schema(self, fake, schema: Schema):
            gens = []
            for attr in schema.attributes:
                params_dict = attr.params.model_dump() if attr.params else {}
                # Remove None values
                params_dict = {k: v for k, v in params_dict.items() if v is not None}
                gens.append(AttributeG(attr.name, self.__resolve_gen(fake, attr), params_dict))
            
            headers = [g.key for g in gens]
            rows = []

            # Handle row count specification
            rowobj = schema.rows
            rowstogen = 0
            if isinstance(rowobj, int):
                rowstogen = rowobj
            elif isinstance(rowobj, RowSpec):
                rowstogen = fake.random.randint(rowobj.min, rowobj.max)
            else:
                raise ValueError(f"Unsupported row spec type: {type(rowobj)}")

            for index in range(1, rowstogen + 1):
                row = [g.gen(**g.params) for g in gens]
                rows.append(row)

            # Build DataFrame and enforce dtypes when rows exist
            df = pd.DataFrame(rows, columns=headers)
            if len(rows) == 0:
                return df

            dts = [numpy.array(x).dtype.name for x in rows[0]]
            pts = [numpy.dtype(type(x)) for x in rows[0]]
            d = {}
            for h, t, v in zip(headers, dts, pts):
                if str(t).startswith("str"):
                    d.update({h: "str"})
                else:
                    d.update({h: t})

            df = df.astype(dtype=d)
            return df


def from_model_file(p):
    with open(p, 'r') as yamlstream:
        mp = yaml.safe_load(yamlstream)
        models = [Model(**m) for m in mp['models']]
        return MultiModelsFaker(models)


# Experiment classes moved to qsynth.experiments package
# Imported dynamically via registry in Experiments.run()


class Experiments:
    """Manager for running multiple experiments."""
    
    def __init__(self, exps, models, relative_to=None):
        self.models: List[Model] = models
        self.exps = exps
        if relative_to:
            self.relative_to = Path(relative_to).parent
        else:
            self.relative_to = Path(__file__).parent

    def run_all(self):
        """Run all configured experiments."""
        for name in self.exps.keys():
            self.run(name)

    def run(self, name):
        """Run a single experiment by name."""
        experiment_config = self.exps[name]
        
        if 'type' not in experiment_config:
            raise ValueError(f"Experiment '{name}' is missing required 'type' field")
        
        experiment_type = experiment_config['type']
        
        # Use registry to get experiment class
        from qsynth.experiments import get_experiment_class
        experiment_class = get_experiment_class(experiment_type)
        
        # Create and run experiment
        experiment = experiment_class(experiment_config, self.models, self.relative_to)
        experiment.run()


def load(p):
    with open(p, 'r') as yamlstream:
        mp = yaml.safe_load(yamlstream)
        models = [Model(**m) for m in mp['models']]
        return Experiments(mp['experiments'], models, relative_to=p)


def run_experiments(path, *args):
    input = load(Path(path).absolute())
    for experiment in args:
        input.run(experiment)


def run_all_experiments(path):
    input = load(Path(path).absolute())
    input.run_all()


def list_providers(find=None):
    faker = create_faker()
    p = dir(faker)
    for a in p:
        if a.startswith('_'):
            continue
        if not find or (find and a.startswith(find)):
            print(a)
    pass


def argument_parser():
    argp = argparse.ArgumentParser(prog="PROG")
    subparsers = argp.add_subparsers(dest='command')
    types = subparsers.add_parser('types')
    types.add_argument('--all', action='store_true')
    types.add_argument('--find')

    run = subparsers.add_parser('run')
    run.add_argument('--input-file', '-i', metavar='input', required=True)
    run.add_argument('--experiment', '-e', nargs='+', metavar='experiments')
    run.add_argument('--run-all-experiments', '-a', action='store_true')
    #
    # argp.add_argument('--info', action='store_true')
    # argp.add_argument('--list-providers', '-lp', action='store_true')

    return argp


def exec_types(args):
    if args.find:
        print('by name')
        list_providers(args.find)
    elif args.all:
        list_providers()


def exec_run(args):
    if args.run_all_experiments:
        run_all_experiments(args.input_file)
    elif args.experiment:
        run_experiments(args.input_file, *args.experiment)


def exec_cli():
    parsed = argument_parser().parse_args()
    print(parsed)
    if parsed.command == 'types':
        exec_types(parsed)
    elif parsed.command == 'run':
        exec_run(parsed)
    else:
        raise Exception(f"Unknown subcommand:{parsed.command}")


if __name__ == '__main__':
    exec_cli()
