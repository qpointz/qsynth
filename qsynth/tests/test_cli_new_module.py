from qsynth import cli


def test_new_cli_module_parses_types():
    p = cli.argument_parser().parse_args(['types', '--all'])
    assert p.command == 'types'
    assert p.all is True


def test_new_cli_module_parses_run():
    p = cli.argument_parser().parse_args(['run', '-i', 'x.yaml', '-a'])
    assert p.command == 'run'
    assert p.input_file == 'x.yaml'
    assert p.run_all_experiments is True

