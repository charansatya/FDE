# Operational Runbook & Incident Playbook: GenAI Autorating & Agent Optimization (`Day 3`)

## 1. Operational Runbook

This runbook provides Standard Operating Procedures (SOPs) for running, monitoring, and evaluating the **ADK 2.0 Real Estate Opportunity Analyst** and the **Vertex AI Gen AI Evaluation Service**.

---

### 1.1 Command Reference & Execution Matrix

| Action | Command | Purpose & Parameters |
| :--- | :--- | :--- |
| **All Criteria Analysis** | `python3 -m eval_harness.all_criteria_analysis --run_geap_eval_out <FILE>` | Computes global summary statistics, pairwise agreement, and Krippendorff's Alpha across all evaluated rubrics. |
| **Single Criterion Deep Dive** | `python3 -m eval_harness.single_criterion_analysis --run_geap_eval_out <FILE> --criterion <CRIT_ID>` | Evaluates a single criterion's distribution across reports, variance breakdown, and per-report scores. |
| **Judge Rationale Extraction** | `python3 -m eval_harness.explain_criteria_results --run_geap_eval_out <FILE> --criterion <CRIT_ID> --max_score_to_show <N>` | Extracts the judge's internal chain-of-thought rationale for reports scoring $\le N$. Default threshold: `4.0`. |
| **Automated Hill Climbing** | `python3 -m eval_harness.run_hillclimb [--lots-file <FILE>] [--autorater-model <MODEL>]` | Runs the active agent in `re_analyst/` over target lots, generates traces, runs single-pass GEAP evaluation, and outputs mean scores. |
| **Standalone EvalSet Generation** | `python3 -m eval_harness.create_re_agent_evalset --lots-file <FILE> --output-file <FILE> --agent-dir re_analyst` | Executes the ADK agent concurrently over a list of lots and dumps traces in ADK 2.0 Pydantic EvalSet schema. |
| **Standalone GEAP Execution** | `python3 -m eval_harness.run_geap_eval --traces-path <FILE> --rubrics-path eval_harness/rubrics.json --k-passes <K>` | Dispatches multi-pass ($k$) batch evaluation jobs to Vertex AI Evaluation Service. |

---

### 1.2 Step-by-Step Operational Workflows

#### Workflow A: Executing a Hill Climbing Iteration Cycle
1. **Verify Target Lots**:
   Ensure `eval_harness/hillclimb_lots.txt` contains the desired target lot IDs.
2. **Execute Runner**:
   ```bash
   python3 -m eval_harness.run_hillclimb
   ```
3. **Capture Execution Artifacts**:
   - Trace file: `re_analyst/hillclimb_<X>.evalset.json`
   - Evaluation output: `runs/hillclimb_<X>/geap_calls_and_responses_hillclimb_<X>.json`
4. **Evaluate Exit Criteria**:
   - If both `cost-per-acre` $\ge 4.0$ and `neighboring-flood-risk` $\ge 4.0$, proceed to verification checkpoint.
   - If either score $< 4.0$, proceed to Workflow B.

#### Workflow B: Diagnosing Deficiencies & Mutating Skills
1. **Extract Explanations for Deficient Criteria**:
   ```bash
   python3 -m eval_harness.explain_criteria_results \
     --run_geap_eval_out runs/hillclimb_<X>/geap_calls_and_responses_hillclimb_<X>.json \
     --criterion <deficient-criterion-id> \
     --max_score_to_show 3.0
   ```
2. **Cross-Reference with Rubric Standards**:
   Inspect `eval_harness/rubrics.json` for the target criterion to check the exact requirement for Score 5.
3. **Mutate Targeted Skill in `re_analyst/skills/`**:
   - `analyze-opportunity/SKILL.md`: Mathematical formulas, valuation metrics, synthesis.
   - `analyze-flood-risk/SKILL.md`: Multi-hop adjacent lot queries, drainage, stormwater runoff.
   - `analyze-tax-implications/SKILL.md`: Assessor valuations, monthly carrying rates.
4. **Repeat Workflow A**.

---

## 2. Troubleshooting Playbook

### Incident 1: Vertex AI Evaluation API Quota Exceeded (`429 Resource Exhausted`)

#### Symptom
```text
google.api_core.exceptions.ResourceExhausted: 429 Quota exceeded for aiplatform.googleapis.com/online_eval_requests
```

#### Root Cause
High concurrency or rapid succession of large $k$-pass evaluation requests exhausting regional API quotas.

#### Resolution Steps
1. Throttle the QPS using the `--qps` argument in the runner:
   ```bash
   python3 -m eval_harness.run_hillclimb --qps 2.0
   ```
2. If running standalone `run_geap_eval.py`, reduce `judge_model_sampling_count` or pass count:
   ```bash
   python3 -m eval_harness.run_geap_eval --k-passes 1 --qps 1.5
   ```
3. Verify that Vertex API mTLS is disabled to avoid concurrent connection locks:
   ```bash
   export GOOGLE_API_USE_MTLS=never
   export GOOGLE_API_USE_CLIENT_CERTIFICATE=false
   ```

---

### Incident 2: Broken Pipe or Partial Output Truncation in Explainer Tool

#### Symptom
```text
❌ Error: [Errno 32] Broken pipe
```

#### Root Cause
Piping the output of `explain_criteria_results.py` to `head` or `less` terminates the stdout stream before the Python process finishes writing.

#### Resolution Steps
1. Filter directly using `--max_score_to_show` instead of piping:
   ```bash
   python3 -m eval_harness.explain_criteria_results \
     --run_geap_eval_out runs/hillclimb_1/geap_calls_and_responses_hillclimb_1.json \
     --criterion cost-per-acre \
     --max_score_to_show 2.0
   ```
2. Alternatively, redirect output to a file and view it:
   ```bash
   python3 -m eval_harness.explain_criteria_results ... > /tmp/explanation.log
   cat /tmp/explanation.log
   ```

---

### Incident 3: Agent Fails to Query Adjacent Parcels

#### Symptom
Judge gives a score of 1.0 on `neighboring-flood-risk` with rationale:
> *"The response completely omits any mention of neighboring or adjacent property flood risks."*

#### Diagnostic Steps
1. Check if the agent called `get_lot_data` for adjacent parcels in the intermediate trace:
   ```python
   import json
   with open("re_analyst/hillclimb_1.evalset.json") as f:
       evalset = json.load(f)
   # Inspect functionCall events in intermediateData
   ```
2. Check `re_analyst/skills/analyze-flood-risk/SKILL.md` metadata:
   Ensure `adk_additional_tools` lists `get_lot_data`:
   ```yaml
   metadata:
     adk_additional_tools:
       - get_lot_data
   ```
3. Verify that `tools_data/lots_database.json` contains `adjacent_parcels` for the given lot ID.

---

### Incident 4: Score Regression After Skill Modification

#### Symptom
After modifying skills, `cost-per-acre` drops from 5.0 to 2.0, or another metric regresses.

#### Root Cause
The prompt or skill instruction inadvertently omitted mandatory keywords, changed section headers, or failed to display the explicit mathematical division formula.

#### Resolution Steps
1. Re-read the exact rating scale requirements in `eval_harness/rubrics.json`:
   - Score 4: Correctly computes cost-per-acre with clear derivation.
   - Score 5: Accurately calculates AND highlights exact cost-per-acre as a core valuation metric.
2. Ensure the agent explicitly writes out the formula text:
   `Acquisition Cost-Per-Acre Calculation: Last Sale Price ($[X]) / Acreage ([Y] acres) = $[Z] per acre`
3. Ensure section headers match standard ADK memorandum format:
   - `## Executive Summary`
   - `## Acquisition Basis and Holding Costs`
   - `## Zoning and Infrastructure Readiness`
   - `## Risk Assessment`
   - `## Recommendation`

---

## 3. Best Practices for Enterprise GenAI Autorating

1. **Unambiguous Anchor Definitions**:
   Avoid vague rubrics (e.g., "Good tone" vs "Bad tone"). Define concrete factual criteria: "Mentions exact parcel ID, numerical cost-per-acre formula, and adjacent parcel FEMA flood zones."
2. **Multi-Pass Inter-Rater Verification**:
   Never deploy an autorater in production with $k=1$ until you have run a benchmark with $k \ge 8$ and verified that Krippendorff's Alpha satisfies $\alpha \ge 0.800$.
3. **Guard Against Ceiling Effects**:
   A criterion where the autorater assigns 5.0 to every test case has zero diagnostic utility. Review report standard deviations (`sd report means`) to ensure the rubric discriminates quality effectively.
4. **Decouple Dynamic Skills from Static System Prompts**:
   Use ADK's `SkillToolset` to modularize complex domain checks (`analyze-flood-risk`, `analyze-tax-implications`). This reduces context window bloat and allows surgical prompt engineering without destabilizing unrelated capabilities.
