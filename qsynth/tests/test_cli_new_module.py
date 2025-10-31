from qsynth import cli
from qsynth import main


def test_new_cli_module_parses_types():
    p = cli.argument_parser().parse_args(['types', '--all'])
    assert p.command == 'types'
    assert p.all is True


def test_new_cli_module_parses_run():
    p = cli.argument_parser().parse_args(['run', '-i', 'x.yaml', '-a'])
    assert p.command == 'run'
    assert p.input_file == 'x.yaml'
    assert p.run_all_experiments is True


def test_new_cli_module_parses_show_type():
    p = cli.argument_parser().parse_args(['show-type', 'first_name'])
    assert p.command == 'show-type'
    assert p.type_name == 'first_name'


def test_new_cli_module_parses_schema():
    p = cli.argument_parser().parse_args(['schema', 'test.yaml'])
    assert p.command == 'schema'
    assert p.yaml_file == 'test.yaml'
    assert p.model is None
    assert p.schema is None


def test_new_cli_module_parses_schema_with_filters():
    p = cli.argument_parser().parse_args(['schema', 'test.yaml', '--model', 'mymodel', '--schema', 'myschema'])
    assert p.command == 'schema'
    assert p.yaml_file == 'test.yaml'
    assert p.model == 'mymodel'
    assert p.schema == 'myschema'


def test_show_type_info_for_first_name(capsys):
    """Test showing information for first_name type."""
    main.show_type_info('first_name')
    captured = capsys.readouterr()
    assert 'Type: first_name' in captured.out
    assert 'Parameters:' in captured.out


def test_show_type_info_for_random_int(capsys):
    """Test showing information for random_int type with parameters."""
    main.show_type_info('random_int')
    captured = capsys.readouterr()
    assert 'Type: random_int' in captured.out
    # Rich uses unicode box drawing characters, so we just check for the parameter names
    assert 'min' in captured.out
    assert 'max' in captured.out


def test_show_type_info_for_ref_type(capsys):
    """Test showing information for ${ref} type."""
    main.show_type_info('${ref}')
    captured = capsys.readouterr()
    assert 'Type: ${ref}' in captured.out
    assert 'dataset:' in captured.out
    assert 'attribute:' in captured.out
    assert 'cord:' in captured.out
    assert 'Example:' in captured.out


def test_show_type_info_for_nonexistent(capsys):
    """Test showing information for non-existent type."""
    main.show_type_info('nonexistent_type_xyz')
    captured = capsys.readouterr()
    assert "Error: Type 'nonexistent_type_xyz' not found" in captured.out


def test_show_schema_info_for_formats_yaml(capsys):
    """Test showing schema information for formats.yaml."""
    main.show_schema_info('formats.yaml')
    captured = capsys.readouterr()
    assert 'Schema Information from: formats.yaml' in captured.out
    assert 'Model: formats' in captured.out
    assert 'fmttypes' in captured.out
    assert 'id' in captured.out
    assert 'last_name' in captured.out
    assert 'first_name' in captured.out


def test_show_schema_info_for_models_yaml(capsys):
    """Test showing schema information for models.yaml."""
    main.show_schema_info('models.yaml')
    captured = capsys.readouterr()
    assert 'Model: testmodel' in captured.out
    assert 'dataset1' in captured.out
    assert 'dataset2' in captured.out
    assert '${ref}' in captured.out
    assert '-> dataset1.id' in captured.out


def test_show_schema_info_with_model_filter(capsys):
    """Test showing schema information with model filter."""
    main.show_schema_info('moneta.yaml', model_name='moneta')
    captured = capsys.readouterr()
    assert 'Model: moneta' in captured.out
    assert 'clients' in captured.out
    assert 'accounts' in captured.out


def test_show_schema_info_with_schema_filter(capsys):
    """Test showing schema information with schema filter."""
    main.show_schema_info('moneta.yaml', model_name='moneta', schema_name='clients')
    captured = capsys.readouterr()
    assert 'Model: moneta' in captured.out
    assert 'Schema: clients' in captured.out
    assert 'client_id' in captured.out
    assert 'accounts' not in captured.out or 'accounts' not in captured.out.split('\n')[captured.out.split('\n').index('Schema: clients'):]


def test_show_schema_info_with_nonexistent_model(capsys):
    """Test showing schema information with non-existent model."""
    main.show_schema_info('formats.yaml', model_name='nonexistent')
    captured = capsys.readouterr()
    assert "Error: Model 'nonexistent' not found" in captured.out


def test_show_schema_info_with_nonexistent_file(capsys):
    """Test showing schema information with non-existent file."""
    main.show_schema_info('nonexistent.yaml')
    captured = capsys.readouterr()
    assert 'Error:' in captured.out or 'File' in captured.out or 'not found' in captured.out

