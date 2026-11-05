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

"""Unit tests for bq-agent tools, agent definition, and A2A skill card."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from a2a.types import AgentCard

from app.agent import root_agent
from app.app_utils.a2a import _set_single_bug_search_skill
from app.tools import find_similar_bugs


def test_find_similar_bugs_empty_query() -> None:
    """Empty or whitespace-only queries return a clear message without calling GCP."""
    result = find_similar_bugs("   ")
    assert "no similar bugs found" in result.lower()


@patch("app.tools.bigquery.Client")
@patch("app.tools.genai.Client")
@patch("app.tools._resolve_project_id", return_value="test-project")
def test_find_similar_bugs_returns_formatted_matches(
    mock_project_id: MagicMock,
    mock_genai_cls: MagicMock,
    mock_bq_cls: MagicMock,
) -> None:
    """Matching rows from VECTOR_SEARCH include bug_id, title, description, resolution, and distance."""
    mock_genai = mock_genai_cls.return_value
    mock_genai.models.embed_content.return_value = SimpleNamespace(
        embeddings=[SimpleNamespace(values=[0.1] * 768)]
    )

    fake_row = SimpleNamespace(
        bug_id="BUG-1001",
        title="FastAPI service returns 500 on startup after dependency bump",
        description="After upgrading pydantic from v1 to v2, the FastAPI app crashes on startup.",
        resolution="Migrate models to Pydantic v2: replace class Config with model_config = ConfigDict(...).",
        distance=0.1359,
    )
    mock_bq = mock_bq_cls.return_value
    mock_bq.query.return_value.result.return_value = [fake_row]

    output = find_similar_bugs("FastAPI returns a 500 on startup after a dependency bump.")

    mock_genai_cls.assert_called_once_with(
        vertexai=True,
        project="test-project",
        location="us-central1",
    )
    mock_genai.models.embed_content.assert_called_once_with(
        model="text-embedding-004",
        contents="FastAPI returns a 500 on startup after a dependency bump.",
    )

    sql_arg = mock_bq.query.call_args[0][0]
    assert "VECTOR_SEARCH" in sql_arg
    assert "description_embedding" in sql_arg
    assert "COSINE" in sql_arg
    assert "top_k => 3" in sql_arg
    assert "ORDER BY distance ASC" in sql_arg

    assert "BUG-1001" in output
    assert "FastAPI service returns 500 on startup after dependency bump" in output
    assert "0.1359" in output
    assert "Migrate models to Pydantic v2" in output


@patch("app.tools.bigquery.Client")
@patch("app.tools.genai.Client")
@patch("app.tools._resolve_project_id", return_value="test-project")
def test_find_similar_bugs_no_matches(
    mock_project_id: MagicMock,
    mock_genai_cls: MagicMock,
    mock_bq_cls: MagicMock,
) -> None:
    """When BigQuery returns zero rows, return a clear 'no similar bugs found' message."""
    mock_genai = mock_genai_cls.return_value
    mock_genai.models.embed_content.return_value = SimpleNamespace(
        embeddings=[SimpleNamespace(values=[0.2] * 768)]
    )
    mock_bq = mock_bq_cls.return_value
    mock_bq.query.return_value.result.return_value = []

    output = find_similar_bugs("Unrelated query")
    assert "no similar bugs found" in output.lower()


@patch("app.tools.genai.Client", side_effect=RuntimeError("Vertex AI quota exceeded"))
@patch("app.tools._resolve_project_id", return_value="test-project")
def test_find_similar_bugs_embedding_unavailable_graceful_degradation(
    mock_project_id: MagicMock,
    mock_genai_cls: MagicMock,
) -> None:
    """When Vertex AI embedding fails, return a graceful message instead of raising."""
    output = find_similar_bugs("Some software error")
    assert "temporarily unavailable" in output.lower()


@patch("app.tools.bigquery.Client", side_effect=RuntimeError("BigQuery service error"))
@patch("app.tools.genai.Client")
@patch("app.tools._resolve_project_id", return_value="test-project")
def test_find_similar_bugs_bigquery_unavailable_graceful_degradation(
    mock_project_id: MagicMock,
    mock_genai_cls: MagicMock,
    mock_bq_cls: MagicMock,
) -> None:
    """When BigQuery fails, return a graceful message instead of raising."""
    mock_genai = mock_genai_cls.return_value
    mock_genai.models.embed_content.return_value = SimpleNamespace(
        embeddings=[SimpleNamespace(values=[0.1] * 768)]
    )

    output = find_similar_bugs("Some software error")
    assert "temporarily unavailable" in output.lower()


def test_agent_and_single_a2a_skill() -> None:
    """Verify root_agent configuration and single A2A skill with example query."""
    assert root_agent.name == "bq_agent"
    assert find_similar_bugs in root_agent.tools

    card = _set_single_bug_search_skill(AgentCard(name="bq_agent"))
    assert len(card.skills) == 1
    assert card.skills[0].id == "find_similar_bugs"
    assert len(card.skills[0].examples) >= 1
    assert "FastAPI" in card.skills[0].examples[0]
