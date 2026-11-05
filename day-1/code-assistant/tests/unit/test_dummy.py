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
"""
You can add your unit tests here.
This is where you test your business logic, including agent functionality,
data processing, and other core components of your application.
"""


from types import SimpleNamespace
import pytest

from app.callbacks import capture_response_to_state


def test_dummy() -> None:
    """Placeholder - replace with real tests."""
    assert 1 == 1


@pytest.mark.asyncio
async def test_capture_response_to_state_saves_latest_matching_text() -> None:
    """Saves joined text parts of the most recent event matching agent_name."""
    events = [
        SimpleNamespace(
            author="github_agent",
            content=SimpleNamespace(parts=[SimpleNamespace(text="older reply")]),
        ),
        SimpleNamespace(
            author="other_agent",
            content=SimpleNamespace(parts=[SimpleNamespace(text="other reply")]),
        ),
        SimpleNamespace(
            author="github_agent",
            content=SimpleNamespace(
                parts=[
                    SimpleNamespace(text="part 1"),
                    SimpleNamespace(text=None),
                    SimpleNamespace(text="part 2"),
                ]
            ),
        ),
        SimpleNamespace(
            author="github_agent",
            content=SimpleNamespace(parts=[SimpleNamespace(text=None)]),
        ),
    ]
    ctx = SimpleNamespace(
        agent_name="github_agent",
        session=SimpleNamespace(events=events),
        state={},
    )

    cb = capture_response_to_state("github_findings")
    result = await cb(ctx)

    assert result is None
    assert ctx.state["github_findings"] == "part 1\npart 2"

