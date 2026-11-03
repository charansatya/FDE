# Operational Runbook & Incident Response Playbook

## Part 1: Operational Runbook (Day-1 & Day-2 Operations)

### 1.1 Pre-Deployment Health & Environment Checklist

Before deploying or updating any specialist or the root orchestrator, run the pre-flight verification script:

```bash
cd ~/agents/code-assistant
blank=$(grep -E '^(GITHUB_AGENT_URL|STACKEXCHANGE_AGENT_URL|SALESFORCE_AGENT_URL|BQ_AGENT_URL)=$' .env)
if [ -n "${blank}" ]; then
  echo "ERROR: Blank specialist URLs detected:"
  echo "${blank}"
  exit 1
else
  echo "OK: All specialist URLs are populated."
fi
```

### 1.2 Endpoint Verification Runbook (Smoke Tests)

Verify every A2A agent card is reachable and advertising valid JSON-RPC endpoints:

```bash
# 1. Stack Exchange Agent Card (Cloud Run)
curl -s "${STACKEXCHANGE_AGENT_URL}" | jq '{name, version, supported_interfaces}'

# 2. Salesforce Agent Card (Cloud Run)
curl -s "${SALESFORCE_AGENT_URL}" | jq '{name, version, url, skills: [.skills[].name]}'

# 3. BigQuery Bug DB Agent Card (GKE LoadBalancer)
curl -s "${BQ_AGENT_URL}" | jq '{name, version, url}'

# 4. GitHub Agent Card (Vertex AI Agent Runtime - requires Google ADC Bearer token)
curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "${GITHUB_AGENT_URL}" | jq '{name, version, url}'
```

### 1.3 Unit Test Execution Matrix

Run offline unit tests across all agents prior to deployment:

```bash
# Root Orchestrator (11 unit tests)
cd ~/agents/code-assistant && uv run pytest tests/unit && rm -rf .venv

# Salesforce Specialist (28 unit tests)
cd ~/agents/salesforce-agent && uv run pytest tests/unit && rm -rf .venv

# Stack Exchange Specialist
cd ~/agents/stackexchange-agent && uv run pytest tests/unit && rm -rf .venv

# BigQuery Bug DB Specialist
cd ~/agents/bq-agent && uv run pytest tests/unit && rm -rf .venv
```

### 1.4 Standard Rolling Deployment Procedure

1. **Agent Runtime Targets (`code-assistant`, `github-agent`)**:
   ```bash
   cd ~/agents/<agent-dir>
   rm -rf .venv
   agents-cli deploy --project "${PROJECT_ID}" --no-confirm-project --no-wait \
     --update-env-vars "$(grep -v '^#' .env | grep -v '^$' | grep -v '^GOOGLE_CLOUD_PROJECT' | paste -sd,)"
   agents-cli deploy --status
   ```
2. **Cloud Run Targets (`salesforce-agent`, `stackexchange-agent`)**:
   ```bash
   cd ~/agents/salesforce-agent
   rm -rf .venv
   agents-cli deploy --project "${PROJECT_ID}" --no-confirm-project --no-wait \
     --update-env-vars "$(grep -v '^#' .env | grep -v '^$' | grep -v '^GOOGLE_CLOUD_PROJECT' | paste -sd,)"
   agents-cli deploy --status
   ```
3. **GKE Target (`bq-agent`)**:
   ```bash
   kubectl rollout status deployment/bq-agent
   kubectl get svc bq-agent
   ```

---

## Part 2: Incident Response Playbook (Troubleshooting & RCA)

### Playbook 1: Agent Runtime Deployment Fails on Packaging (`.venv/bin/python` Symlink Error)
- **Symptom**: `agents-cli deploy` fails when archiving the project directory for Vertex AI Agent Runtime.
- **Root Cause**: Local testing (`uv run` or `agents-cli install`) creates a `.venv/` directory containing a symlink (`.venv/bin/python`) pointing outside the workspace root, which the Agent Runtime packager rejects.
- **Remediation**:
  ```bash
  rm -rf .venv
  agents-cli deploy --project "${PROJECT_ID}" --no-confirm-project --no-wait \
    --update-env-vars "$(grep -v '^#' .env | grep -v '^$' | grep -v '^GOOGLE_CLOUD_PROJECT' | paste -sd,)"
  ```

### Playbook 2: ADC / Authentication Failure (`service account info is missing 'email' field`)
- **Symptom**: Deployment or local execution fails with `service account info is missing 'email' field` or `Reauthentication is needed`.
- **Root Cause**: Application Default Credentials (ADC) or `gcloud` user credentials expired in the shell session.
- **Remediation**:
  ```bash
  gcloud auth login
  gcloud auth application-default login
  ```

### Playbook 3: `gcloud run services add-iam-policy-binding` Returns `NOT_FOUND`
- **Symptom**:
  ```text
  ERROR: (gcloud.run.services.add-iam-policy-binding) NOT_FOUND: Resource 'salesforce-agent' of kind 'SERVICE' in region 'us-central1' does not exist.
  ```
- **Root Cause**: The IAM binding command was executed before `agents-cli deploy` created the Cloud Run service (or while Cloud Build was still building the first container image).
- **Remediation**:
  1. Deploy the service first (`agents-cli deploy ...`).
  2. Poll `agents-cli deploy --status` until the Cloud Run service exists.
  3. Re-run `gcloud run services add-iam-policy-binding salesforce-agent --region=us-central1 --member=allUsers --role=roles/run.invoker`.

### Playbook 4: `Workflow` Pydantic Validation Error on `root_agent` Edges
- **Symptom**: `pydantic_core._pydantic_core.ValidationError: validation errors for Workflow` when importing `code-assistant/app/agent.py`.
- **Root Cause**: Passing string node names (e.g. `["START", "query_extractor"]`) or an `"END"` string node in `Workflow(edges=...)`. ADK 2.0 `Workflow` requires `"START"` (literal string) followed by actual `BaseAgent` / `JoinNode` object references in tuples, and terminates automatically at the final node (`synthesizer`) without an `"END"` edge.
- **Remediation**: Ensure `edges` uses `( "START", query_extractor )`, tuple fan-out `(query_extractor, (github_agent, ...))`, tuple fan-in `((github_agent, ...), merge)`, and `(merge, synthesizer)`.

### Playbook 5: Salesforce 2LO Authentication or SOSL Search Returns Empty Results
- **Symptom**: `search_salesforce` returns `Salesforce auth failed: 400 Bad Request` or empty `data: []`.
- **Root Cause**:
  1. For `400/401` on `/services/oauth2/token`: Consumer Key/Secret mismatch, or **Enable Client Credentials Flow** / **Run As User** is not configured on the External Client App / Connected App.
  2. For empty SOSL results: Uploaded `.docx` files were not granted read visibility to the Run-As user (**Query All Files** permission), or the Salesforce full-text search index is still warming up (~15 minutes after upload).
- **Remediation**:
  ```bash
  # Test 2LO authentication directly
  cd ~/agents/salesforce-agent
  uv run python -c "from app.agent import salesforce_client; print(salesforce_client.authenticate())"
  ```

### Playbook 6: Memory Bank Returns `404 Not Found` on Memories Subresource
- **Symptom**: `VertexAiMemoryBankService` fails with `404` when reading or writing memories.
- **Root Cause**: `GOOGLE_CLOUD_LOCATION=global` was passed to `VertexAiMemoryBankService` instead of a regional endpoint (`us-central1`), or `MEMORY_BANK_ID` contains the full `projects/.../reasoningEngines/...` path instead of the numeric ID.
- **Remediation**:
  - Keep `MEMORY_BANK_LOCATION=us-central1` in `.env`.
  - Set `MEMORY_BANK_ID` to the numeric ID only (`engine.api_resource.name.split("/")[-1]`).
