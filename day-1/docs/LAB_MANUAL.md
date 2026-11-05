# Step-by-Step Lab Manual: Multi-Agent Code Assistant on Google Cloud

This manual provides the complete, step-by-step walkthrough for building, testing, and deploying all components of the **Multi-Agent Code Assistant** lab across Tasks 1 through 7.

---

## Prerequisites & Environment Variables

Set your core project and region variables in Cloud Shell:

```bash
export PROJECT_ID=$(gcloud config get-value project)
export PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" --format="value(projectNumber)")
export REGION=us-central1
gcloud config set project "${PROJECT_ID}"
```

---

## Task 1: Create the Vertex AI Search Datastore (`code-manuals-datastore`)

The `manual_search_agent` searches internal engineering handbooks stored in a Vertex AI Search datastore.

1. In the Google Cloud Console, navigate to **AI Applications (Vertex AI Search)** $\rightarrow$ **Data Stores**.
2. Create an unstructured document datastore in location **`global`** named:
   - **Data store ID**: `code-manuals-datastore`
3. Import the internal engineering handbook documents from the lab's Cloud Storage bucket into `code-manuals-datastore`.

---

## Task 2: Build and Deploy the GitHub Specialist Agent (`github-agent`)

The `github-agent` connects to the remote GitHub Copilot MCP server using ADK's `McpToolset` and runs on **Vertex AI Agent Runtime (Agent Engine)**.

### Step 2.1: Implement `McpToolset` in `github-agent/app/agent.py`
Open `~/agents/github-agent/app/agent.py` and configure `github_mcp_toolset` to authenticate with `GITHUB_TOKEN` and restrict tools to `GITHUB_TOOL_FILTER`:

```python
github_mcp_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=GITHUB_MCP_URL,
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "X-MCP-Toolsets": "all",
            "X-MCP-Readonly": "true",
        },
    ),
    tool_filter=GITHUB_TOOL_FILTER,
)
```

### Step 2.2: Configure `github-agent/.env` and Deploy to Agent Runtime

```bash
cd ~/agents/github-agent
cat << EOF > .env
GOOGLE_CLOUD_PROJECT=${PROJECT_ID}
GOOGLE_CLOUD_LOCATION=global
GOOGLE_GENAI_USE_VERTEXAI=True
MODEL=gemini-3.5-flash
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_YOUR_GITHUB_PAT
GITHUB_MCP_URL=https://api.githubcopilot.com/mcp/
EOF

rm -rf .venv
agents-cli deploy --project "${PROJECT_ID}" --no-confirm-project --no-wait \
  --update-env-vars "$(grep -v '^#' .env | grep -v '^$' | grep -v '^GOOGLE_CLOUD_PROJECT' | paste -sd,)"

# Poll until deployment succeeds
agents-cli deploy --status
```

Export the resulting Agent Card URL:
```bash
export GITHUB_AGENT_URL="https://us-central1-aiplatform.googleapis.com/reasoningEngines/v1/projects/${PROJECT_NUMBER}/locations/us-central1/reasoningEngines/<ENGINE_ID>/api/a2a/app/.well-known/agent-card.json"
```

---

## Task 3: Build and Deploy the Stack Exchange Specialist Agent (`stackexchange-agent`)

The `stackexchange-agent` is a deterministic LangGraph agent wrapped with `a2a-sdk 1.x` and deployed to **Cloud Run**.

### Step 3.1: Advertise Dual 1.0 and 0.3 Interfaces in `stackexchange-agent/app/server.py`
Open `~/agents/stackexchange-agent/app/server.py` and complete `supported_interfaces` in `build_agent_card`:

```python
        supported_interfaces=[
            AgentInterface(protocol_binding="JSONRPC", protocol_version="1.0", url=rpc_url),
            AgentInterface(protocol_binding="JSONRPC", protocol_version="0.3", url=rpc_url),
        ],
```

### Step 3.2: Deploy to Cloud Run and Export URL

```bash
cd ~/agents/stackexchange-agent
gcloud run deploy stackexchange-agent \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --source=. \
  --allow-unauthenticated \
  --quiet

export STACKEXCHANGE_BASE_URL=$(gcloud run services describe stackexchange-agent \
  --project="${PROJECT_ID}" --region="${REGION}" --format="value(status.url)")

gcloud run services update stackexchange-agent \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --set-env-vars="PUBLIC_URL=${STACKEXCHANGE_BASE_URL}" \
  --quiet

export STACKEXCHANGE_AGENT_URL="${STACKEXCHANGE_BASE_URL}/.well-known/agent-card.json"
```

---

## Task 4: Build and Deploy the BigQuery Bug Database Specialist (`bq-agent`)

The `bq-agent` embeds incident descriptions using `text-embedding-004` and runs BigQuery `VECTOR_SEARCH` (`COSINE` distance, `top_k=3`) against `code_assist_bugs.known_bugs`, deployed on **GKE**.

### Step 4.1: Verify `find_similar_bugs` in `bq-agent/app/tools.py`
The tool embeds the query via `client.models.embed_content(model="text-embedding-004", contents=query)` and queries `VECTOR_SEARCH(TABLE \`${project_id}.code_assist_bugs.known_bugs\`, 'description_embedding', ...)`.

### Step 4.2: Build Container Image & Deploy to GKE
```bash
cd ~/agents/bq-agent
# Build and push container image to Artifact Registry, then apply K8s manifests
kubectl apply -f k8s/
kubectl get svc bq-agent
export BQ_AGENT_URL="http://<EXTERNAL_IP>:8080/a2a/app/.well-known/agent-card.json"
```

---

## Task 5: Wire the Root Code Assistant Workflow (`code-assistant`)

### Step 5.1: Implement `GoogleADCAuth._apply` in `code-assistant/app/auth.py`
Open `~/agents/code-assistant/app/auth.py` and complete `_apply` so outgoing requests to Agent Runtime carry a valid Google OAuth2 Bearer token:

```python
    def _apply(self, request: httpx.Request) -> None:
        headers: dict[str, str] = {}
        self._creds.before_request(
            GoogleAuthRequest(), request.method, str(request.url), headers
        )
        request.headers.update(headers)
```

### Step 5.2: Define Remote Specialists & Workflow Graph in `code-assistant/app/agent.py`
Open `~/agents/code-assistant/app/agent.py`:

1. **`github_agent`**:
   ```python
   github_agent = RemoteA2aAgent(
       name="github_agent",
       description="Searches GitHub issues and PRs.",
       agent_card=GITHUB_AGENT_URL,
       httpx_client=google_authed_client(),
       use_legacy=False,
       after_agent_callback=capture_response_to_state("github_findings"),
   )
   ```
2. **`stackexchange_agent`**:
   ```python
   stackexchange_agent = CleanQueryRemoteA2aAgent(
       name="stackexchange_agent",
       description="Searches Stack Exchange for community answers.",
       agent_card=STACKEXCHANGE_AGENT_URL,
       after_agent_callback=capture_response_to_state("stackexchange_findings"),
   )
   ```
3. **`root_agent` Workflow Graph Edges**:
   ```python
   root_agent = Workflow(
       name="code_assist_agent",
       description=(
           "End-to-end engineering assistant: extracts the core query, searches "
           "GitHub, Stack Exchange, Salesforce ADRs/policies, the Bug DB, and "
           "product manuals in parallel, then synthesizes a cited answer."
       ),
       edges=[
           ("START", query_extractor),
           (
               query_extractor,
               (
                   github_agent,
                   stackexchange_agent,
                   salesforce_agent,
                   bug_db_agent,
                   manual_search_agent,
               ),
           ),
           (
               (
                   github_agent,
                   stackexchange_agent,
                   salesforce_agent,
                   bug_db_agent,
                   manual_search_agent,
               ),
               merge,
           ),
           (merge, synthesizer),
       ],
   )
   ```

### Step 5.3: Publish the Developer Knowledge Skill to GCP Skill Registry
```bash
cd ~/agents/code-assistant
uv run python scripts/publish_skill.py \
  --project "${PROJECT_ID}" \
  --location us-central1
```

### Step 5.4: Test Locally
```bash
cd ~/agents/code-assistant
uv run pytest tests/unit
agents-cli install
agents-cli playground
```

---

## Task 6: Deploy the Root Agent (`code-assistant`) to Agent Runtime

```bash
cd ~/agents/code-assistant
rm -rf .venv
agents-cli deploy --project "${PROJECT_ID}" --no-confirm-project --no-wait \
  --update-env-vars "$(grep -v '^#' .env | grep -v '^$' | grep -v '^GOOGLE_CLOUD_PROJECT' | paste -sd,)"

agents-cli deploy --status
```

---

## Task 7: Implement the Salesforce Specialist Agent with Long-Term Memory (`salesforce-agent`)

### Step 7.1: Implement 2-Legged OAuth in `salesforce-agent/app/salesforce_client.py`
In `SalesforceClient.authenticate()`:
```python
        resp = requests.post(
            f"https://{self.domain}/services/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            timeout=_TIMEOUT_SECONDS,
        )
        _raise_for_status(resp)
        return resp.json()
```

### Step 7.2: Implement User-Scoped Request Conversion in `salesforce-agent/app/app_utils/a2a.py`
In `_user_scoped_request_converter()`:
```python
    run_request = convert_a2a_request_to_agent_run_request(
        request, part_converter
    )
    forwarded_user_id = (request.metadata or {}).get("user_id")
    if forwarded_user_id:
        run_request.user_id = forwarded_user_id
    return run_request
```

### Step 7.3: Enable Memory Tools & Callback in `salesforce-agent/app/agent.py`
```python
async def generate_memories_callback(callback_context: CallbackContext) -> None:
    await callback_context.add_session_to_memory()
```
And in `root_agent`:
```python
    tools=[search_salesforce, PreloadMemoryTool()],
    after_agent_callback=generate_memories_callback,
```

### Step 7.4: Forward `user_id` from Root Agent in `code-assistant/app/app_utils/a2a.py`
In `user_id_meta_provider()`:
```python
def user_id_meta_provider(ctx: InvocationContext, a2a_message) -> dict[str, str]:
    return {"user_id": ctx.user_id}
```

### Step 7.5: Implement & Run Idempotent Memory Bank Provisioning (`salesforce-agent/scripts/create_memory_bank.py`)
```python
    engine = next(
        (
            e
            for e in client.agent_engines.list()
            if e.api_resource.display_name == DISPLAY_NAME
        ),
        None,
    )
    if engine is not None:
        print(f"Found existing Memory Bank '{DISPLAY_NAME}': {engine.api_resource.name}")
    else:
        print(f"Creating Memory Bank '{DISPLAY_NAME}'...")
        engine = client.agent_engines.create(
            config={"display_name": DISPLAY_NAME}
        )
        print(f"Created Memory Bank '{DISPLAY_NAME}': {engine.api_resource.name}")
    memory_bank_id = engine.api_resource.name.split("/")[-1]
    print(f"MEMORY_BANK_ID={memory_bank_id}")
```

Run the script and add `MEMORY_BANK_ID` to `~/agents/salesforce-agent/.env`:
```bash
cd ~/agents/salesforce-agent
GOOGLE_CLOUD_PROJECT=${PROJECT_ID} uv run python scripts/create_memory_bank.py
```

### Step 7.6: Deploy `salesforce-agent` to Cloud Run and Grant Invoker Role
```bash
cd ~/agents/salesforce-agent
rm -rf .venv
agents-cli deploy --project "${PROJECT_ID}" --no-confirm-project --no-wait \
  --update-env-vars "$(grep -v '^#' .env | grep -v '^$' | grep -v '^GOOGLE_CLOUD_PROJECT' | paste -sd,)"

agents-cli deploy --status

gcloud run services add-iam-policy-binding salesforce-agent \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --member=allUsers \
  --role=roles/run.invoker \
  --quiet
```

### Step 7.7: Update `SALESFORCE_AGENT_URL` in `code-assistant/.env` and Redeploy Root Agent
```bash
export SALESFORCE_BASE_URL=$(gcloud run services describe salesforce-agent \
  --project="${PROJECT_ID}" --region="${REGION}" --format="value(status.url)")
export SALESFORCE_AGENT_URL="${SALESFORCE_BASE_URL}/a2a/app/.well-known/agent-card.json"

cd ~/agents/code-assistant
sed -i "s|^SALESFORCE_AGENT_URL=.*|SALESFORCE_AGENT_URL=${SALESFORCE_AGENT_URL}|" .env

rm -rf .venv
agents-cli deploy --project "${PROJECT_ID}" --no-confirm-project --no-wait \
  --update-env-vars "$(grep -v '^#' .env | grep -v '^$' | grep -v '^GOOGLE_CLOUD_PROJECT' | paste -sd,)"

agents-cli deploy --status
```
