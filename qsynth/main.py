import argparse
import sys
import inspect

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
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint

# Global console instance for rich output
console = Console()

def create_faker(**kwargs):
    faker = Faker(**kwargs)
    faker.add_provider(AirTravelProvider)
    faker.add_provider(MarketDataProvider)
    faker.add_provider(VehicleProvider)
    faker.add_provider(QsynthProviders)
    return faker




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
    providers = []
    for a in p:
        if a.startswith('_'):
            continue
        if not find or (find and a.startswith(find)):
            providers.append(a)
    
    if find:
        console.print(f"\n[bold cyan]Found {len(providers)} provider{'s' if len(providers) != 1 else ''} matching '{find}':[/bold cyan]\n")
    else:
        console.print(f"\n[bold cyan]Available Faker Providers ({len(providers)} total):[/bold cyan]\n")
    
    # Display in columns for better readability
    from rich.columns import Columns
    from rich.text import Text
    
    provider_texts = [Text(provider, style="green") for provider in sorted(providers)]
    columns = Columns(provider_texts, equal=True, expand=True)
    console.print(columns)
    console.print()


def show_type_info(type_name):
    """Show information about a specific Faker provider type, including its parameters."""
    faker = create_faker()
    
    # Check if this is a special reference type
    if type_name == "${ref}":
        console.print(f"\n[bold cyan]Type:[/bold cyan] [yellow]{type_name}[/yellow]")
        console.print("\n[bold]Description:[/bold]")
        console.print("  References a column from another dataset to establish relationships.")
        console.print("\n[bold green]Required Parameters:[/bold green]")
        console.print("  [cyan]dataset[/cyan]: str      - Name of the referenced dataset")
        console.print("  [cyan]attribute[/cyan]: str    - Name of the referenced attribute/column")
        console.print("\n[bold yellow]Optional Parameters:[/bold yellow]")
        console.print("  [cyan]cord[/cyan]: str         - Cardinality (default: '1-*')")
        console.print("                      Options: '1-1', '1-*', '*-*'")
        console.print("\n[bold]Example:[/bold]")
        example_code = """- name: customer_id
  type: ${ref}
  params:
    dataset: customers
    attribute: id
    cord: 1-*"""
        console.print(Syntax(example_code, "yaml", theme="monokai"))
        return
    
    # Check if the type exists in faker
    if not hasattr(faker, type_name):
        console.print(f"\n[bold red]Error:[/bold red] Type '[yellow]{type_name}[/yellow]' not found.")
        console.print("\n[dim]Use 'python -m qsynth types --all' to list all available types.[/dim]")
        console.print("[dim]Use 'python -m qsynth types --find <pattern>' to search for types.[/dim]")
        return
    
    # Get the method
    method = getattr(faker, type_name)
    
    # Get the signature
    try:
        sig = inspect.signature(method)
        console.print(f"\n[bold cyan]Type:[/bold cyan] [yellow]{type_name}[/yellow]")
        console.print(f"[bold]Description:[/bold] Faker provider method")
        
        # Create a table for parameters
        params = sig.parameters
        if len(params) > 0:
            table = Table(title="Parameters", show_header=True, header_style="bold magenta")
            table.add_column("Parameter", style="cyan", no_wrap=True)
            table.add_column("Type", style="green")
            table.add_column("Default", style="yellow")
            
            for param_name, param in params.items():
                if param_name == 'self':
                    continue
                
                # Get type
                type_str = "-"
                if param.annotation != inspect.Parameter.empty:
                    type_str = param.annotation.__name__ if hasattr(param.annotation, '__name__') else str(param.annotation)
                
                # Get default
                default_str = "-"
                if param.default != inspect.Parameter.empty:
                    default_str = str(param.default)
                
                table.add_row(param_name, type_str, default_str)
            
            console.print("\n")
            console.print(table)
        else:
            console.print("\n[dim]Parameters: None[/dim]")
        
        # Try to show a sample output
        console.print("\n[bold green]Sample Output:[/bold green]")
        try:
            if sig:
                # Build kwargs for parameters that have defaults
                kwargs = {}
                for param_name, param in params.items():
                    if param_name != 'self' and param.default != inspect.Parameter.empty:
                        kwargs[param_name] = param.default
                
                # Call the method
                sample = method(**kwargs)
                sample_str = str(sample)
                if len(sample_str) > 100:
                    sample_str = sample_str[:100] + "..."
                console.print(f"  [green]{sample_str}[/green]")
        except Exception as e:
            console.print(f"  [dim red](Could not generate sample: {e})[/dim red]")
            
    except Exception as e:
        console.print(f"\n[bold red]Error inspecting signature:[/bold red] {e}")
        console.print("\n[dim]Note: This may be a property or non-callable attribute.[/dim]")


def show_schema_info(yaml_file, model_name=None, schema_name=None):
    """Show schema information from a YAML file with rich formatting."""
    try:
        # Load and parse YAML file
        with open(yaml_file, 'r') as yamlstream:
            mp = yaml.safe_load(yamlstream)
        
        if 'models' not in mp:
            console.print(f"\n[bold red]Error:[/bold red] No 'models' section found in YAML file.")
            return
        
        # Parse models
        models = [Model(**m) for m in mp['models']]
        
        # Filter by model name if specified
        if model_name:
            models = [m for m in models if m.name == model_name]
            if not models:
                console.print(f"\n[bold red]Error:[/bold red] Model '[yellow]{model_name}[/yellow]' not found in YAML file.")
                return
        
        # Display each model
        console.print(f"\n[bold cyan]Schema Information from:[/bold cyan] [yellow]{yaml_file}[/yellow]\n")
        
        for model in models:
            # Model header
            locales_str = model.locales if isinstance(model.locales, str) else ', '.join(model.locales)
            console.print(Panel(
                f"[bold]Model:[/bold] {model.name}\n"
                f"[bold]Locales:[/bold] {locales_str}\n"
                f"[bold]Schemas:[/bold] {len(model.schemas)}",
                title="[cyan]Model Overview[/cyan]",
                border_style="cyan"
            ))
            console.print()
            
            # Filter schemas if specified
            schemas_to_display = model.schemas
            if schema_name:
                schemas_to_display = [s for s in schemas_to_display if s.name == schema_name]
                if not schemas_to_display:
                    console.print(f"[bold red]Schema '[yellow]{schema_name}[/yellow]' not found in model '[yellow]{model.name}[/yellow]'[/bold red]\n")
                    continue
            
            # Display each schema
            for schema in schemas_to_display:
                # Schema info
                rows_str = str(schema.rows) if isinstance(schema.rows, int) else f"{schema.rows.min}-{schema.rows.max} (random)"
                schema_title = f"[green]Schema: {schema.name}[/green]"
                if schema.description:
                    schema_title += f" - {schema.description}"
                
                console.print(schema_title)
                console.print(f"[dim]Rows:[/dim] {rows_str}")
                console.print()
                
                # Attributes table
                if schema.attributes:
                    table = Table(
                        title=f"Attributes ({len(schema.attributes)} columns)",
                        show_header=True,
                        header_style="bold magenta",
                        box=None
                    )
                    table.add_column("Name", style="cyan", no_wrap=True)
                    table.add_column("Type", style="green")
                    table.add_column("Parameters", style="yellow")
                    table.add_column("Description", style="dim")
                    
                    for attr in schema.attributes:
                        # Format params
                        params_str = "-"
                        if attr.params:
                            params_list = []
                            if attr.type == "${ref}":
                                if attr.params.dataset and attr.params.attribute:
                                    params_list.append(f"-> {attr.params.dataset}.{attr.params.attribute}")
                                if attr.params.cord:
                                    params_list.append(f"card: {attr.params.cord}")
                            elif attr.params.min is not None and attr.params.max is not None:
                                params_list.append(f"min: {attr.params.min}, max: {attr.params.max}")
                            elif attr.params.elements:
                                elements_preview = ', '.join(str(e)[:20] for e in attr.params.elements[:3])
                                if len(attr.params.elements) > 3:
                                    elements_preview += f", ... (+{len(attr.params.elements)-3} more)"
                                params_list.append(f"[{elements_preview}]")
                            elif attr.params.text:
                                params_list.append(f'"{attr.params.text}"')
                            
                            if params_list:
                                params_str = "; ".join(params_list)
                        
                        table.add_row(
                            attr.name,
                            attr.type,
                            params_str,
                            attr.description or "-"
                        )
                    
                    console.print(table)
                else:
                    console.print("[dim]No attributes defined[/dim]")
                
                console.print()
        
    except FileNotFoundError:
        console.print(f"\n[bold red]Error:[/bold red] File '[yellow]{yaml_file}[/yellow]' not found.")
    except yaml.YAMLError as e:
        console.print(f"\n[bold red]Error parsing YAML:[/bold red] {e}")
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")


def list_schema_content(yaml_file, mp):
    """List all schemas, models, and experiments from a YAML file."""
    console.print(f"\n[bold cyan]Schema Overview:[/bold cyan] [yellow]{yaml_file}[/yellow]\n")
    
    # List experiments
    if 'experiments' in mp and mp['experiments']:
        console.print(f"[bold green]Experiments ({len(mp['experiments'])}):[/bold green]")
        for exp_name in sorted(mp['experiments'].keys()):
            exp_type = mp['experiments'][exp_name].get('type', 'unknown')
            console.print(f"  [cyan]{exp_name}[/cyan] - type: [yellow]{exp_type}[/yellow]")
        console.print()
    else:
        console.print("[dim]No experiments defined[/dim]\n")
    
    # List models and their schemas
    if 'models' in mp and mp['models']:
        console.print(f"[bold green]Models ({len(mp['models'])}):[/bold green]")
        for model in mp['models']:
            model_name = model.get('name', 'unnamed')
            schemas = model.get('schemas', [])
            console.print(f"  [cyan]{model_name}[/cyan] - {len(schemas)} schema(s)")
            for schema in schemas:
                schema_name = schema.get('name', 'unnamed')
                rows = schema.get('rows', 'N/A')
                if isinstance(rows, dict):
                    rows = f"{rows.get('min', '?')}-{rows.get('max', '?')} (random)"
                rows_str = f"[dim]{rows} row(s)[/dim]"
                console.print(f"    • [green]{schema_name}[/green] {rows_str}")
        console.print()
    else:
        console.print("[dim]No models defined[/dim]\n")


def describe_experiments(yaml_file):
    """Describe experiments configuration from a YAML file."""
    try:
        with open(yaml_file, 'r') as yamlstream:
            mp = yaml.safe_load(yamlstream)
        
        if 'experiments' not in mp or not mp['experiments']:
            console.print(f"\n[bold yellow]No experiments defined in:[/bold yellow] [yellow]{yaml_file}[/yellow]\n")
            return
        
        console.print(f"\n[bold cyan]Experiments Configuration:[/bold cyan] [yellow]{yaml_file}[/yellow]\n")
        
        experiments = mp['experiments']
        for exp_name, exp_config in sorted(experiments.items()):
            # Experiment name header
            console.print(Panel(
                f"[bold]Type:[/bold] {exp_config.get('type', 'unknown')}",
                title=f"[cyan]{exp_name}[/cyan]",
                border_style="cyan"
            ))
            
            # Path
            if 'path' in exp_config:
                console.print(f"[green]Output Path:[/green] {exp_config['path']}")
            
            # Special parameters based on type
            if exp_config.get('type') == 'cron_feed':
                if 'cron' in exp_config:
                    console.print(f"[green]Schedule:[/green] {exp_config['cron']}")
                if 'dates' in exp_config:
                    dates = exp_config['dates']
                    console.print(f"[green]Date Range:[/green] {dates.get('from')} to {dates.get('to')}")
                    console.print(f"[green]Max Files:[/green] {dates.get('count')}")
                if 'writer' in exp_config:
                    console.print(f"[green]Writer:[/green] {exp_config['writer'].get('name')}")
            
            # General params
            if 'params' in exp_config and exp_config['params']:
                console.print("[bold]Parameters:[/bold]")
                for key, value in exp_config['params'].items():
                    if isinstance(value, dict):
                        console.print(f"  [cyan]{key}[/cyan]:")
                        for subkey, subvalue in value.items():
                            console.print(f"    - [yellow]{subkey}[/yellow]: {subvalue}")
                    elif isinstance(value, list):
                        console.print(f"  [cyan]{key}[/cyan]:")
                        for item in value:
                            console.print(f"    - {item}")
                    else:
                        console.print(f"  [cyan]{key}[/cyan]: {value}")
            
            console.print()
        
    except FileNotFoundError:
        console.print(f"\n[bold red]Error:[/bold red] File '[yellow]{yaml_file}[/yellow]' not found.")
    except yaml.YAMLError as e:
        console.print(f"\n[bold red]Error parsing YAML:[/bold red] {e}")
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")


def argument_parser():
    argp = argparse.ArgumentParser(prog="qsynth")
    subparsers = argp.add_subparsers(dest='command')
    types = subparsers.add_parser('types')
    types.add_argument('--all', action='store_true')
    types.add_argument('--find')

    run = subparsers.add_parser('run')
    run.add_argument('--input-file', '-i', metavar='input', required=True)
    run.add_argument('--experiment', '-e', nargs='+', metavar='experiments')
    run.add_argument('--run-all-experiments', '-a', action='store_true')

    show = subparsers.add_parser('show-type', help='Show information about a specific type')
    show.add_argument('type_name', metavar='TYPE', help='Name of the type to inspect')

    show_schema = subparsers.add_parser('schema', help='Show schema information from YAML file')
    show_schema.add_argument('yaml_file', metavar='YAML_FILE', help='Path to the YAML model file')
    show_schema.add_argument('--model', '-m', metavar='MODEL_NAME', help='Filter by specific model name')
    show_schema.add_argument('--schema', '-s', metavar='SCHEMA_NAME', help='Filter by specific schema name')
    show_schema.add_argument('--experiments', action='store_true', help='Describe experiments configuration')

    shell = subparsers.add_parser('shell', help='Start interactive REPL shell with a YAML file')
    shell.add_argument('yaml_file', metavar='YAML_FILE', help='Path to the YAML model file')

    return argp


def exec_types(args):
    if args.find:
        list_providers(args.find)
    elif args.all:
        list_providers()


def exec_run(args):
    if args.run_all_experiments:
        run_all_experiments(args.input_file)
    elif args.experiment:
        run_experiments(args.input_file, *args.experiment)


def exec_show_type(args):
    show_type_info(args.type_name)


def exec_show_schema(args):
    # Handle experiment description mode
    if args.experiments:
        describe_experiments(args.yaml_file)
        return
    
    # Handle listing mode when no specific filters applied
    # List mode shows overview when no specific model/schema filters are applied
    if not args.model and not args.schema:
        try:
            with open(args.yaml_file, 'r') as yamlstream:
                mp = yaml.safe_load(yamlstream)
            
            list_schema_content(args.yaml_file, mp)
            
        except FileNotFoundError:
            console.print(f"\n[bold red]Error:[/bold red] File '[yellow]{args.yaml_file}[/yellow]' not found.")
        except yaml.YAMLError as e:
            console.print(f"\n[bold red]Error parsing YAML:[/bold red] {e}")
        except Exception as e:
            console.print(f"\n[bold red]Error:[/bold red] {e}")
        return
    
    # Normal schema info mode (with filters)
    show_schema_info(args.yaml_file, model_name=args.model, schema_name=args.schema)


def exec_shell(args):
    """Start the interactive REPL shell."""
    from qsynth.repl import QsynthRepl
    repl = QsynthRepl(args.yaml_file)
    repl.run()


def exec_cli():
    parsed = argument_parser().parse_args()
    if parsed.command == 'types':
        exec_types(parsed)
    elif parsed.command == 'run':
        exec_run(parsed)
    elif parsed.command == 'show-type':
        exec_show_type(parsed)
    elif parsed.command == 'schema':
        exec_show_schema(parsed)
    elif parsed.command == 'shell':
        exec_shell(parsed)
    else:
        raise Exception(f"Unknown subcommand:{parsed.command}")


if __name__ == '__main__':
    exec_cli()
