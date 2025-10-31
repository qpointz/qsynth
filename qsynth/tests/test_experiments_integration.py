"""Integration tests for all experiment types."""
import yaml
from pathlib import Path
import pytest

from qsynth.models import Model
from qsynth.experiments import get_experiment_class
from qsynth.main import load


# Test output directory - use real directory structure
TEST_OUTPUT_BASE = Path(__file__).parent.parent.parent / ".test-data" / ".ut"


def create_minimal_model_yaml(output_dir: Path):
    """Create a minimal model YAML for testing."""
    return {
        'models': [
            {
                'name': 'testmodel',
                'locales': ['en-US'],
                'schemas': [
                    {
                        'name': 'testdata',
                        'rows': 10,
                        'attributes': [
                            {'name': 'id', 'type': 'random_int', 'params': {'min': 1, 'max': 100}},
                            {'name': 'name', 'type': 'first_name'},
                        ]
                    }
                ]
            }
        ]
    }


class TestCsvExperiment:
    def test_csv_experiment_runs(self, tmp_path):
        """Test CSV experiment executes and creates files."""
        output_dir = TEST_OUTPUT_BASE / "experiments" / "csv"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        yaml_file = tmp_path / "test.yaml"
        config = create_minimal_model_yaml(output_dir)
        config['experiments'] = {
            'test_csv': {
                'type': 'csv',
                'path': str(output_dir / '{dataset-name}.csv'),
                'params': {'index': False}
            }
        }
        
        yaml_file.write_text(yaml.dump(config))
        
        experiments = load(str(yaml_file))
        experiments.run('test_csv')
        
        # Check file was created
        csv_file = output_dir / "testdata.csv"
        assert csv_file.exists()


class TestParquetExperiment:
    def test_parquet_experiment_runs(self, tmp_path):
        """Test Parquet experiment executes and creates files."""
        output_dir = TEST_OUTPUT_BASE / "experiments" / "parquet"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        yaml_file = tmp_path / "test.yaml"
        config = create_minimal_model_yaml(output_dir)
        config['experiments'] = {
            'test_parquet': {
                'type': 'parquet',
                'path': str(output_dir / '{dataset-name}.parquet'),
            }
        }
        
        yaml_file.write_text(yaml.dump(config))
        
        experiments = load(str(yaml_file))
        experiments.run('test_parquet')
        
        # Check file was created
        parquet_file = output_dir / "testdata.parquet"
        assert parquet_file.exists()


class TestAvroExperiment:
    def test_avro_experiment_runs(self, tmp_path):
        """Test Avro experiment executes and creates files."""
        output_dir = TEST_OUTPUT_BASE / "experiments" / "avro"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        yaml_file = tmp_path / "test.yaml"
        config = create_minimal_model_yaml(output_dir)
        config['experiments'] = {
            'test_avro': {
                'type': 'avro',
                'path': str(output_dir / '{dataset-name}.avro'),
            }
        }
        
        yaml_file.write_text(yaml.dump(config))
        
        experiments = load(str(yaml_file))
        experiments.run('test_avro')
        
        # Check file was created
        avro_file = output_dir / "testdata.avro"
        assert avro_file.exists()


class TestSqlExperiment:
    def test_sql_experiment_runs(self, tmp_path):
        """Test SQL experiment executes and creates files."""
        output_dir = TEST_OUTPUT_BASE / "experiments" / "sql"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        yaml_file = tmp_path / "test.yaml"
        config = create_minimal_model_yaml(output_dir)
        config['experiments'] = {
            'test_sql': {
                'type': 'sql',
                'path': str(output_dir / '{model-name}.sql'),
            }
        }
        
        yaml_file.write_text(yaml.dump(config))
        
        experiments = load(str(yaml_file))
        experiments.run('test_sql')
        
        # Check file was created
        sql_file = output_dir / "testmodel.sql"
        assert sql_file.exists()
        
        # Check content
        content = sql_file.read_text()
        assert "CREATE TABLE" in content.upper()


class TestErModelExperiment:
    def test_ermodel_experiment_runs(self, tmp_path):
        """Test ER Model experiment executes and creates files."""
        output_dir = TEST_OUTPUT_BASE / "experiments" / "ermodel"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        yaml_file = tmp_path / "test.yaml"
        config = create_minimal_model_yaml(output_dir)
        config['experiments'] = {
            'test_ermodel': {
                'type': 'ermodel',
                'path': str(output_dir / '{model-name}.puml'),
            }
        }
        
        yaml_file.write_text(yaml.dump(config))
        
        experiments = load(str(yaml_file))
        experiments.run('test_ermodel')
        
        # Check file was created
        puml_file = output_dir / "testmodel.puml"
        assert puml_file.exists()
        
        content = puml_file.read_text()
        assert "@startuml" in content


class TestMermaidExperiment:
    def test_mermaid_experiment_runs(self, tmp_path):
        """Test Mermaid experiment executes and creates files."""
        output_dir = TEST_OUTPUT_BASE / "experiments" / "mermaid"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        yaml_file = tmp_path / "test.yaml"
        config = create_minimal_model_yaml(output_dir)
        config['experiments'] = {
            'test_mermaid': {
                'type': 'mermaid',
                'path': str(output_dir / '{model-name}.mmd'),
            }
        }
        
        yaml_file.write_text(yaml.dump(config))
        
        experiments = load(str(yaml_file))
        experiments.run('test_mermaid')
        
        # Check file was created
        mmd_file = output_dir / "testmodel.mmd"
        assert mmd_file.exists()
        
        content = mmd_file.read_text()
        assert "erDiagram" in content


class TestMetaExperiment:
    def test_meta_experiment_runs(self, tmp_path):
        """Test Meta experiment executes and creates files."""
        output_dir = TEST_OUTPUT_BASE / "experiments" / "meta"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        yaml_file = tmp_path / "test.yaml"
        config = create_minimal_model_yaml(output_dir)
        config['experiments'] = {
            'test_meta': {
                'type': 'meta',
                'path': str(output_dir / '{model-name}-meta.yaml'),
            }
        }
        
        yaml_file.write_text(yaml.dump(config))
        
        experiments = load(str(yaml_file))
        experiments.run('test_meta')
        
        # Check file was created
        meta_file = output_dir / "testmodel-meta.yaml"
        assert meta_file.exists()
        
        content = meta_file.read_text()
        assert "schemas" in content


class TestLLMPromptExperiment:
    def test_llm_prompt_experiment_runs(self, tmp_path):
        """Test LLM Prompt experiment executes and creates files."""
        output_dir = TEST_OUTPUT_BASE / "experiments" / "llm_prompt"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        yaml_file = tmp_path / "test.yaml"
        config = create_minimal_model_yaml(output_dir)
        config['experiments'] = {
            'test_llm_prompt': {
                'type': 'llm-prompt',
                'path': str(output_dir / '{model-name}.prompt'),
                'params': {
                    'prologue': 'Test prologue',
                    'epilogue': 'Test epilogue'
                }
            }
        }
        
        yaml_file.write_text(yaml.dump(config))
        
        experiments = load(str(yaml_file))
        experiments.run('test_llm_prompt')
        
        # Check file was created
        prompt_file = output_dir / "testmodel.prompt"
        assert prompt_file.exists()
        
        content = prompt_file.read_text()
        assert "Test prologue" in content
        assert "Test epilogue" in content
        assert "Tables:" in content


class TestCronFeedExperiment:
    def test_cron_feed_experiment_runs(self, tmp_path):
        """Test Cron Feed experiment executes and creates files."""
        output_dir = TEST_OUTPUT_BASE / "experiments" / "cron_feed"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        yaml_file = tmp_path / "test.yaml"
        config = create_minimal_model_yaml(output_dir)
        config['experiments'] = {
            'test_cron_feed': {
                'type': 'cron_feed',
                'cron': '0 12 * * *',
                'dates': {
                    'from': '2023-01-01',
                    'to': '2023-01-03',
                    'count': 2
                },
                'path': str(output_dir / '{dataset-name}-{cron-date:%Y-%m-%d}.csv'),
                'writer': {
                    'name': 'csv',
                    'params': {'index': False}
                }
            }
        }
        
        yaml_file.write_text(yaml.dump(config))
        
        experiments = load(str(yaml_file))
        experiments.run('test_cron_feed')
        
        # Check files were created for dates
        files = list(output_dir.glob("*.csv"))
        assert len(files) > 0
        assert any("2023-01" in str(f) for f in files)


class TestExperimentRegistry:
    def test_all_experiment_types_registered(self):
        """Test all experiment types can be retrieved from registry."""
        types = ['csv', 'parquet', 'avro', 'sql', 'ermodel', 'mermaid', 'llm-prompt', 'meta', 'cron_feed']
        
        for exp_type in types:
            exp_class = get_experiment_class(exp_type)
            assert exp_class is not None
            assert hasattr(exp_class, 'run')
    
    def test_plantuml_alias_works(self):
        """Test that 'plantuml' is an alias for 'ermodel'."""
        exp_class = get_experiment_class('plantuml')
        assert exp_class is not None

