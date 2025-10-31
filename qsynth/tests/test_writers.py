"""Tests for all writer classes."""
import pandas as pd
from pathlib import Path
import pytest

from qsynth.models import Model, Schema, Attribute
from qsynth.main import MultiModelsFaker
from qsynth.writers import get_writer
from qsynth.writers.csv_writer import CsvWriter
from qsynth.writers.parquet_writer import ParquetWriter
from qsynth.writers.avro_writer import AvroWriter
from qsynth.writers.sql_writer import SqlWriter
from qsynth.writers.ermodel_writer import ErModelWriter
from qsynth.writers.mermaid_writer import ErMermaidModelWriter
from qsynth.writers.meta_writer import MetaDescriptorWriter
from qsynth.writers.llm_prompt_writer import LLMPromptWriter


# Test output directory - use real directory structure
TEST_OUTPUT_BASE = Path(__file__).parent.parent.parent / ".test-data" / ".ut"


def create_test_model():
    """Create a simple test model for writer tests."""
    return Model(
        name="test_model",
        locales="en-US",
        schemas=[
            Schema(
                name="users",
                rows=5,
                attributes=[
                    Attribute(name="id", type="random_int", params={"min": 1, "max": 100}),
                    Attribute(name="name", type="first_name"),
                    Attribute(name="email", type="email"),
                ]
            ),
            Schema(
                name="orders",
                rows=3,
                attributes=[
                    Attribute(name="order_id", type="random_int"),
                    Attribute(name="user_id", type="${ref}", params={"dataset": "users", "attribute": "id"}),
                    Attribute(name="amount", type="random_double", params={"min": 10.0, "max": 1000.0}),
                ]
            )
        ]
    )


def generate_test_data(model):
    """Generate test data from a model."""
    mmf = MultiModelsFaker([model])
    mmf.generate_all()
    return mmf.models[model.name]


@pytest.fixture
def test_output_dir():
    """Create test output directory in .test-data/.ut/writers."""
    output_dir = TEST_OUTPUT_BASE / "writers"
    output_dir.mkdir(parents=True, exist_ok=True)
    yield output_dir
    # Cleanup: remove test files after each test
    for file in output_dir.glob("*"):
        if file.is_file():
            file.unlink()


class TestCsvWriter:
    def test_csv_writer_creates_file(self, test_output_dir):
        """Test CSV writer creates output file."""
        model = create_test_model()
        model_faker = generate_test_data(model)
        
        writer = CsvWriter()
        output_path = test_output_dir / "users.csv"
        writer.init_writer(output_path)
        
        writer.write(
            output_path,
            model_faker.generated["users"],
            "test_model",
            "users",
            model_faker,
            {"index": False}
        )
        writer.finalize_writer()
        
        assert output_path.exists()
        content = output_path.read_text()
        assert "id" in content or "name" in content


class TestParquetWriter:
    def test_parquet_writer_creates_file(self, test_output_dir):
        """Test Parquet writer creates output file."""
        model = create_test_model()
        model_faker = generate_test_data(model)
        
        writer = ParquetWriter()
        output_path = test_output_dir / "users.parquet"
        writer.init_writer(output_path)
        
        writer.write(
            output_path,
            model_faker.generated["users"],
            "test_model",
            "users",
            model_faker
        )
        writer.finalize_writer()
        
        assert output_path.exists()
        # Verify it's readable as parquet
        df = pd.read_parquet(output_path)
        assert len(df) == 5
        assert "id" in df.columns


class TestAvroWriter:
    def test_avro_writer_creates_file(self, test_output_dir):
        """Test Avro writer creates output file."""
        model = create_test_model()
        model_faker = generate_test_data(model)
        
        writer = AvroWriter()
        output_path = test_output_dir / "users.avro"
        writer.init_writer(output_path)
        
        writer.write(
            output_path,
            model_faker.generated["users"],
            "test_model",
            "users",
            model_faker
        )
        writer.finalize_writer()
        
        assert output_path.exists()


class TestSqlWriter:
    def test_sql_writer_creates_file(self, test_output_dir):
        """Test SQL writer creates DDL and INSERT statements."""
        model = create_test_model()
        model_faker = generate_test_data(model)
        
        writer = SqlWriter()
        output_path = test_output_dir / "users.sql"
        writer.init_writer(output_path)
        
        writer.write(
            output_path,
            model_faker.generated["users"],
            "test_model",
            "users",
            model_faker
        )
        writer.finalize_writer()
        
        assert output_path.exists()
        content = output_path.read_text()
        assert "CREATE TABLE" in content.upper()
        assert "INSERT INTO" in content.upper()
        assert "users" in content


class TestErModelWriter:
    def test_ermodel_writer_creates_file(self, test_output_dir):
        """Test ER Model writer creates PlantUML file."""
        model = create_test_model()
        model_faker = generate_test_data(model)
        
        writer = ErModelWriter()
        output_path = test_output_dir / "model.puml"
        writer.init_writer(output_path)
        
        # Write both schemas
        writer.write(
            output_path,
            model_faker.generated["users"],
            "test_model",
            "users",
            model_faker
        )
        writer.write(
            output_path,
            model_faker.generated["orders"],
            "test_model",
            "orders",
            model_faker
        )
        writer.finalize_writer()
        
        assert output_path.exists()
        content = output_path.read_text()
        assert "@startuml" in content
        assert "entity" in content.lower()
        assert "users" in content or "Users" in content


class TestMermaidWriter:
    def test_mermaid_writer_creates_file(self, test_output_dir):
        """Test Mermaid writer creates diagram file."""
        model = create_test_model()
        model_faker = generate_test_data(model)
        
        writer = ErMermaidModelWriter()
        output_path = test_output_dir / "model.mmd"
        writer.init_writer(output_path)
        
        # Write both schemas
        writer.write(
            output_path,
            model_faker.generated["users"],
            "test_model",
            "users",
            model_faker
        )
        writer.write(
            output_path,
            model_faker.generated["orders"],
            "test_model",
            "orders",
            model_faker
        )
        writer.finalize_writer()
        
        assert output_path.exists()
        content = output_path.read_text()
        assert "erDiagram" in content
        assert "users" in content or "Users" in content


class TestMetaDescriptorWriter:
    def test_meta_writer_creates_yaml(self, test_output_dir):
        """Test Meta descriptor writer creates YAML file."""
        model = create_test_model()
        model_faker = generate_test_data(model)
        
        writer = MetaDescriptorWriter()
        output_path = test_output_dir / "meta.yaml"
        writer.init_writer(output_path)
        
        # Write both schemas
        writer.write(
            output_path,
            model_faker.generated["users"],
            "test_model",
            "users",
            model_faker
        )
        writer.write(
            output_path,
            model_faker.generated["orders"],
            "test_model",
            "orders",
            model_faker
        )
        writer.finalize_writer()
        
        assert output_path.exists()
        content = output_path.read_text()
        assert "schemas" in content
        assert "users" in content or "Users" in content


class TestLLMPromptWriter:
    def test_llm_prompt_writer_creates_file(self, test_output_dir):
        """Test LLM prompt writer creates prompt file."""
        model = create_test_model()
        model_faker = generate_test_data(model)
        
        writer = LLMPromptWriter()
        output_path = test_output_dir / "prompt.txt"
        writer.init_writer(output_path)
        
        # Write both schemas
        writer.write(
            output_path,
            model_faker.generated["users"],
            "test_model",
            "users",
            model_faker,
            {"prologue": "Test prologue", "epilogue": "Test epilogue"}
        )
        writer.write(
            output_path,
            model_faker.generated["orders"],
            "test_model",
            "orders",
            model_faker
        )
        writer.finalize_writer()
        
        assert output_path.exists()
        content = output_path.read_text()
        assert "Test prologue" in content
        assert "Test epilogue" in content
        assert "Tables:" in content
        assert "Relations:" in content


class TestWriterRegistry:
    def test_registry_get_csv_writer(self):
        """Test registry returns CSV writer."""
        writer = get_writer('csv')
        assert isinstance(writer, CsvWriter)
    
    def test_registry_get_parquet_writer(self):
        """Test registry returns Parquet writer."""
        writer = get_writer('parquet')
        assert isinstance(writer, ParquetWriter)
    
    def test_registry_get_avro_writer(self):
        """Test registry returns Avro writer."""
        writer = get_writer('avro')
        assert isinstance(writer, AvroWriter)
    
    def test_registry_get_sql_writer(self):
        """Test registry returns SQL writer."""
        writer = get_writer('sql')
        assert isinstance(writer, SqlWriter)
    
    def test_registry_raises_on_unknown(self):
        """Test registry raises error for unknown writer."""
        with pytest.raises(Exception, match="Unknown writer"):
            get_writer('unknown_type')

