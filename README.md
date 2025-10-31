# Qsynth

**Qsynth** is a synthetic data generation tool that creates realistic, relational datasets from declarative YAML models. It generates data in multiple formats (CSV, Parquet, Avro, SQL) and produces documentation artifacts like ER diagrams, metadata descriptors, and LLM prompts.

## Table of Contents

- [Overview](#overview)
  - [Key Features](#key-features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [CLI Usage](#cli-usage)
  - [List Available Faker Providers](#list-available-faker-providers)
  - [Show Type Information](#show-type-information)
  - [Show Schema Information](#show-schema-information)
  - [Run Experiments](#run-experiments)
  - [Interactive REPL Shell](#interactive-repl-shell)
  - [Using Docker](#using-docker)
- [Model File Format](#model-file-format)
  - [Basic Structure](#basic-structure)
  - [Model Definition](#model-definition)
  - [Schema (Table/Dataset)](#schema-tabledataset)
  - [Attributes (Columns)](#attributes-columns)
  - [Row Count Specifications](#row-count-specifications)
- [Experiments](#experiments)
  - [CSV Experiment](#csv-experiment)
  - [Parquet Experiment](#parquet-experiment)
  - [Avro Experiment](#avro-experiment)
  - [SQL Experiment](#sql-experiment)
  - [ER Model Experiment](#er-model-experiment)
  - [Mermaid Experiment](#mermaid-experiment)
  - [Metadata Descriptor](#metadata-descriptor)
  - [LLM Prompt](#llm-prompt)
  - [Cron Feed Experiment](#cron-feed-experiment)
- [Examples](#examples)
- [Project Structure](#project-structure)
- [Development](#development)
  - [Running Tests](#running-tests)
  - [Adding Custom Experiments](#adding-custom-experiments)
  - [Adding Custom Writers](#adding-custom-writers)

## Overview

Qsynth solves the problem of creating realistic test data with proper relational integrity. Instead of manually crafting CSV files or SQL inserts, you define your data model in YAML and Qsynth generates:

- **Synthetic datasets** with realistic-looking values (names, addresses, emails, etc.)
- **Referential integrity** between related entities using `${ref}` references
- **Multiple output formats** for different use cases (analytics, databases, documentation)
- **Time-based feeds** using cron schedules for simulating historical data streams

### Key Features

- 🎲 **Rich Data Types**: Built on [Faker](https://github.com/joke2k/faker) with extensions for financial, aviation, vehicle data
- 🔗 **Relationship Modeling**: Define foreign keys and cardinalities declaratively
- 📊 **Multiple Outputs**: CSV, Parquet, Avro, SQL DDL, ER diagrams, metadata YAML, LLM prompts
- ⏰ **Cron Schedules**: Generate time-series data with configurable date ranges
- 🔧 **Extensible**: Easy to add new experiment types and writer formats
- ✅ **Type-Safe**: Pydantic validation ensures your models are well-formed

## Installation

```bash
pip install -e .
```

Or using Docker:

```bash
docker build -t qsynth .
```

## Quick Start

1. **Define your model** in a YAML file:

```yaml
models:
  - name: ecommerce
    locales: ['en-US']
    schemas:
      - name: customers
        rows: 100
        attributes:
          - name: customer_id
            type: random_int
            params:
              min: 1000
              max: 9999
          - name: email
            type: email
          - name: first_name
            type: first_name
      
      - name: orders
        rows: 200
        attributes:
          - name: order_id
            type: random_int
          - name: customer_id
            type: ${ref}
            params:
              dataset: customers
              attribute: customer_id
              cord: 1-*  # one-to-many
          - name: total
            type: random_double
```

2. **Configure experiments** for output formats:

```yaml
experiments:
  write_csv:
    type: csv
    path: "./data/{model-name}/csv/{dataset-name}.csv"
    params:
      sep: ";"
      header: true
      index: false
```

3. **Run the generation**:

```bash
python -m qsynth run --input-file model.yaml --run-all-experiments
```

## CLI Usage

Qsynth provides a simple command-line interface:

### List Available Faker Providers

```bash
python -m qsynth types --all
```

Search for specific providers:

```bash
python -m qsynth types --find random
```

### Show Type Information

Get detailed information about a specific type, including its parameters:

```bash
python -m qsynth show-type first_name
```

For types with parameters:

```bash
python -m qsynth show-type random_int
```

For the special reference type:

```bash
python -m qsynth show-type '${ref}'
```

This command displays:
- **Parameters**: Required and optional parameters with default values
- **Sample Output**: An example of generated data
- **Documentation**: Usage instructions and examples

### Show Schema Information

Explore and display schema information from YAML model files. The `schema` command has three modes:

#### List Overview (Default)

When no filters are specified, it lists all models, schemas, and experiments:

```bash
python -m qsynth schema model.yaml
```

This shows:
- All experiments with their types
- All models with schema counts
- All schemas with row counts

#### Detailed Schema Information

Filter by a specific model:

```bash
python -m qsynth schema model.yaml --model moneta
```

Filter by a specific schema within a model:

```bash
python -m qsynth schema model.yaml --model moneta --schema clients
```

This command displays:
- **Model Overview**: Model name, locales, and schema count in a formatted panel
- **Schema Details**: Each schema with its row count and description
- **Attribute Tables**: All attributes with their types, parameters, and descriptions
- **Rich Formatting**: Color-coded, easy-to-read output using the `rich` library

The output shows:
- Reference attributes (`${ref}`) with their target relationships
- Parameters for numeric types (min/max ranges)
- Random element choices
- All other configuration details

#### Describe Experiments

Show detailed experiment configurations:

```bash
python -m qsynth schema model.yaml --experiments
```

This displays:
- Experiment types and output paths
- All parameters and configuration options
- Special settings for different experiment types (e.g., cron schedules for `cron_feed`)

### Run Experiments

Run all experiments defined in a YAML file:

```bash
python -m qsynth run --input-file model.yaml --run-all-experiments
```

Or run specific experiments:

```bash
python -m qsynth run --input-file model.yaml --experiment write_csv write_parquet
```

### Interactive REPL Shell

Qsynth includes an interactive REPL shell for exploring and working with your models:

```bash
python -m qsynth shell model.yaml
```

This launches an interactive shell where you can:

**Information Commands:**
- `help` - Show available commands
- `list` or `ls` - List all models, schemas, and experiments
- `models` - Show all models
- `schemas [model_name]` - Show schemas (optionally filtered by model)
- `experiments` or `exps` - Show all experiments
- `describe model <name>` - Describe a specific model
- `describe schema <name>` - Describe a specific schema
- `describe experiments` - Show detailed experiment configurations

**Operation Commands:**
- `run` - Run all experiments
- `run <experiment1> <experiment2>` - Run specific experiments
- `types --all` - List all Faker provider types
- `types --find <pattern>` - Search for types matching a pattern
- `info <type>` - Show detailed information about a Faker type

**Utility Commands:**
- `clear` - Clear the screen
- `exit` or `quit` - Exit the shell

**Example Session:**

```bash
qsynth> list
# Shows overview of all models, schemas, and experiments

qsynth> models
# Lists all models with their schemas

qsynth> schemas moneta
# Shows schemas in the 'moneta' model

qsynth> describe model moneta
# Detailed view of the moneta model

qsynth> run write_csv
# Run the write_csv experiment

qsynth> info random_int
# Show details about the random_int type

qsynth> exit
# Goodbye!
```

The REPL shell provides a convenient way to explore your data models and run experiments interactively without typing the full command-line each time.

### Using Docker

```bash
docker run -v "$(pwd):/data" qsynth run --input-file /data/model.yaml --run-all-experiments
```

## Model File Format

### Basic Structure

Every Qsynth configuration file has two main sections:

```yaml
experiments:
  # Output format configurations

models:
  # Data model definitions
```

### Model Definition

A **model** is a collection of related **schemas** (tables/datasets):

```yaml
- name: mymodel          # Model name
  locales: ['en-US']     # Locale for generating data
  schemas:               # List of schemas
    - name: dataset1
      rows: 100          # Number of rows
      attributes: [...]  # Columns
```

### Schema (Table/Dataset)

A **schema** defines a single dataset with its columns:

```yaml
- name: customers
  rows: 100              # Exact count OR {min: 10, max: 100}
  description: Customer master data
  attributes:
    - name: id
      type: random_int
      params:
        min: 1
        max: 1000
      description: Primary key
```

### Attributes (Columns)

Each attribute specifies:
- **name**: Column name
- **type**: Faker provider method or `${ref}` for foreign keys
- **params**: Parameters for the generator
- **description**: Optional documentation

#### Built-in Faker Types

Common types from Faker:

- `random_int` - Random integer (params: `min`, `max`)
- `random_double` - Random float (params: `min`, `max`)
- `random_element` - Random choice (params: `elements` list)
- `first_name`, `last_name`, `name` - Person names
- `email`, `phone_number` - Contact info
- `address`, `city`, `country` - Location data
- `date_this_year`, `date_this_decade` - Dates
- `sentence`, `text` - Text content
- `job`, `company` - Business data

And many more (see `python -m qsynth types --all`)

#### Reference Types (`${ref}`)

Reference to another dataset's column:

```yaml
- name: customer_id
  type: ${ref}
  params:
    dataset: customers      # Target dataset name
    attribute: customer_id  # Target column
    cord: 1-*              # Cardinality (optional, default: "1-*")
```

Cardinality options:
- `1-*`: One-to-many (each parent can have multiple children)
- `*-*`: Many-to-many
- `1-1`: One-to-one

### Row Count Specifications

Exact count:
```yaml
rows: 100
```

Range:
```yaml
rows:
  min: 10
  max: 100
```

## Experiments

Experiments define **what to generate** and **where to write it**. Each experiment has a `type` and configuration.

### CSV Experiment

Generate CSV files:

```yaml
write_csv:
  type: csv
  path: "./data/{dataset-name}.csv"
  params:
    sep: ";"
    header: true
    index: false
```

Path templates support:
- `{model-name}` - Model name
- `{dataset-name}` - Schema/dataset name

### Parquet Experiment

Generate Apache Parquet files (columnar format):

```yaml
write_parquet:
  type: parquet
  path: "./data/parquet/{model-name}/{dataset-name}.parquet"
```

### Avro Experiment

Generate Apache Avro files:

```yaml
write_avro:
  type: avro
  path: "./data/avro/{dataset-name}.avro"
```

### SQL Experiment

Generate SQL DDL and INSERT statements:

```yaml
write_sql:
  type: sql
  path: "./data/{model-name}.sql"
```

Outputs:
- `CREATE TABLE` statements with column definitions
- `INSERT` statements with all rows

### ER Model Experiment

Generate PlantUML ER diagram:

```yaml
write_model:
  type: ermodel  # or 'plantuml'
  path: "./data/{model-name}.puml"
```

### Mermaid Experiment

Generate Mermaid ER diagram:

```yaml
write_mermaid:
  type: mermaid
  path: "./data/{model-name}.mmd"
```

### Metadata Descriptor

Generate YAML metadata about tables and relationships:

```yaml
write_meta:
  type: meta
  path: "./data/{model-name}-meta.yaml"
```

### LLM Prompt

Generate prompt text for LLM SQL assistance:

```yaml
write_prompt:
  type: llm-prompt
  path: "./data/{model-name}.prompt"
  params:
    prologue: "You are a SQL assistant"
    rules:
      - "Use JOIN when needed"
      - "Quote identifiers with backticks"
    epilogue: "Always return JSON with query and confidence"
```

### Cron Feed Experiment

Generate time-series files based on a cron schedule:

```yaml
cron_feed:
  type: cron_feed
  cron: 0 18 * * MON-FRI        # Every weekday at 6 PM
  dates:
    from: '2023-01-01'
    to: '2023-12-31'
    count: 100                   # OR use 'count' instead of 'to'
  path: "./data/feed/{dataset-name}-{cron-date:%Y-%m-%d}.csv"
  writer:
    name: csv
    params:
      sep: ";"
      header: true
      index: false
```

This generates files for each occurrence of the cron pattern between dates.

## Using as a Library

Qsynth can be used programmatically in your Python applications:

```python
from qsynth import Model, Schema, Attribute, Experiments

# Define your data model
model = Model(
    name="products",
    locales="en-US",
    schemas=[
        Schema(
            name="items",
            rows=100,
            attributes=[
                Attribute(name="id", type="random_int", params={"min": 1, "max": 10000}),
                Attribute(name="name", type="company"),
                Attribute(name="price", type="random_double", params={"min": 10.0, "max": 1000.0}),
            ]
        )
    ]
)

# Configure output experiments
experiments_config = {
    'write_csv': {
        'type': 'csv',
        'path': './output/{dataset-name}.csv',
        'params': {'index': False}
    }
}

# Run generation
experiments = Experiments(experiments_config, [model])
experiments.run_all()
```

### Direct Data Generation

Generate DataFrames without writing to files:

```python
from qsynth import Model, Schema, Attribute, MultiModelsFaker

model = Model(
    name="test",
    locales="en-US",
    schemas=[
        Schema(
            name="users",
            rows=50,
            attributes=[
                Attribute(name="id", type="random_int"),
                Attribute(name="email", type="email"),
                Attribute(name="name", type="first_name"),
            ]
        )
    ]
)

# Generate data in memory
mmf = MultiModelsFaker([model])
mmf.generate_all()

# Access generated DataFrames
users_df = mmf.models["test"].generated["users"]
print(f"Generated {len(users_df)} users")
```

## Examples

See the included example files:

- `formats.yaml` - Basic CSV/Parquet/Avro generation
- `models.yaml` - Complex model with references and cron feed
- `moneta.yaml` - Financial services domain model

## Project Structure

```
qsynth/
├── qsynth/
│   ├── __init__.py
│   ├── main.py              # Core generation logic
│   ├── cli.py               # Command-line interface
│   ├── models.py            # Pydantic model definitions
│   ├── provider.py          # Custom Faker providers
│   ├── experiments/         # Experiment types
│   │   ├── csv_experiment.py
│   │   ├── parquet_experiment.py
│   │   ├── sql_experiment.py
│   │   └── ...
│   ├── writers/             # Output writers
│   │   ├── csv_writer.py
│   │   ├── parquet_writer.py
│   │   └── ...
│   └── tests/               # Test suite
└── models.yaml              # Example configuration
```

## Development

### Running Tests

```bash
pytest
```

Tests generate outputs in `.test-data/.ut/` directory.

### Adding Custom Experiments

1. Create a new file in `qsynth/experiments/`:

```python
from qsynth.experiments.write_experiment import WriteExperiment
from qsynth.experiments import register_experiment
from qsynth.writers.your_writer import YourWriter

@register_experiment('your-type')
class YourExperiment(WriteExperiment):
    def get_writer(self):
        return YourWriter()
```

2. Register the writer in `qsynth/writers/__init__.py`

### Adding Custom Writers

1. Create a file in `qsynth/writers/`:

```python
from qsynth.writers.base import Writer
from qsynth.writers import register_writer

@register_writer('your-format')
class YourWriter(Writer):
    def write(self, path, pd, model_name, schema_name, model, writeparams={}):
        # Your implementation
        pass
```

## License

[Your License Here]

## Contributing

Contributions welcome! Please ensure all tests pass before submitting.

```bash
pytest
```

## To run using docker 

```bash
docker run -v "$(pwd):/data" qsynth run --input-file formats.yaml --run-all-experiments
```
