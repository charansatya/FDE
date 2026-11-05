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

"""Bug Database specialist agent (ADK + BigQuery VECTOR_SEARCH, exposed via A2A)."""

import os

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

from app.tools import find_similar_bugs

load_dotenv()

MODEL = os.environ.get("MODEL", "gemini-3.5-flash")

INSTRUCTION = """You are `bq_agent`, a specialist engineering-incident agent that answers one question well:
"Have we seen this software problem before, and how was it fixed?"

## Workflow
1. For any reported software problem, exception, stack trace, or bug query, call `find_similar_bugs` with a clear problem description capturing the symptom, framework/language, and key error terms.
2. Inspect the returned matches and their cosine distances:
   - Lower cosine distance indicates higher semantic similarity.
   - Determine which returned incidents actually match or are relevant to the reported problem.
3. Respond concisely and practically:
   - Summarize only the relevant matching incidents and their concrete resolutions from the `find_similar_bugs` results.
   - **Always cite each `bug_id`** used (for example, `BUG-1001`).
4. **Strict grounding**:
   - Summarize **only** what `find_similar_bugs` returns.
   - Never invent or fabricate incidents, `bug_id`s, resolutions, or details.
   - If `find_similar_bugs` returns no matches, if the search service is unavailable, or if none of the returned top-k rows are relevant to the user's question, clearly state that no matching known bugs were found in the bug database.
"""

root_agent = Agent(
    # Keep in sync with create_params.root_agent_name in agents-cli-manifest.yaml
    name="bq_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    description=(
        "Performs semantic search over the internal BigQuery database of past "
        "engineering incidents and returns similar known bugs with their "
        "bug_id and resolution."
    ),
    instruction=INSTRUCTION,
    tools=[find_similar_bugs],
)

app = App(
    root_agent=root_agent,
    name="app",
)
