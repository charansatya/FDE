# Day 3: Vertex AI GenAI Evaluation Service & ADK Agent Hill Climbing

This directory contains the complete codebase, evaluation harness, ADK 2.0 agent, datasets, and operational artifacts for **Day 3: GenAI Autorating, Statistical Reliability Analysis, and Closed-Loop Agent Optimization**.

---

## Documentation Index

| Document | Description |
| :--- | :--- |
| [**Architectural Design (`docs/ARCHITECTURE.md`)**](docs/ARCHITECTURE.md) | End-to-end evaluation architecture, ADK 2.0 dynamic `SkillToolset` topology, mathematical formulations for Krippendorff's Alpha ($\alpha$) and pairwise agreement, and the closed-loop hill climbing state machine. |
| [**Step-by-Step Lab Manual (`docs/LAB_MANUAL.md`)**](docs/LAB_MANUAL.md) | Hands-on walkthrough covering Task 1 through Task 5: multi-pass agreement analysis ($k=12$), baseline hill climbing (`1.40` and `1.10`), judge failure rationale dissection, skill engineering, and verified optimization (`5.00` and `4.60`). |
| [**Operational Runbook & Playbook (`docs/RUNBOOK_AND_PLAYBOOK.md`)**](docs/RUNBOOK_AND_PLAYBOOK.md) | Standard Operating Procedures (SOPs), execution command reference, and incident response playbooks for Vertex AI API rate limits, rubric ambiguity, and score regressions. |

---

## Directory Structure

```text
day-3/
├── README.md                          # Overview & navigation
├── requirements.txt                   # Python dependencies (google-adk, vertexai, pandas, tabulate)
├── .env.example                       # GCP project & model configuration template
├── best_criteria_submission.txt       # Selected high-agreement autorater criteria
├── docs/                              # Comprehensive architectural, manual & playbook docs
│   ├── ARCHITECTURE.md                # System topology & statistical formulations
│   ├── LAB_MANUAL.md                  # Step-by-step implementation guide
│   └── RUNBOOK_AND_PLAYBOOK.md        # SOPs, command matrix, and troubleshooting playbook
├── eval_harness/                      # Evaluation harness & analysis engines
│   ├── all_criteria_analysis.py       # Global statistical summary (Mean, SD, Krippendorff's Alpha)
│   ├── single_criterion_analysis.py   # In-depth per-criterion variance breakdown
│   ├── explain_criteria_results.py    # Dissects Gemini judge chain-of-thought rationales
│   ├── run_hillclimb.py               # Automated single-pass hill climbing runner
│   ├── run_geap_eval.py               # Direct Vertex AI GEAP batch evaluation runner
│   ├── metrics_calc.py                # Mathematical metrics engine
│   ├── create_re_agent_evalset.py     # Generates ADK EvalSet conversation traces
│   ├── rubrics.json                   # 19 custom evaluation rubrics with 5-point Likert scales
│   └── hillclimb_lots.txt             # 10 target edge-case real estate parcels
├── re_analyst/                        # ADK 2.0 Real Estate Opportunity Analyst Agent
│   ├── agent.py                       # Root agent, model client, and SkillToolset
│   ├── skills/                        # Modular investigation skills
│   │   ├── analyze-opportunity/       # Parcel acquisition & cost-per-acre derivation
│   │   ├── analyze-flood-risk/        # Multi-hop adjacent parcel inspection & hydrology
│   │   └── analyze-tax-implications/  # Assessor valuation & monthly holding cost
│   └── tools/                         # Native ADK FunctionTools
│       ├── lot_tool.py                # County records retrieval (lot attributes & adjacent parcels)
│       └── tax_tool.py                # Assessor property tax liability retrieval
├── tools_data/                        # Enterprise mock data stores
│   ├── lots_database.json             # County parcel database (1,900+ lines of lot attributes)
│   └── tax_database.json              # County tax assessor database
└── runs/                              # Versioned evaluation outputs
    ├── baseline/                      # Initial unoptimized benchmarks
    ├── hillclimb_1/                   # First evaluation run (cost-per-acre: 1.40, flood-risk: 1.10)
    ├── hillclimb_2/                   # Optimized run (cost-per-acre: 5.00, flood-risk: 4.60)
    └── geap_calls_and_responses_for_analysis.json  # 12-pass historical evaluation data
```

---

## Evaluation Benchmark Summary

| Evaluation Metric | Baseline (`hillclimb_1`) | Optimized (`hillclimb_2`) | Target | Status |
| :--- | :---: | :---: | :---: | :---: |
| **`cost-per-acre`** | `1.4000` | **`5.0000`** | > 4.0 | Passed |
| **`neighboring-flood-risk`** | `1.1000` | **`4.6000`** | > 4.0 | Passed |
