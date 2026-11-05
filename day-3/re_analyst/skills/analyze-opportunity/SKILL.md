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
