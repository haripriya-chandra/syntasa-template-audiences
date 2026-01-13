import time
import vertexai
from vertexai.generative_models import (
    GenerationConfig,
    GenerativeModel,
    HarmCategory,
    HarmBlockThreshold,
    SafetySetting,
)
from google.cloud import bigquery
from google.auth import default
from google.auth.transport.requests import Request
from my_function.config import FunctionConfig
from typing import Any, Dict, Optional
from typing import cast


_bq_client = None
_vertex_initialized = False


def get_config(config=None):
    if config is not None:
        return config
    if config is None:
        config = FunctionConfig.from_yaml("config.yaml")
    return config


def init_vertex():
    global _vertex_initialized
    if not _vertex_initialized:
        config = get_config()
        vertexai.init(
            project=config.gcp.project_id,
            location="global",
        )
        _vertex_initialized = True


def get_bq_client():
    global _bq_client
    if _bq_client is None:
        config = get_config()
        _bq_client = bigquery.Client(project=config.gcp.project_id)
    return _bq_client


# Base function to generate response from Gemini
def generate(
    prompt: str,
    response_schema: Optional[Dict[str, Any]] = None,
) -> str:
    config = get_config()
    init_vertex()

    model = GenerativeModel(config.gcp.ai_model)

    # Generation config
    if response_schema:
        model_config = GenerationConfig(
            max_output_tokens=8192,
            temperature=0.0,
            top_p=1,
            response_mime_type="application/json",
            response_schema=response_schema,
        )
    else:
        model_config = GenerationConfig(
            max_output_tokens=8192, temperature=0.0, top_p=1
        )

    # Safety config
    safety_config = [
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=HarmBlockThreshold.BLOCK_NONE,
        ),
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=HarmBlockThreshold.BLOCK_NONE,
        ),
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=HarmBlockThreshold.BLOCK_NONE,
        ),
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=HarmBlockThreshold.BLOCK_NONE,
        ),
    ]

    responses = model.generate_content(
        prompt,
        generation_config=model_config,
        safety_settings=safety_config,
        stream=False,
    )

    try:
        final_response = cast(str, responses.candidates[0].content.parts[0].text)
    except Exception as e:
        print("Error extracting Gemini response:", e)
        print("error", responses)

    return str(final_response)
