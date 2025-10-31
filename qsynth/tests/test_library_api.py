"""Tests for programmatic qsynth library API."""
import pandas as pd
from pathlib import Path
import pytest
from tempfile import TemporaryDirectory

from qsynth import (
    Model,
    Schema,
    Attribute,
    MultiModelsFaker,
    Experiments,
    get_experiment_class,
    get_writer
)


class TestProgrammaticGeneration:
    """Test generating data programmatically without YAML."""
    
    def test_create_model_programmatically(self):
        """Test creating a model programmatically."""
        model = Model(
            name="test_model",
            locales="en-US",
            schemas=[
                Schema(
                    name="users",
                    rows=10,
                    attributes=[
                        Attribute(name="id", type="random_int", params={"min": 1, "max": 100}),
                        Attribute(name="name", type="first_name"),
                        Attribute(name="email", type="email"),
                    ]
                )
            ]
        )
        
        assert model.name == "test_model"
        assert len(model.schemas) == 1
        assert model.schemas[0].name == "users"
    
    def test_generate_data_programmatically(self):
        """Test generating data from programmatic model."""
        model = Model(
            name="test_model",
            locales="en-US",
            schemas=[
                Schema(
                    name="users",
                    rows=5,
                    attributes=[
                        Attribute(name="id", type="random_int"),
                        Attribute(name="name", type="first_name"),
                    ]
                )
            ]
        )
        
        mmf = MultiModelsFaker([model])
        mmf.generate_all()
        
        assert "test_model" in mmf.models
        assert "users" in mmf.models["test_model"].generated
        df = mmf.models["test_model"].generated["users"]
        assert len(df) == 5
        assert "id" in df.columns
        assert "name" in df.columns
    
    def test_generate_data_with_references(self):
        """Test generating data with foreign key references."""
        customers_model = Model(
            name="ecommerce",
            locales="en-US",
            schemas=[
                Schema(
                    name="customers",
                    rows=10,
                    attributes=[
                        Attribute(name="customer_id", type="random_int", params={"min": 1, "max": 100}),
                        Attribute(name="name", type="first_name"),
                    ]
                ),
                Schema(
                    name="orders",
                    rows=20,
                    attributes=[
                        Attribute(name="order_id", type="random_int"),
                        Attribute(
                            name="customer_id",
                            type="${ref}",
                            params={"dataset": "customers", "attribute": "customer_id"}
                        ),
                    ]
                )
            ]
        )
        
        mmf = MultiModelsFaker([customers_model])
        mmf.generate_all()
        
        cust_df = mmf.models["ecommerce"].generated["customers"]
        orders_df = mmf.models["ecommerce"].generated["orders"]
        
        # Verify referential integrity
        customer_ids = set(cust_df["customer_id"].tolist())
        order_customer_ids = set(orders_df["customer_id"].tolist())
        assert order_customer_ids.issubset(customer_ids)


class TestProgrammaticExperiments:
    """Test running experiments programmatically."""
    
    def test_run_csv_experiment_programmatically(self, tmp_path):
        """Test running CSV experiment without YAML file."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        # Create model programmatically
        model = Model(
            name="libtest",
            locales="en-US",
            schemas=[
                Schema(
                    name="data",
                    rows=5,
                    attributes=[
                        Attribute(name="id", type="random_int"),
                        Attribute(name="value", type="random_double", params={"min": 1.0, "max": 100.0}),
                    ]
                )
            ]
        )
        
        # Create experiment configuration
        experiment_config = {
            'type': 'csv',
            'path': str(output_dir / '{dataset-name}.csv'),
            'params': {'index': False}
        }
        
        # Get and run experiment
        exp_class = get_experiment_class('csv')
        experiment = exp_class(experiment_config, [model], relative_to=tmp_path)
        experiment.run()
        
        # Verify output
        output_file = output_dir / "data.csv"
        assert output_file.exists()
        df = pd.read_csv(output_file)
        assert len(df) == 5
        assert "id" in df.columns
    
    def test_run_parquet_experiment_programmatically(self, tmp_path):
        """Test running Parquet experiment without YAML file."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        model = Model(
            name="libtest",
            locales="en-US",
            schemas=[
                Schema(
                    name="data",
                    rows=3,
                    attributes=[
                        Attribute(name="id", type="random_int"),
                        Attribute(name="name", type="first_name"),
                    ]
                )
            ]
        )
        
        experiment_config = {
            'type': 'parquet',
            'path': str(output_dir / '{dataset-name}.parquet'),
        }
        
        exp_class = get_experiment_class('parquet')
        experiment = exp_class(experiment_config, [model], relative_to=tmp_path)
        experiment.run()
        
        output_file = output_dir / "data.parquet"
        assert output_file.exists()
        df = pd.read_parquet(output_file)
        assert len(df) == 3


class TestExperimentsClassProgrammatic:
    """Test using Experiments class programmatically."""
    
    def test_experiments_run_all_programmatically(self, tmp_path):
        """Test running multiple experiments programmatically."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        model = Model(
            name="mylib",
            locales="en-US",
            schemas=[
                Schema(
                    name="items",
                    rows=10,
                    attributes=[
                        Attribute(name="id", type="random_int"),
                        Attribute(name="name", type="first_name"),
                    ]
                )
            ]
        )
        
        # Define experiments programmatically
        experiments_config = {
            'write_csv': {
                'type': 'csv',
                'path': str(output_dir / 'csv' / '{dataset-name}.csv'),
                'params': {'index': False}
            },
            'write_sql': {
                'type': 'sql',
                'path': str(output_dir / '{model-name}.sql'),
            }
        }
        
        # Create Experiments instance
        experiments = Experiments(experiments_config, [model], relative_to=tmp_path)
        experiments.run_all()
        
        # Verify outputs
        csv_file = output_dir / "csv" / "items.csv"
        sql_file = output_dir / "mylib.sql"
        
        assert csv_file.exists()
        assert sql_file.exists()
    
    def test_experiments_run_single_programmatically(self, tmp_path):
        """Test running single experiment programmatically."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        model = Model(
            name="single",
            locales="en-US",
            schemas=[
                Schema(
                    name="test",
                    rows=7,
                    attributes=[
                        Attribute(name="id", type="random_int"),
                    ]
                )
            ]
        )
        
        experiments_config = {
            'csv_only': {
                'type': 'csv',
                'path': str(output_dir / '{dataset-name}.csv'),
            }
        }
        
        experiments = Experiments(experiments_config, [model], relative_to=tmp_path)
        experiments.run('csv_only')
        
        assert (output_dir / "test.csv").exists()


class TestWriterRegistryProgrammatic:
    """Test using writers programmatically."""
    
    def test_get_writer_instances(self):
        """Test getting writer instances from registry."""
        csv_writer = get_writer('csv')
        parquet_writer = get_writer('parquet')
        
        assert csv_writer is not None
        assert parquet_writer is not None
        assert csv_writer != parquet_writer

