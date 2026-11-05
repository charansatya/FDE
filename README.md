# FDE (Forward Deployed Engineering) Program Repository

Welcome to the comprehensive repository for the **Forward Deployed Engineering (FDE)** hands-on modules on Google Cloud Platform. This repository contains the complete source code, deployment configurations, evaluation harnesses, architectural documentation, and production runbooks for all laboratory exercises.

---

## 📁 Repository Directory Structure

```text
.
├── day-1/                         # Day 1: Multi-Agent Code Assistant & Microservices
│   ├── bq-agent/                  # BigQuery Autonomous Assistant Agent
│   ├── code-assistant/            # Lead Multi-Agent Orchestrator
│   ├── docs/                      # Architectural designs, sequence diagrams & guides
│   ├── github-agent/              # GitHub API Integration Agent
│   ├── salesforce-agent/          # Salesforce CRM Integration Agent
│   ├── stackexchange-agent/       # StackExchange API Agent
│   └── README.md                  # Day 1 Master Overview & Deployment Guide
│
├── day-3/                         # Day 3: LLM Autoraters & Agent Hill Climbing
│   ├── eval_harness/              # GEAP Evaluation Harness & Statistical Tools
│   ├── re_analyst/                # Real Estate Analyst Agent (ADK 2.0 / Gemini)
│   │   ├── skills/                # Modular Skill System (analyze-flood-risk, etc.)
│   │   └── tools/                 # Parcel Lookup & Valuation Tools
│   ├── tools_data/                # Synthetic Ground-Truth GIS Database (200 parcels)
│   ├── runs/                      # Versioned GEAP Evaluation Runs & Judge Rationales
│   ├── docs/                      # Production Documentation Suite
│   │   ├── ARCHITECTURE.md        # Mathematical Formulations & Component Topology
│   │   ├── LAB_MANUAL.md          # Step-by-Step Task Execution Manual
│   │   └── RUNBOOK_AND_PLAYBOOK.md# Production CLI SOPs & Incident Playbooks
│   ├── best_criteria_submission.txt # Top 5 Statistically Discriminative Autoraters
│   └── README.md                  # Day 3 Technical Guide & Benchmark Results
│
├── day 1 -> day-1                 # Symlink alias for space-delimited navigation
├── day 3 -> day-3                 # Symlink alias for space-delimited navigation
└── README.md                      # Unified Repository Index (This File)
```

---

## 🚀 Module Summaries

### [Day 1: Multi-Agent Systems & Enterprise Integrations](./day-1/)
Focuses on building, deploying, and orchestrating distributed multi-agent systems on Google Cloud Platform using Vertex AI Reasoning Engine, Cloud Run, and Kubernetes.
* **Core Technologies**: Python, FastAPI, Terraform, Google Cloud Run, GKE, Vertex AI, Agent-to-Agent (A2A) protocol.
* **Key Components**:
  * **Code Assistant Orchestrator**: Centrally coordinates developer queries, delegating tasks across specialized agents.
  * **Domain Agents**: BigQuery Agent, Salesforce CRM Agent, GitHub Agent, StackExchange Agent.
  * **Infrastructure as Code (IaC)**: Production Terraform modules for single-project and multi-project GCP environments.

---

### [Day 3: Autonomous Evaluation, LLM-as-a-Judge & Agent Hill Climbing](./day-3/)
Focuses on evaluating and iteratively improving AI agents through automated LLM judges, inter/intra-rater reliability analysis, and hill climbing loops.
* **Core Technologies**: Google Agent Development Kit (ADK 2.0), Gemini 2.5 Flash, GEAP (Gen AI Evaluation Platform), Krippendorff's Alpha ($\alpha$), Hill Climbing Optimization.
* **Key Components**:
  * **Real Estate Analyst Agent (`re_analyst`)**: Multi-hop agent conducting underwriting, risk assessment, and financial modeling on real estate parcels.
  * **Evaluation Harness (`eval_harness`)**: Automated evaluation pipeline computing intra-rater consistency across $k$-replications and orchestrating single-pass hill climbs.
  * **Production Documentation**:
    * 📘 [Lab Manual](./day-3/docs/LAB_MANUAL.md): Step-by-step walkthrough covering environment setup, baseline evaluations, autorater statistical selection, and agent optimization.
    * 📐 [System Architecture](./day-3/docs/ARCHITECTURE.md): Component topology, mathematical formulations of Krippendorff's Alpha, Mermaid sequence flows, and state machines.
    * 🛠️ [Runbook & Playbook](./day-3/docs/RUNBOOK_AND_PLAYBOOK.md): Operational standard operating procedures, CLI cheat sheets, and 5 incident troubleshooting workflows.

#### Hill Climbing Benchmark Results

| Metric Criterion | Target Threshold | Baseline (`hillclimb_1`) | Optimized (`hillclimb_2`) | Delta ($\Delta$) | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **`cost-per-acre`** | $> 4.00$ | 1.4000 | **5.0000** | **+3.6000 (+257%)** | ✅ **PASSED** |
| **`neighboring-flood-risk`** | $> 4.00$ | 1.1000 | **4.6000** | **+3.5000 (+318%)** | ✅ **PASSED** |

---

## 📖 Quick Links & Documentation Map

| Resource | Path | Description |
| :--- | :--- | :--- |
| **Day 1 Overview** | [`day-1/README.md`](./day-1/README.md) | Multi-agent architecture and deployment specifications |
| **Day 3 Overview** | [`day-3/README.md`](./day-3/README.md) | Agent evaluation, autorater rubrics, and optimization results |
| **Lab Manual** | [`day-3/docs/LAB_MANUAL.md`](./day-3/docs/LAB_MANUAL.md) | Comprehensive step-by-step laboratory execution guide |
| **Architecture Design** | [`day-3/docs/ARCHITECTURE.md`](./day-3/docs/ARCHITECTURE.md) | In-depth system diagrams, mathematical definitions, and interaction flows |
| **Runbook & Playbook** | [`day-3/docs/RUNBOOK_AND_PLAYBOOK.md`](./day-3/docs/RUNBOOK_AND_PLAYBOOK.md) | Production operations, debugging checklists, and triage scenarios |
| **Top 5 Criteria** | [`day-3/best_criteria_submission.txt`](./day-3/best_criteria_submission.txt) | Validated autorater metrics based on Krippendorff's Alpha |

---

## 🔒 Security & Best Practices
* **Credentials**: Never commit `.env` files, API keys, or Google Cloud credentials to Git. Always use `.env.example` templates and GCP Secret Manager.
* **Trace Isolation**: Traces and evaluation artifacts in `runs/` are git-tracked for reproducibility, while raw system credential caches are strictly ignored via `.gitignore`.
