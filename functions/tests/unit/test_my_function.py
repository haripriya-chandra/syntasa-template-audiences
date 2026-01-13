import pytest
from unittest.mock import patch, MagicMock


# ----------------------------
# Fixtures
# ----------------------------
@pytest.fixture
def mock_config():
    mock = MagicMock()
    mock.gcp.project_id = "syntasa-saas"
    mock.gcp.dataset_id = "ccdp_demo"
    mock.gcp.table_name = "web_tb_event"
    mock.gcp.bucket_name = "syntasa-saas"
    mock.gcp.schema_blob_name = "donorai_attr_aud/context_dictionary.json"
    mock.gcp.col_values_blob_name = "donorai_attr_aud/distinct_col_values.json"
    return mock


@pytest.fixture
def sample_schema():
    return {
        "columns": [
            {"name": "age", "data_type": "INTEGER", "description": "User age"},
            {"name": "country", "data_type": "STRING", "description": "User country"},
        ]
    }


@pytest.fixture
def sample_col_values():
    return {"age": [20, 25, 30, 35], "country": ["US", "IN"]}


@pytest.fixture
def sample_gemini_response():
    return """
    {
        "filter_clause": "age > 25",
        "columns_used": ["age"],
        "attribute_name": "Older users",
        "attribute_description": "Users older than 25"
    }
    """


# ----------------------------
# Happy path
# ----------------------------
@patch(
    "my_function.audiences_app.audiences_agent.agent.load_context_from_gcs", create=True
)
@patch("my_function.audiences_app.audiences_agent.agent.generate", create=True)
def test_run_audience_agent_success(
    mock_generate,
    mock_load_context,
    mock_config,
    sample_schema,
    sample_col_values,
    sample_gemini_response,
):
    # Mock GCS loads
    mock_load_context.side_effect = [sample_schema, sample_col_values]
    mock_generate.return_value = sample_gemini_response

    # Mock BQ client
    mock_client = MagicMock()
    mock_query_job = MagicMock()
    mock_query_job.result.return_value = [{"matching_users": 42}]
    mock_client.query.return_value = mock_query_job

    from my_function.audiences_app.audiences_agent.agent import run_audience_agent

    result = run_audience_agent(
        "Find users older than 25", config=mock_config, client=mock_client
    )

    assert result["filter_clause"] == "age > 25"
    assert result["columns_used"] == ["age"]
    assert result["attribute_name"] == "Older users"
    assert result["attribute_description"] == "Users older than 25"
    assert result["matching_users"] == 42


# ----------------------------
# Invalid Gemini JSON
# ----------------------------
@patch(
    "my_function.audiences_app.audiences_agent.agent.load_context_from_gcs", create=True
)
@patch("my_function.audiences_app.audiences_agent.agent.generate", create=True)
def test_run_audience_agent_invalid_gemini_response(
    mock_generate, mock_load_context, mock_config, sample_schema, sample_col_values
):
    mock_load_context.side_effect = [sample_schema, sample_col_values]
    mock_generate.return_value = "NOT JSON"

    mock_client = MagicMock()

    from my_function.audiences_app.audiences_agent.agent import run_audience_agent

    result = run_audience_agent(
        "Invalid response test", config=mock_config, client=mock_client
    )

    assert result["filter_clause"] == ""
    assert result["columns_used"] == []
    assert result["attribute_name"] == ""
    assert result["attribute_description"] == ""
    assert result["matching_users"] is None


# ----------------------------
# BigQuery failure
# ----------------------------
@patch(
    "my_function.audiences_app.audiences_agent.agent.load_context_from_gcs", create=True
)
@patch("my_function.audiences_app.audiences_agent.agent.generate", create=True)
def test_run_audience_agent_bigquery_error(
    mock_generate,
    mock_load_context,
    mock_config,
    sample_schema,
    sample_col_values,
    sample_gemini_response,
):
    mock_load_context.side_effect = [sample_schema, sample_col_values]
    mock_generate.return_value = sample_gemini_response

    mock_client = MagicMock()
    mock_client.query.side_effect = Exception("BigQuery error")

    from my_function.audiences_app.audiences_agent.agent import run_audience_agent

    result = run_audience_agent("BQ error test", config=mock_config, client=mock_client)

    assert result["filter_clause"] == "age > 25"
    assert result["matching_users"] is None
