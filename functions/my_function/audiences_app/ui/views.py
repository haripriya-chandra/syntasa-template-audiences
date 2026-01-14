from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.utils.timezone import now
import pandas as pd
import json
from google.cloud import bigquery
import sys
import os
from my_function.config import FunctionConfig

# Load config from YAML
config = FunctionConfig.from_yaml("config.yaml")
# Add current directory to path to import your agent
sys.path.append(os.getcwd())
agent = __import__("audiences_agent.agent", fromlist=["*"])

# Initialize BigQuery client
client = bigquery.Client(project=config.gcp.project_id)

# Load your agent
audience_agent = agent.run_audience_agent


# Function to dry run SQL query in BQ
def run_sql_query(sql_query, max_bytes_gb=500):
    try:
        job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
        query_job = client.query(sql_query, job_config=job_config)
        bytes_processed = query_job.total_bytes_processed
        max_bytes = max_bytes_gb * (1024**3)
        if bytes_processed <= max_bytes:
            return client.query(sql_query).to_dataframe()
        else:
            return f"Query exceeds {max_bytes_gb} GB limit (processed: {bytes_processed} bytes)."
    except Exception as e:
        return f"There was a problem executing the generated SQL query. Error: {e}"


@ensure_csrf_cookie
def index(request):
    """Render homepage."""
    return render(request, "index.html", {"timestamp": now().timestamp()})


@csrf_exempt
def generate_audience(request):
    """Generate audience based on user input."""
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    try:
        data = json.loads(request.body)
        attribute_goal = data.get("attribute_goal", "")

        if not attribute_goal:
            return JsonResponse({"error": "Missing attribute goal"}, status=400)

        # Call your agent function
        result = audience_agent(
            attribute_goal
        )  # Should return dict with filter_clause, columns_used, matching_users

        return JsonResponse({"success": True, **result})

    except Exception as e:
        import logging

        logging.exception("submit_question failed")
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
def submit_feedback(request):
    """Store user feedback in BigQuery."""
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    try:
        data = json.loads(request.body)
        approved = data.get("feedback")  # thumbs_up / thumbs_down
        feedback_text = data.get("feedback_text", "")
        attribute_goal = data.get("attribute_goal", "")
        filter_clause = data.get("filter_clause", "")
        columns_used = data.get("columns_used", [])

        if not (attribute_goal and filter_clause):
            return JsonResponse({"error": "Missing required fields"}, status=400)

        # Prepare row for BigQuery
        feedback_df = pd.DataFrame(
            {
                "attribute_goal": [attribute_goal],
                "filter_clause": [filter_clause],
                "columns_used": [columns_used],
                "approved": [approved],
                "feedback_text": [feedback_text],
            }
        )

        feedback_table = config.gcp.feedback_table
        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
        client.load_table_from_dataframe(
            feedback_df, feedback_table, job_config=job_config
        ).result()

        return JsonResponse(
            {"success": True, "message": "Feedback recorded successfully"}
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
