# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Read-only BigQuery semantic search tool for known engineering incidents."""

from __future__ import annotations

import logging
import os

import google.auth
from google import genai
from google.cloud import bigquery

logger = logging.getLogger(__name__)

DEFAULT_BQ_DATASET = "code_assist_bugs"
DEFAULT_BQ_TABLE = "known_bugs"
DEFAULT_EMBEDDING_MODEL = "text-embedding-004"
DEFAULT_EMBEDDING_LOCATION = "us-central1"
TOP_K = 3


def _resolve_project_id() -> str:
    """Resolves the Google Cloud project ID from environment or ADC."""
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT")
    if project_id:
        return project_id
    _, adc_project = google.auth.default()
    if adc_project:
        return adc_project
    raise RuntimeError("GOOGLE_CLOUD_PROJECT is not set and could not be determined from ADC.")


def _embed_query(query: str, *, project_id: str, location: str, model: str) -> list[float]:
    """Generates a 768-dim embedding vector for the query string via Vertex AI."""
    client = genai.Client(
        vertexai=True,
        project=project_id,
        location=location,
    )
    response = client.models.embed_content(
        model=model,
        contents=query,
    )
    if not response.embeddings or not response.embeddings[0].values:
        raise ValueError("Embedding model returned an empty embedding vector.")
    return [float(v) for v in response.embeddings[0].values]


def find_similar_bugs(query: str) -> str:
    """Searches the internal BigQuery bug database for similar past incidents.

    Embeds the free-text problem description with ``text-embedding-004`` and
    runs BigQuery ``VECTOR_SEARCH`` (cosine distance, top_k=3) against
    ``code_assist_bugs.known_bugs.description_embedding``.

    Args:
        query: A free-text problem description (exception, key stack-trace
            terms, language/framework, symptom).

    Returns:
        Formatted matches including ``bug_id``, ``title``, ``description``,
        ``resolution``, and cosine ``distance``, a clear "no similar bugs found"
        message if the table returns no matches, or a graceful degradation
        message if embedding or BigQuery is temporarily unavailable.
    """
    if not query or not query.strip():
        return "No similar bugs found: query was empty."

    dataset = os.environ.get("BQ_DATASET", DEFAULT_BQ_DATASET)
    table = os.environ.get("BQ_TABLE", DEFAULT_BQ_TABLE)
    embedding_model = os.environ.get("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)
    embedding_location = os.environ.get(
        "EMBEDDING_LOCATION", DEFAULT_EMBEDDING_LOCATION
    )

    try:
        project_id = _resolve_project_id()
        query_vector = _embed_query(
            query.strip(),
            project_id=project_id,
            location=embedding_location,
            model=embedding_model,
        )
    except Exception as exc:
        logger.warning("Failed to embed bug query %r: %s", query, exc)
        return (
            "Bug database search is temporarily unavailable because query "
            f"embedding failed ({type(exc).__name__}: {exc})."
        )

    sql = f"""
        SELECT
            base.bug_id AS bug_id,
            base.title AS title,
            base.description AS description,
            base.resolution AS resolution,
            distance
        FROM VECTOR_SEARCH(
            TABLE `{project_id}.{dataset}.{table}`,
            'description_embedding',
            (SELECT @query_embedding AS embedding),
            top_k => {TOP_K},
            distance_type => 'COSINE'
        )
        ORDER BY distance ASC
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter("query_embedding", "FLOAT64", query_vector),
        ],
    )

    try:
        bq_client = bigquery.Client(project=project_id)
        rows = list(bq_client.query(sql, job_config=job_config).result())
    except Exception as exc:
        logger.warning("BigQuery VECTOR_SEARCH failed for query %r: %s", query, exc)
        return (
            "Bug database search is temporarily unavailable because the BigQuery "
            f"query failed ({type(exc).__name__}: {exc})."
        )

    if not rows:
        return "No similar bugs found in the bug database."

    formatted: list[str] = []
    for row in rows:
        distance_val = float(row.distance) if row.distance is not None else 1.0
        formatted.append(
            f"- bug_id: {row.bug_id}\n"
            f"  title: {row.title}\n"
            f"  cosine_distance: {distance_val:.4f}\n"
            f"  description: {row.description}\n"
            f"  resolution: {row.resolution}"
        )

    return "Similar known bugs (ordered by ascending cosine distance):\n\n" + "\n\n".join(
        formatted
    )
