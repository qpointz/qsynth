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


def exec_cli():
    parsed = argument_parser().parse_args()
    if parsed.command == 'types':
        exec_types(parsed)
    elif parsed.command == 'run':
        exec_run(parsed)
    else:
        raise Exception(f"Unknown subcommand:{parsed.command}")


