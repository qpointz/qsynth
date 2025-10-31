import argparse

from qsynth import main as _main


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
        _main.list_providers(args.find)
    elif args.all:
        _main.list_providers()


def exec_run(args):
    if args.run_all_experiments:
        _main.run_all_experiments(args.input_file)
    elif args.experiment:
        _main.run_experiments(args.input_file, *args.experiment)


def exec_show_type(args):
    _main.show_type_info(args.type_name)


def exec_show_schema(args):
    # Handle experiment description mode
    if args.experiments:
        _main.describe_experiments(args.yaml_file)
        return
    
    # Handle listing mode when no specific filters applied
    # List mode shows overview when no specific model/schema filters are applied
    if not args.model and not args.schema:
        try:
            import yaml
            with open(args.yaml_file, 'r') as yamlstream:
                mp = yaml.safe_load(yamlstream)
            
            _main.list_schema_content(args.yaml_file, mp)
            
        except FileNotFoundError:
            _main.console.print(f"\n[bold red]Error:[/bold red] File '[yellow]{args.yaml_file}[/yellow]' not found.")
        except yaml.YAMLError as e:
            _main.console.print(f"\n[bold red]Error parsing YAML:[/bold red] {e}")
        except Exception as e:
            _main.console.print(f"\n[bold red]Error:[/bold red] {e}")
        return
    
    # Normal schema info mode (with filters)
    _main.show_schema_info(args.yaml_file, model_name=args.model, schema_name=args.schema)


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


