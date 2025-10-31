import csv
from pathlib import Path

import pandas as pd

from qsynth.main import load


def test_csv_experiment_writes_files(tmp_path):
    y = (
        "experiments:\n"
        "  write_csv:\n"
        "    type: csv\n"
        "    path: \"{dataset-name}.csv\"\n"
        "    params:\n"
        "      sep: ';'\n"
        "      header: true\n"
        "      index: false\n"
        "models:\n"
        "  - name: m\n"
        "    locales: ['en-US']\n"
        "    schemas:\n"
        "      - name: ds\n"
        "        rows: 3\n"
        "        attributes:\n"
        "          - name: id\n"
        "            type: random_int\n"
        "            params: {min: 1, max: 9}\n"
        "          - name: first\n"
        "            type: first_name\n"
    )

    yaml_path = tmp_path / 'exp.yaml'
    yaml_path.write_text(y)

    exps = load(str(yaml_path))
    exps.run('write_csv')

    out = tmp_path / 'ds.csv'
    # Files are written relative to YAML file dir
    # Ensure file exists and has content
    assert out.exists()
    rows = list(csv.reader(out.read_text().splitlines(), delimiter=';'))
    # Header + 3 rows
    assert len(rows) == 4
    assert rows[0] == ['id', 'first']

