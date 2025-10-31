import pytest

from qsynth.main import argument_parser


def parse(*args):
    return argument_parser().parse_args(args)


def test_cli_types_all_parses():
    p = parse('types', '--all')
    assert p.command == 'types'
    assert p.all is True


def test_cli_types_find_parses():
    p = parse('types', '--find', 'rand')
    assert p.command == 'types'
    assert p.find == 'rand'


def test_cli_run_all_parses(tmp_path):
    dummy = tmp_path / 'dummy.yaml'
    dummy.write_text('experiments: {}\nmodels: []\n')
    p = parse('run', '--input-file', str(dummy), '--run-all-experiments')
    assert p.command == 'run'
    assert p.input_file == str(dummy)
    assert p.run_all_experiments is True

