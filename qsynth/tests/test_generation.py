import pandas as pd

from qsynth.main import MultiModelsFaker


def test_generate_two_schemas_and_reference():
    models = [
        {
            'name': 'm1',
            'locales': ['en-US'],
            'schemas': [
                {
                    'name': 'base',
                    'rows': 5,
                    'attributes': [
                        {'name': 'id', 'type': 'random_int', 'params': {'min': 1, 'max': 9}},
                        {'name': 'name', 'type': 'name'},
                    ],
                },
                {
                    'name': 'child',
                    'rows': 5,
                    'attributes': [
                        {'name': 'id', 'type': 'random_int', 'params': {'min': 1, 'max': 9}},
                        {'name': 'parent_id', 'type': '${ref}', 'params': {'dataset': 'base', 'attribute': 'id'}},
                    ],
                },
            ],
        }
    ]

    mmf = MultiModelsFaker(models)
    mmf.generate_all()

    model = mmf.models['m1']
    assert set(model.generated.keys()) == {'base', 'child'}

    base_df = model.generated['base']
    child_df = model.generated['child']

    assert isinstance(base_df, pd.DataFrame)
    assert isinstance(child_df, pd.DataFrame)
    assert set(base_df.columns) == {'id', 'name'}
    assert set(child_df.columns) == {'id', 'parent_id'}
    assert len(base_df) == 5
    assert len(child_df) == 5

    # Reference values should be chosen from base.id
    base_ids = set(base_df['id'].tolist())
    assert set(child_df['parent_id'].tolist()).issubset(base_ids)


def test_zero_rows_schema_generates_empty_dataframe():
    models = [
        {
            'name': 'm1',
            'locales': ['en-US'],
            'schemas': [
                {
                    'name': 'empty',
                    'rows': 0,
                    'attributes': [
                        {'name': 'id', 'type': 'random_int', 'params': {'min': 1, 'max': 9}},
                    ],
                },
            ],
        }
    ]

    mmf = MultiModelsFaker(models)
    mmf.generate_all()
    df = mmf.models['m1'].generated['empty']
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0


def test_model_without_schemas_defaults_to_empty():
    models = [
        {
            'name': 'm1',
            'locales': ['en-US'],
            # 'schemas' key intentionally omitted
        }
    ]

    mmf = MultiModelsFaker(models)
    mmf.generate_all()
    # No generated datasets expected
    assert mmf.models['m1'].generated == {}

