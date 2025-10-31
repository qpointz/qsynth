"""Tests for the REPL shell."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from qsynth.repl import QsynthRepl


def test_repl_initialization(tmp_path):
    """Test REPL can be initialized with a valid YAML file."""
    # Create a minimal YAML file
    yaml_content = """
models:
  - name: testmodel
    locales: ['en-US']
    schemas:
      - name: dataset1
        rows: 100
        attributes:
          - name: id
            type: random_int
            params:
              min: 1
              max: 1000

experiments:
  write_csv:
    type: csv
    path: "./output/test.csv"
"""
    yaml_file = tmp_path / "test.yaml"
    yaml_file.write_text(yaml_content)
    
    repl = QsynthRepl(str(yaml_file))
    assert repl.yaml_file == yaml_file.absolute()
    assert len(repl.models) == 1
    assert len(repl.experiments) == 1
    assert repl.running


def test_repl_initialization_nonexistent_file():
    """Test REPL raises error for nonexistent file."""
    with pytest.raises(FileNotFoundError):
        QsynthRepl("nonexistent.yaml")


def test_repl_cmd_help(capsys):
    """Test help command."""
    yaml_content = """
models:
  - name: testmodel
    locales: ['en-US']
    schemas: []

experiments: {}
"""
    yaml_file = Path(__file__).parent.parent.parent / "models.yaml"
    if not yaml_file.exists():
        pytest.skip("models.yaml not found")
    
    repl = QsynthRepl(str(yaml_file))
    console = MagicMock()
    
    repl._cmd_help(console)
    
    # Verify console.print was called with help text
    assert console.print.call_count > 0


def test_repl_cmd_models(capsys):
    """Test models command."""
    yaml_file = Path(__file__).parent.parent.parent / "models.yaml"
    if not yaml_file.exists():
        pytest.skip("models.yaml not found")
    
    repl = QsynthRepl(str(yaml_file))
    console = MagicMock()
    
    repl._cmd_models(console, [])
    
    assert console.print.call_count > 0


def test_repl_cmd_experiments(capsys):
    """Test experiments command."""
    yaml_file = Path(__file__).parent.parent.parent / "models.yaml"
    if not yaml_file.exists():
        pytest.skip("models.yaml not found")
    
    repl = QsynthRepl(str(yaml_file))
    console = MagicMock()
    
    repl._cmd_experiments(console)
    
    assert console.print.call_count > 0


def test_repl_execute_help(capsys):
    """Test help command execution."""
    yaml_file = Path(__file__).parent.parent.parent / "models.yaml"
    if not yaml_file.exists():
        pytest.skip("models.yaml not found")
    
    repl = QsynthRepl(str(yaml_file))
    console = MagicMock()
    
    repl._execute_command(console, "help", [])
    
    assert console.print.call_count > 0


def test_repl_execute_unknown_command(capsys):
    """Test unknown command handling."""
    yaml_file = Path(__file__).parent.parent.parent / "models.yaml"
    if not yaml_file.exists():
        pytest.skip("models.yaml not found")
    
    repl = QsynthRepl(str(yaml_file))
    console = MagicMock()
    
    repl._execute_command(console, "unknown_command", [])
    
    # Should print error message
    assert console.print.call_count > 0


def test_repl_execute_exit(capsys):
    """Test exit command."""
    yaml_file = Path(__file__).parent.parent.parent / "models.yaml"
    if not yaml_file.exists():
        pytest.skip("models.yaml not found")
    
    repl = QsynthRepl(str(yaml_file))
    assert repl.running
    
    console = MagicMock()
    repl._execute_command(console, "exit", [])
    
    assert not repl.running
    assert console.print.call_count > 0


def test_repl_cmd_list(capsys):
    """Test list command."""
    yaml_file = Path(__file__).parent.parent.parent / "models.yaml"
    if not yaml_file.exists():
        pytest.skip("models.yaml not found")
    
    repl = QsynthRepl(str(yaml_file))
    console = MagicMock()
    
    repl._cmd_list(console)
    
    # list_schema_content will be called which prints
    assert True  # If we got here without error, test passes


def test_repl_execute_list_aliases(capsys):
    """Test list command aliases (list and ls)."""
    yaml_file = Path(__file__).parent.parent.parent / "models.yaml"
    if not yaml_file.exists():
        pytest.skip("models.yaml not found")
    
    repl = QsynthRepl(str(yaml_file))
    console = MagicMock()
    
    # Test both aliases
    repl._execute_command(console, "list", [])
    repl._execute_command(console, "ls", [])
    
    # Should work without errors
    assert True

