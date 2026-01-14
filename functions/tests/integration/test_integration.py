"""
Integration tests for run_audience_agent.
Mocks:
- GCS schema + column values
- BigQuery count query
- Gemini generate
"""

import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from my_function.audiences_app.audiences_agent.agent import run_audience_agent


@pytest.mark.integration
@patch(
    "my_function.audiences_app.audiences_agent.agent.load_context_from_gcs"
)
@patch("my_function.audiences_app.audiences_agent.agent.generate")
def test_run_audience_agent_end_to_end(mock_generate, mock_load_context):
    """
    End-to-end test with mocked external dependencies.
    """

    # Mock schema and column values
    sample_schema = {
        "columns": [
            {"name": "age", "data_type": "INTEGER", "description": "User age"},
            {"name": "country", "data_type": "STRING", "description": "User country"},
        ]
    }
    sample_col_values = {"age": [20, 25, 30, 35], "country": ["US", "IN"]}
    mock_load_context.side_effect = [sample_schema, sample_col_values]

    # Mock Gemini response
    sample_gemini_response = """
    {
        "filter_clause": "age > 25",
        "columns_used": ["age"],
        "attribute_name": "Older users",
        "attribute_description": "Users older than 25"
    }
    """
    mock_generate.return_value = sample_gemini_response

    # Mock BigQuery client
    mock_bq_client = MagicMock()
    mock_query_job = MagicMock()
    mock_query_job.result.return_value = [{"matching_users": 42}]
    mock_bq_client.query.return_value = mock_query_job

    # Mock config with nested gcp object
    config = SimpleNamespace(
        gcp=SimpleNamespace(
            bucket_name="syntasa-saas",
            schema_blob_name="donorai_attr_aud/context_dictionary.json",
            col_values_blob_name="donorai_attr_aud/distinct_col_values.json",
        ),
        dataset_id="ccdp_demo",
        table_name="web_tb_event",
    )

    result = run_audience_agent(
        attribute_goal="Users older than 25 living in India",
        config=config,
        client=mock_bq_client,
    )

    assert result["filter_clause"] == "age > 25"
    assert result["columns_used"] == ["age"]
    assert result["attribute_name"] == "Older users"
    assert result["attribute_description"] == "Users older than 25"


@pytest.mark.integration
@patch(
    "my_function.audiences_app.audiences_agent.agent.load_context_from_gcs"
)
@patch("my_function.audiences_app.audiences_agent.agent.generate")
def test_run_audience_agent_with_simple_attribute(mock_generate, mock_load_context):
    """
    Simpler query to reduce Gemini variability.
    """

    sample_schema = {
        "columns": [
            {"name": "country", "data_type": "STRING", "description": "User country"}
        ]
    }
    sample_col_values = {"country": ["US", "IN"]}
    mock_load_context.side_effect = [sample_schema, sample_col_values]

    # Mock Gemini response
    mock_generate.return_value = """
    {
        "filter_clause": "country = 'US'",
        "columns_used": ["country"],
        "attribute_name": "US Users",
        "attribute_description": "Users from US"
    }
    """

    # Mock BigQuery client
    mock_bq_client = MagicMock()
    mock_query_job = MagicMock()
    mock_query_job.result.return_value = [{"matching_users": 10}]
    mock_bq_client.query.return_value = mock_query_job

    # Mock config with nested gcp object
    config = SimpleNamespace(
        gcp=SimpleNamespace(
            bucket_name="syntasa-saas",
            schema_blob_name="donorai_attr_aud/context_dictionary.json",
            col_values_blob_name="donorai_attr_aud/distinct_col_values.json",
        ),
        dataset_id="ccdp_demo",
        table_name="web_tb_event",
    )

    result = run_audience_agent(
        attribute_goal="Users from United States", config=config, client=mock_bq_client
    )

    assert result["filter_clause"] == "country = 'US'"
    assert result["columns_used"] == ["country"]
    assert result["attribute_name"] == "US Users"
    assert result["attribute_description"] == "Users from US"
