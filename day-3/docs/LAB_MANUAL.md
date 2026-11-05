# Step-by-Step Lab Manual: Vertex AI GenAI Evaluation Service & ADK Agent Hill Climbing (`Day 3`)

## 1. Lab Overview & Objectives

In this hands-on lab, you will evaluate and optimize an autonomous Generative AI Real Estate Investment Opportunity Analyst agent built on the **Google Cloud Agent Development Kit (ADK 2.0)**. 

### Core Objectives
1. **Analyze Autorater Reliability**: Evaluate multi-pass ($k=12$) judge evaluation telemetry to compute statistical agreement metrics (Mean, Pairwise Agreement, Krippendorff's Alpha).
2. **Filter Reliable Evaluation Criteria**: Identify rubrics with high intra-rater consistency versus criteria suffering from subjective variance or ceiling effects.
3. **Execute Baseline Hill Climbing**: Run automated single-pass ($k=1$) evaluation over 10 target edge-case properties.
4. **Dissect Judge Rationales**: Use automated explanatory tooling to perform root-cause analysis on failing agent traces.
5. **Engineer Modular Agent Skills**: Mutate ADK investigation skills to provide explicit mathematical derivation and multi-hop adjacent parcel queries.
6. **Achieve Production Quality Targets**: Elevate agent criteria mean scores above the required **`> 4.0`** threshold.

---

## 2. Environment Setup & Pre-Flight Checks

### Step 2.1: Verify Directory Structure
Navigate to the lab workspace:
```bash
cd ~/autoraters
ls -la
```
Ensure the following directories exist:
- `eval_harness/`: Evaluation scripts, metrics calculator, and rubrics.
- `re_analyst/`: ADK agent definition, skills, and tools.
- `tools_data/`: County property records (`lots_database.json`) and tax database (`tax_database.json`).
- `runs/`: Evaluation outputs and telemetry.

### Step 2.2: Verify Google Cloud & Vertex AI Environment
Ensure that Application Default Credentials (ADC) and project environment variables are loaded:
```bash
echo "Project: $GOOGLE_CLOUD_PROJECT"
echo "Location: $GOOGLE_CLOUD_LOCATION"
gcloud auth list
```

---

## 3. Task 1: Autorater Agreement Analysis ($k=12$ Multi-Pass)

Before optimizing an agent, we must ensure our evaluation judge is reliable and consistent.

### Step 3.1: Execute Global Criteria Analysis
Execute the comprehensive statistical summary script over 12 evaluation passes:
```bash
python3 -m eval_harness.all_criteria_analysis \
  --run_geap_eval_out runs/geap_calls_and_responses_for_analysis.json
```

#### Output Metrics Summary Table
```text
=== GEAP Evaluation Metrics Summary ===
| criterion_id           | criterion_name                                | mean   | min rating | max rating | sd report means | sd pass means | pairwise %_agree | alpha |
| ---------------------- | --------------------------------------------- | ------ | ---------- | ---------- | --------------- | ------------- | ---------------- | ----- |
| monthly-tax-holding    | Monthly Tax Holding Cost Calculation          | 2.2764 |          2 |          5 |          0.8872 |        0.0228 |           99.17% | 0.997 |
| environmental-esa      | Environmental Status (Phase I ESA) Evaluation | 4.2772 |          2 |          5 |          0.7042 |        0.0991 |           79.10% | 0.897 |
| flood-zone-flagging    | Precise Flood Zone Flagging                   | 4.8447 |          3 |          5 |          0.3357 |        0.0256 |           94.41% | 0.897 |
| risk-assessment        | Comprehensive Risk Assessment                 | 4.9532 |          3 |          5 |          0.1843 |        0.0306 |           96.25% | 0.803 |
| utility-topography     | Utility & Topography Evaluation               | 4.7756 |          4 |          5 |          0.3081 |        0.0695 |           82.57% | 0.751 |
| cost-per-acre          | Acquisition Cost-Per-Acre Calculation         | 1.3771 |          1 |          3 |          0.2163 |        0.0511 |           58.97% | 0.565 |
| neighboring-flood-risk | Neighboring Property Flood Risk Analysis      | 1.0316 |          1 |          2 |          0.1768 |        0.0009 |          100.00% |     1 |
| general-tone           | General Tone Suitability                      |      5 |          5 |          5 |               0 |             0 |          100.00% |     1 |
```

### Step 3.2: Interpreting Statistical Agreement
1. **Ceiling Effect / Artificial Agreement**: Criteria such as `general-tone`, `logical-flow`, and `readability` show `alpha = 1.0` solely because the judge rated every single report a `5` with zero variance (`sd = 0.0`). These metrics lack discriminative ability.
2. **Reliable Discriminating Criteria**: Criteria like `monthly-tax-holding` ($\alpha = 0.997$), `environmental-esa` ($\alpha = 0.897$), and `flood-zone-flagging` ($\alpha = 0.897$) exhibit wide variance across reports (`sd report means > 0.3`) but high consistency across passes (`sd pass means < 0.1`).
3. **Save Selected Criteria**:
Save the three most reliable criteria to `best_criteria_submission.txt`:
```bash
echo "monthly-tax-holding,environmental-esa,flood-zone-flagging" > best_criteria_submission.txt
```

---

## 4. Task 2: Baseline Hill Climbing Run (`hillclimb_1`)

The objective is to optimize the agent for two high-priority business metrics:
1. `cost-per-acre` (Acquisition Cost-Per-Acre Calculation)
2. `neighboring-flood-risk` (Neighboring Property Flood Risk Analysis)

The target properties are listed in `eval_harness/hillclimb_lots.txt` (10 edge-case parcels: `LOT-8472`, `LOT-8471`, `LOT-8473`, `LOT-1000` to `LOT-1006`).

### Step 4.1: Run the Hill Climbing Harness
```bash
python3 -m eval_harness.run_hillclimb
```

### Step 4.2: Inspect Baseline Results
The execution completes with versioned output in `runs/hillclimb_1/`:
```text
=========================================
📊 Hill Climbing Results: hillclimb_1
=========================================
 • cost-per-acre             Mean Score: 1.4000
 • neighboring-flood-risk    Mean Score: 1.1000
=========================================
```
Both scores are severely deficient and far below the target of **`> 4.0`**.

---

## 5. Task 3: Dissecting Judge Failure Rationales

Use `explain_criteria_results.py` to extract the Gemini judge's internal reasoning.

### Step 5.1: Analyze `cost-per-acre` Failures
```bash
python3 -m eval_harness.explain_criteria_results \
   --run_geap_eval_out runs/hillclimb_1/geap_calls_and_responses_hillclimb_1.json \
   --criterion cost-per-acre \
   --max_score_to_show 4.0
```
#### Judge Rationale Sample (LOT-1000 / Score 1.0):
> *"The response provides the last sale price ($310,000) and the acreage (3.1 acres), but it completely omits the actual mathematical calculation of the cost-per-acre based on these figures, nor does it state the derived cost-per-acre."*

### Step 5.2: Analyze `neighboring-flood-risk` Failures
```bash
python3 -m eval_harness.explain_criteria_results \
   --run_geap_eval_out runs/hillclimb_1/geap_calls_and_responses_hillclimb_1.json \
   --criterion neighboring-flood-risk \
   --max_score_to_show 4.0
```
#### Judge Rationale Sample (LOT-8472 / Score 1.0):
> *"The response meticulously details the flood risk for the subject parcel (LOT-8472) but completely omits any investigation or discussion of the flood zone designations or hydrological risks of neighboring or adjacent properties."*

---

## 6. Task 4: Modifying & Engineering Agent Skills

To fix these deficiencies, we modify the agent's modular skills in `re_analyst/skills/`.

### Step 6.1: Update `re_analyst/skills/analyze-opportunity/SKILL.md`
Mandate calculating and benchmarking the exact acquisition cost-per-acre with formula derivation:
```markdown
---
name: analyze-opportunity
description: Investigates a land parcel for real estate investment opportunity analysis, calculating core acquisition valuation metrics and coordinating risk and tax assessments.
metadata:
  adk_additional_tools:
    - get_lot_data
---
# Analyze Opportunity Skill

When asked to investigate a property or analyze an investment opportunity for a lot:

## 1. Retrieve Lot Data
Use the `get_lot_data` tool to look up the property attributes by its lot ID (e.g., `LOT-8472`).

## 2. Calculate Acquisition Cost-Per-Acre (Core Valuation Metric)
- Extract the `last_sale_price` and `acreage` from the lot record.
- Accurately calculate the exact mathematical acquisition cost-per-acre:
  $$\text{Acquisition Cost Per Acre} = \frac{\text{Last Sale Price}}{\text{Acreage}}$$
- In the memorandum under `## Acquisition Basis and Holding Costs`, prominently feature and highlight this figure as a core valuation metric.
- Always display the explicit mathematical formula and derivation, e.g.:
  `Acquisition Cost-Per-Acre Calculation: Last Sale Price ($[last_sale_price]) / Acreage ([acreage] acres) = $[calculated_cost_per_acre] per acre`
- Benchmark and emphasize this metric within the valuation context (e.g., assessing whether the cost-per-acre represents an advantageous basis, fair market pricing, or premium valuation for the submarket).

## 3. Investigate Flood and Hydrological Risks (Subject & Neighboring Lots)
- Consult and execute the `analyze-flood-risk` skill.
- Note the `adjacent_parcels` list in the property attributes returned by `get_lot_data`.
- You MUST investigate not only the subject lot, but ALSO every adjacent property by calling `get_lot_data` for each adjacent parcel ID.
- Detail the flood zone designations and evaluate runoff, drainage, and shared hydrological risks under `## Risk Assessment`.

## 4. Investigate Tax Liabilities and Carrying Costs
- Consult and execute the `analyze-tax-implications` skill using the lot's `parcel_apn`.
- Calculate monthly tax holding carrying costs: $\text{Annual Taxes} / 12$.

## 5. Synthesize Findings into Standard Memorandum
- Assemble all insights into the required memorandum structure, ensuring all core specifications, exact cost-per-acre derivation, and neighboring flood risk analyses are prominently highlighted.
```

### Step 6.2: Update `re_analyst/skills/analyze-flood-risk/SKILL.md`
Mandate multi-hop tool execution across adjacent parcels and comparative hydrological analysis:
```markdown
---
name: analyze-flood-risk
description: Exhaustively investigates flood zone designations, environmental constraints, and hydrological risks for the subject parcel and all neighboring/adjacent properties.
metadata:
  adk_additional_tools:
    - get_lot_data
---
# Analyze Flood Risk Skill

When evaluating environmental, flood, and geographic risks for a land acquisition:

## 1. Subject Parcel Flood Risk Evaluation
- Inspect the `flood_zone` field from the subject lot's data returned by `get_lot_data`.
- Explicitly identify the exact FEMA flood zone designation (e.g., Zone AE, Zone VE, Zone X) and risk category.
- Detail specific structural, construction, and insurance implications (BFE compliance, elevated foundations, pilings, fill dirt, hydrostatic vents, mandatory flood insurance).

## 2. Exhaustive Neighboring & Adjacent Property Flood Investigation
- Inspect the `adjacent_parcels` list in the subject parcel's property data.
- For **EVERY** parcel listed in `adjacent_parcels`, call the `get_lot_data` tool with its parcel ID (e.g., `get_lot_data("LOT-8471")`).
- For each neighboring parcel, retrieve and record:
  - Exact parcel ID
  - Exact FEMA flood zone classification
  - Topography and slope grade

## 3. Critical Comparative Hydrological and Drainage Impact Analysis
- Perform a comprehensive comparative hydrological analysis evaluating how neighboring properties impact the subject parcel:
  - **Drainage & Runoff Interaction**: Analyze how stormwater runoff flows between adjacent parcels and the subject parcel.
  - **Spillover & Hazard Risks**: If neighboring parcels are in high-hazard flood zones (Zone AE or Zone VE) while the subject lot is in Zone X, evaluate the severe risk of localized backflow or sheet runoff.
  - **Shared Watershed & Retention Requirements**: Analyze on-site civil engineering needs (detention basins, drainage swales, grading modifications, retaining walls).
  - **Development Feasibility Impact**: Conclude on the overall impact of neighboring hydrological conditions on site preparation CapEx and construction feasibility.

## 4. Final Memorandum Reporting Requirements
In the final memorandum under `## Risk Assessment`:
- Explicitly state the subject lot's FEMA flood zone classification.
- Create a dedicated subsection: `### Neighboring Property Flood and Hydrological Risk Analysis`.
- Present a clear breakdown or table of ALL adjacent parcels with their exact IDs, FEMA flood zones, and topography.
- Provide in-depth critical commentary analyzing runoff, drainage patterns, and shared hydrological risks.
```

### Step 6.3: Reinforce System Instructions in `re_analyst/agent.py`
Update `SYSTEM_INSTRUCTION` in `re_analyst/agent.py` to align memorandum structure requirements with the rubrics.

---

## 7. Task 5: Re-Evaluating the Optimized Agent (`hillclimb_2`)

### Step 7.1: Run Hill Climbing Evaluation
Execute the runner again:
```bash
python3 -m eval_harness.run_hillclimb
```

### Step 7.2: Verify Optimized Results
```text
=========================================
📊 Hill Climbing Results: hillclimb_2
=========================================
 • cost-per-acre             Mean Score: 5.0000
 • neighboring-flood-risk    Mean Score: 4.6000
=========================================
```

### Step 7.3: Review Passing Explanations
Verify that individual pass scores achieve 5.0:
```bash
python3 -m eval_harness.explain_criteria_results \
   --run_geap_eval_out runs/hillclimb_2/geap_calls_and_responses_hillclimb_2.json \
   --criterion neighboring-flood-risk \
   --max_score_to_show 4.0
```
9 out of 10 parcels achieved a perfect 5.0 score, bringing the mean to **`4.6000`**, while `cost-per-acre` achieved **`5.0000`** (10/10 perfect scores).

### Step 7.4: Verification & Completion
Click **Check my progress** in the lab interface to record completion of the evaluation milestone.
