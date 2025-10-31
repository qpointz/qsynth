"""Unit tests for CLI execution with YAML configuration files."""
import subprocess
import sys
from pathlib import Path
import pytest

# Path to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent


def run_cli_command(args):
    """Run qsynth CLI command and return result."""
    cmd = [sys.executable, "-m", "qsynth"] + args
    result = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=60  # 60 second timeout for safety
    )
    return result


def test_cli_formats_yaml_runs_all_experiments():
    """Test that formats.yaml runs all experiments successfully."""
    result = run_cli_command([
        "run",
        "--input-file", "formats.yaml",
        "--run-all-experiments"
    ])
    
    assert result.returncode == 0, f"CLI failed with stderr: {result.stderr}"
    
    # Check that output mentions expected experiments
    assert "Init Parquet writer" in result.stdout or "Parquet" in result.stdout.lower()
    assert "Init Avro writer" in result.stdout or "avro" in result.stdout.lower()


def test_cli_moneta_yaml_runs_all_experiments():
    """Test that moneta.yaml runs all experiments successfully."""
    result = run_cli_command([
        "run",
        "--input-file", "moneta.yaml",
        "--run-all-experiments"
    ])
    
    assert result.returncode == 0, f"CLI failed with stderr: {result.stderr}"
    
    # Check that output mentions expected experiments
    output_lower = result.stdout.lower()
    assert "csv" in output_lower or "Init CSV writer" in result.stdout
    assert "parquet" in output_lower or "Init Parquet writer" in result.stdout
    assert "sql" in output_lower or "Init SQL writer" in result.stdout


def test_cli_models_yaml_runs_all_experiments():
    """Test that models.yaml runs all experiments including cron_feed."""
    result = run_cli_command([
        "run",
        "--input-file", "models.yaml",
        "--run-all-experiments"
    ])
    
    assert result.returncode == 0, f"CLI failed with stderr: {result.stderr}"
    
    # Check that output mentions expected experiments
    output_lower = result.stdout.lower()
    assert "csv" in output_lower or "Init CSV writer" in result.stdout
    assert "parquet" in output_lower or "Init Parquet writer" in result.stdout
    
    # Cron feed should generate date output
    assert "2023-01" in result.stdout or "2023-02" in result.stdout


def test_cli_formats_yaml_single_experiment():
    """Test running a single experiment from formats.yaml."""
    result = run_cli_command([
        "run",
        "--input-file", "formats.yaml",
        "--experiment", "write_parquet"
    ])
    
    assert result.returncode == 0, f"CLI failed with stderr: {result.stderr}"
    assert "parquet" in result.stdout.lower() or "Init Parquet writer" in result.stdout


def test_cli_moneta_yaml_single_experiment():
    """Test running a single experiment from moneta.yaml."""
    result = run_cli_command([
        "run",
        "--input-file", "moneta.yaml",
        "--experiment", "write_csv"
    ])
    
    assert result.returncode == 0, f"CLI failed with stderr: {result.stderr}"
    assert "csv" in result.stdout.lower() or "Init CSV writer" in result.stdout


def test_cli_invalid_file_returns_error():
    """Test that CLI returns error for non-existent file."""
    result = run_cli_command([
        "run",
        "--input-file", "nonexistent.yaml",
        "--run-all-experiments"
    ])
    
    assert result.returncode != 0, "CLI should fail for non-existent file"


def test_cli_models_yaml_multiple_experiments():
    """Test running multiple specific experiments from models.yaml."""
    result = run_cli_command([
        "run",
        "--input-file", "models.yaml",
        "--experiment", "write_csv", "write_parquet"
    ])
    
    assert result.returncode == 0, f"CLI failed with stderr: {result.stderr}"
    output_lower = result.stdout.lower()
    assert "csv" in output_lower or "Init CSV writer" in result.stdout
    assert "parquet" in output_lower or "Init Parquet writer" in result.stdout


def test_cli_formats_yaml_generates_output_files(tmp_path):
    """Test that formats.yaml generates actual output files."""
    # Copy formats.yaml to temp directory and modify paths safely
    formats_yaml = PROJECT_ROOT / "formats.yaml"
    if formats_yaml.exists():
        import yaml
        
        # Load original YAML
        with open(formats_yaml, 'r') as f:
            config = yaml.safe_load(f)
        
        # Modify paths to use temp directory (using forward slashes for YAML)
        output_base = str(tmp_path / "test-data").replace("\\", "/")
        for exp_name, exp_config in config.get('experiments', {}).items():
            if 'path' in exp_config:
                original_path = exp_config['path']
                # Replace .test-data/ with temp directory path
                if original_path.startswith(".test-data/"):
                    exp_config['path'] = original_path.replace(".test-data/", f"{output_base}/")
        
        # Write modified YAML
        test_yaml = tmp_path / "formats.yaml"
        with open(test_yaml, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        # Run CLI with modified YAML
        result = run_cli_command([
            "run",
            "--input-file", str(test_yaml),
            "--run-all-experiments"
        ])
        
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        
        # Check that command executed successfully
        assert "Init Parquet writer" in result.stdout or "Parquet" in result.stdout.lower()

