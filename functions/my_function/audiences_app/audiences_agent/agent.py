import json
import pandas as pd
import re
from google.cloud import storage  # type: ignore[attr-defined]
import yaml
import os
import sys
from .base_functions import generate, get_bq_client, get_config
from typing import Any, Dict
from typing import Optional

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)


# Load prompts
prompts_path = os.path.join(
    os.path.dirname(__file__), "prompts", "generate_audiences.yaml"
)
with open(prompts_path, "r", encoding="utf-8") as f:
    prompts = yaml.safe_load(f)
attribute_prompt_template = prompts["prompt"]

base_path = os.path.dirname(__file__)

# ----------------- Helper Functions -----------------
def load_context_from_gcs(bucket_name: str, blob_name: str) -> Dict[str, Any]:
    client = storage.Client()
    blob = client.bucket(bucket_name).blob(blob_name)
    content = blob.download_as_text()
    return json.loads(content)


def format_schema_from_column_list(context_json):
    formatted = []
    for col in context_json.get("columns", []):
        name = col.get("name", "")
        dtype = col.get("data_type", "").upper()
        desc = col.get("description", "").strip()
        if desc:
            formatted.append(f"- {name} ({dtype}): {desc}")
        else:
            formatted.append(f"- {name} ({dtype})")
    return "\n".join(formatted)


def fetch_data_as_strings(client, project_id, dataset_id, table_name, columns, limit=5):
    cols_sql = ", ".join(f"`{c}`" for c in columns)
    query = (
        f"SELECT {cols_sql} FROM `{project_id}.{dataset_id}.{table_name}` LIMIT {limit}"
    )
    rows = client.query(query).result()
    records = [dict(row.items()) for row in rows]
    df = pd.DataFrame(records)
    return df.astype(str)


def clean_gemini_json_response(response_text):
    if response_text.strip().startswith("```json"):
        cleaned = re.sub(r"^```json\s*", "", response_text.strip())
        cleaned = re.sub(r"\s*```$", "", cleaned)
        return cleaned.strip()
    return response_text.strip()


# ----------------- Main Agent Function -----------------
def run_audience_agent(attribute_goal: str, config=None, client=None):
    config = get_config(config)
    client = client or get_bq_client()

    """
    Input: attribute goal string
    Output: dict with keys: filter_clause, columns_used, matching_users
    """
    # Load context (schema) from GCS
    context_json = load_context_from_gcs(
        bucket_name=config.gcp.bucket_name, blob_name=config.gcp.schema_blob_name
    )

    schema_str = format_schema_from_column_list(context_json)

    # Load column values
    col_values_json = load_context_from_gcs(
        bucket_name=config.gcp.bucket_name, blob_name=config.gcp.col_values_blob_name
    )

    col_values_str = json.dumps(col_values_json, indent=2, ensure_ascii=False)

    # Build prompt
    prompt = attribute_prompt_template.format(
        attribute_goal=attribute_goal,
        schema_str=schema_str,
        sample_json_str=col_values_str,
    )

    response_schema = prompts["response_schema"]

    # Generate Gemini response
    response = generate(prompt, response_schema)

    try:
        response = json.loads(response)
        filter_clause = response["filter_clause"]
        columns_used = response["columns_used"]
        attribute_name = response["attribute_name"]
        description = response["attribute_description"]
    except Exception as e:
        print("Error parsing Gemini response:", e)
        filter_clause = ""
        columns_used = []
        attribute_name = ""
        description = ""

    # Ensure id column exists
    id_col = "mcvisid"

    # Count matching users
    matching_users: Optional[int] = None

    if filter_clause:
        try:
            query = f"SELECT COUNT(DISTINCT {id_col}) as matching_users FROM `{config.gcp.project_id}.{config.gcp.dataset_id}.{config.gcp.table_name}` WHERE {filter_clause}"
            rows = client.query(query).result()
            matching_users = int(next(iter(rows))["matching_users"])
        except Exception as e:
            print("Error executing count query:", e)
            matching_users = None

    return {
        "filter_clause": filter_clause,
        "columns_used": columns_used,
        "attribute_name": attribute_name,
        "attribute_description": description,
        "matching_users": matching_users,
    }


# validate model's query against ground truth for benchmark testing
def validate_query(nl_query, filter_clause, ground_truth_clause, config=None):
    config = get_config(config)
    client = get_bq_client()
    context_json = load_context_from_gcs(
        bucket_name=config.gcp.bucket_name, blob_name=config.gcp.schema_blob_name
    )

    schema_str = format_schema_from_column_list(context_json)
    allowed_columns = [c["name"] for c in context_json.get("columns", [])]

    # Sample data for Gemini prompt
    preview_columns = allowed_columns[: min(8, len(allowed_columns))]
    sample_df = fetch_data_as_strings(
        client,
        config.gcp.project_id,
        config.gcp.dataset_id,
        config.gcp.table_name,
        preview_columns,
        limit=5,
    )
    sample_json_str = json.dumps(
        sample_df.to_dict(orient="records"), indent=2, ensure_ascii=False
    )
    prompt_path = os.path.join(base_path, "prompts", "ground_truth_validation.yaml")
    with open(prompt_path, "r") as f:
        query_template = yaml.safe_load(f)

    prompt = query_template["prompt"].format(
        nl_query=nl_query,
        filter_clause=filter_clause,
        ground_truth_clause=ground_truth_clause,
        schema_str=schema_str,
        sample_json_str=sample_json_str,
    )

    response_schema = query_template["response_schema"]
    result = generate(prompt, response_schema)
    return json.loads(result)
