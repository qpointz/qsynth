import argparse
import os.path
import sys
from abc import abstractmethod

import fastavro
import numpy
import pandavro
from croniter import croniter
from datetime import datetime
from pandas import DataFrame
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
from qsynth.provider import QsynthProviders


def create_faker(**kwargs):
    faker = Faker(**kwargs)
    faker.add_provider(AirTravelProvider)
    faker.add_provider(MarketDataProvider)
    faker.add_provider(VehicleProvider)
    faker.add_provider(QsynthProviders)
    return faker


class Writer:

    @abstractmethod
    def init_writer(self, init_path):
        print(f"Init writer on {init_path}")

    @abstractmethod
    def finalize_writer(self):
        print(f"Finalize writer on")

    @abstractmethod
    def write(self, path, pd: DataFrame, model_name, schema_name, model, writeparams={}):
        pass

    @staticmethod
    def ensure_path(path):
        if os.path.exists(path):
            os.remove(path)
        else:
            if not os.path.exists(path.parent):
                os.makedirs(path.parent)


class CsvWriter(Writer):
    def init_writer(self, init_path):
        print(f"Init CSV writer on {init_path}")

    def write(self, path, pd: DataFrame, model_name, schema_name, model, writeparams={}):
        Writer.ensure_path(path)
        pd.to_csv(path, **writeparams)


class ParquetWriter(Writer):
    def init_writer(self, init_path):
        print(f"Init Parquet writer on {init_path}")

    def write(self, path, pd: DataFrame, model_name, schema_name, model, writeparams={}):
        Writer.ensure_path(path)
        pd.to_parquet(path, **writeparams)

class AvroWriter(Writer):
    def init_writer(self, init_path):
        print(f"Init Avro writer on {init_path}")

    def write(self, path, pd: DataFrame, model_name, schema_name, model, writeparams={}):
        Writer.ensure_path(path)
        pandavro.to_avro(path, pd, **writeparams)
        m = fastavro.writer()

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

    def _get_columns_definition(dataset_schema, pd):
        attrs = []

        for tp, x in list(zip(list(pd.dtypes), dataset_schema['attributes'])):
            attrs.append(f"{x['name']} {SqlWriter.to_sql_type(tp.kind)} NOT NULL\n")
        return "\t "+ "\t,".join(attrs)

    def _write_insert(self, dataset_schema, pd, row):
        attrs = ",".join([x['name'] for x in dataset_schema['attributes']])

        type = [ x.kind for x in list(pd.dtypes)]
        values = list(zip(type, list(row)))

        def encode(k,o):
            match k:
                case 'O':
                    return "'" + str(o).replace("'", "''") + "'"
                case _ :
                    return str(o)

        enc = ",".join([encode(x[0],x[1]) for x in values])
        return f"INSERT INTO {dataset_schema['name']} ({attrs}) VALUES ({enc});"
        #list(zip(list(pd.dtypes), dataset_schema['attributes'])):


    def write(self, path, pd: DataFrame, model_name, schema_name, model, writeparams={}):
        self.last_path = path
        sc = [schema for schema in model.model['schemas'] if schema['name'] == schema_name]
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



class ErModelWriter(Writer):

    def __init__(self):
        self.last_path = None
        self.refs = []
        self.models = {}

    def init_writer(self, init_path):
        pass

    def write(self, path, pd: DataFrame, model_name, schema_name, model, writeparams={}):
        self.last_path = path
        sc = [schema for schema in model.model['schemas'] if schema['name'] == schema_name][0]
        names = [x['name'] for x in sc['attributes']]
        types = [SqlWriter.to_sql_type(x.kind) for x in list(pd.dtypes)]
        a = list(zip(names, types))
        for at in sc['attributes']:
            if at['type']=="${ref}":
                self.refs.append({'p': at['params']['dataset'], 'pa':at['params']['attribute'],'c' : schema_name, 'ca': at['name'], 'cord': at['params'].get('cord', "1-*")})
        self.models.update({schema_name:a})
        print(a)

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


def get_writer(name) -> Writer:
    if name == 'csv':
        return CsvWriter()

    if name == 'parquet':
        return ParquetWriter()

    if name == 'avro':
        return AvroWriter()

    raise Exception(f"Unknown writer '{name}'")


AttributeG = namedtuple("AttributeG", "key gen params")


class MultiModelsFaker:

    def __init__(self, models):
        self.models = {}
        for m in models:
            name = m['name']
            self.models.update({name: MultiModelsFaker.ModelFaker(m)})
        pass

    def explain(self):
        print(self.models)
        pass

    def generate_all(self):
        for k, m in self.models.items():
            m.generate()

    class ModelFaker:
        def __init__(self, model):
            if 'locales' not in model:
                model.update({'locales': 'en-US'})
            locales = model['locales']
            if 'rows' not in model:
                model.update({'rows': {'min': 1, 'max': 100}})
            if 'schemas' not in model:
                model.update({'schemas', []})
            self.model = model
            self.generated = {}

        def generate(self):
            self.generated = {}
            faker = create_faker(locale=self.model['locales'])
            for schema in self.model['schemas']:
                r = self.__generate_schema(faker, schema)
                key = schema['name']
                self.generated.update({key: r})

        def __resolve_gen(self, f, c):
            gn = c['type']
            if gn == "${ref}":
                ds = c['params']['dataset']
                col = c['params']['attribute']
                pd = self.generated[ds]

                def g(*args, **kwargs):
                    return random.choice(list(pd[col].values))

                return g
            elif hasattr(f, gn):
                g = getattr(f, gn)
                return g
            else:
                raise Exception(f"Unknown generator {gn}")

        def __generate_schema(self, fake, schema):
            gens = []
            for col in schema['attributes']:
                if 'params' not in col:
                    params = {}
                else:
                    params = col['params']
                gens.append(AttributeG(col['name'], self.__resolve_gen(fake, col), params))
            headers = [g.key for g in gens]
            rows = []

            rowobj = schema['rows']
            rowstogen = 0
            if isinstance(rowobj, numbers.Number):
                rowstogen = rowobj
            else:
                if type(rowobj) is dict:
                    minrows = 0
                    maxrows = 0
                    if 'min' not in rowobj:
                        minrows = 0
                    else:
                        minrows = int(rowobj['min'])
                    if 'max' not in rowobj:
                        maxrows = 10000
                    else:
                        maxrows = int(rowobj['max'])
                    rowstogen = fake.random.randint(minrows, maxrows)
                else:
                    raise Exception("rows spec not supported")

            for index in range(1, rowstogen + 1):
                row = [g.gen(**g.params) for g in gens]
                rows.append(row)

            dts = [numpy.array(x).dtype.name for x in rows[0]]
            pts = [numpy.dtype(type(x)) for x in rows[0]]
            d = {}
            for h, t, v in zip(headers, dts, pts):
                if str(t).startswith("str"):
                    d.update({h:"str"})
                else:
                    d.update({h:t})

            df = pd.DataFrame(rows, columns=headers)
            df.astype(dtype=d)
            return df


def from_model_file(p):
    with open(p, 'r') as yamlstream:
        mp = yaml.safe_load(yamlstream)
        return MultiModelsFaker(mp['models'])


class Experiment:
    pass


class CronFeedExperiment(Experiment):
    def __init__(self, p, models, relative_to):
        self.models = models
        self.relative_to = relative_to
        self.p = p

    def run(self):
        datesp = self.p['dates']
        from_date = datetime.now()
        to_date = datetime.max
        count = sys.maxsize
        if 'to' not in datesp and 'count' not in datesp:
            raise Exception("One of parameters 'to' or 'count' must be present")

        if 'from' in datesp:
            from_date = datetime.strptime(datesp['from'], '%Y-%m-%d')
        if 'to' in datesp:
            to_date = datetime.strptime(datesp['to'], '%Y-%m-%d')
        if 'count' in datesp:
            count = datesp['count']
        if from_date >= to_date:
            raise Exception("'from_date' can't be greater as 'to_date'")

        i = 0
        iter = croniter(self.p['cron'], from_date)
        cur_date = from_date
        path_template = Path(self.relative_to) / str(self.p['path'])
        writer = get_writer(self.p['writer']['name'])
        if 'params' in self.p['writer']:
            writeparams = self.p['writer']['params']
        else:
            writeparams = {}
        while i < count and cur_date <= to_date:
            cur_date = iter.next(datetime)
            print(cur_date)
            mmf = MultiModelsFaker(self.models)
            mmf.generate_all()
            for mn, m in mmf.models.items():
                for gn, g in m.generated.items():
                    p = {'model-name': mn, 'dataset-name': gn, 'cron-date': cur_date}
                    ap = Path(str(path_template).format(**p)).absolute()
                    writer.write(ap, g, mn, gn, m, writeparams)

class WriteExperiment:
    def __init__(self, p, models, relative_to):
        self.path = p['path']
        self.models = models
        self.relative_to = relative_to
        if 'params' not in p:
            self.writeParams = {}
        else:
            self.writeParams = p['params']

    def run(self):
        mmf = MultiModelsFaker(self.models)
        mmf.generate_all()
        w = self.writer()
        init_path = (Path(self.relative_to) / str(self.path)).absolute()
        w.init_writer(init_path)

        for mn, m in mmf.models.items():
            for gn, g in m.generated.items():
                p = {'model-name': mn, 'dataset-name': gn}
                ap = (Path(self.relative_to) / str(self.path).format(**p)).absolute()
                w.write(ap, g, mn, gn, m, self.writeParams)
        w.finalize_writer()


    def writer(self) -> Writer:
        pass


class CsvWriteExperiment(WriteExperiment):
    def writer(self) -> Writer:
        return CsvWriter()


class ParquetWriteExperiment(WriteExperiment):
    def writer(self) -> Writer:
        return ParquetWriter()

class AvroWriteExperiment(WriteExperiment):
    def writer(self) -> Writer:
        return AvroWriter()

class SqlWriteExperiment(WriteExperiment):
    def writer(self) -> Writer:
        return SqlWriter()

class ErModelWriteExperiment(WriteExperiment):
    def writer(self) -> Writer:
        return ErModelWriter()

class Experiments:
    def __init__(self, exps, models, relative_to=None):
        self.models = models
        self.exps = exps
        if relative_to:
            self.relative_to = Path(relative_to).parent
        else:
            self.relative_to = Path(__file__).parent

    def run_all(self):
        for k, v in self.exps.items():
            self.run(k)

    def run(self, name):
        e = self.exps[name]

        def get_by_type():
            if 'type' not in e:
                raise Exception(f"Experiment {name} type is missing")
            et = e['type']
            if et == 'csv':
                return CsvWriteExperiment(e, self.models, self.relative_to)
                pass
            if et == 'parquet':
                return ParquetWriteExperiment(e, self.models, self.relative_to)
                pass
            if et == 'avro':
                return AvroWriteExperiment(e, self.models, self.relative_to)
                pass
            if et == 'cron_feed':
                return CronFeedExperiment(e, self.models, self.relative_to)
                pass
            if et == 'sql':
                return SqlWriteExperiment(e, self.models, self.relative_to)
                pass
            if et == 'ermodel':
                return ErModelWriteExperiment(e, self.models, self.relative_to)
            raise Exception(f"Unknown experiment type {et}")

        inst = get_by_type()
        inst.run()


def load(p):
    with open(p, 'r') as yamlstream:
        mp = yaml.safe_load(yamlstream)
        return Experiments(mp['experiments'], mp['models'], relative_to=p)


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
    elif len(args.experiment) > 0:
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
