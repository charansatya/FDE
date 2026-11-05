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
- Explicitly identify the exact FEMA flood zone designation (e.g., Zone AE, Zone VE, Zone X) and risk category (e.g., Special Flood Hazard Area / High Risk vs. Minimal Risk).
- Detail specific structural, construction, and insurance implications:
  - For high-risk zones (Zone AE, Zone VE): Explain Base Flood Elevation (BFE) compliance, necessity of elevated vertical construction (e.g., pilings, stems, fill dirt, hydrostatic vents), and mandatory commercial flood insurance premiums.
  - For minimal-risk zones (Zone X): Note standard grade-level foundation suitability and lower insurance requirements.

## 2. Exhaustive Neighboring & Adjacent Property Flood Investigation
- Inspect the `adjacent_parcels` list in the subject parcel's property data.
- For **EVERY** parcel listed in `adjacent_parcels`, call the `get_lot_data` tool with its parcel ID (e.g., `get_lot_data("LOT-8471")`).
- For each neighboring parcel, retrieve and record:
  - Exact parcel ID (e.g., `LOT-8471`, `LOT-8473`)
  - Exact FEMA flood zone classification (e.g., Zone AE, Zone X, Zone VE)
  - Topography and slope grade (e.g., flat, moderate slope, steep slope)

## 3. Critical Comparative Hydrological and Drainage Impact Analysis
- Perform a comprehensive comparative hydrological analysis evaluating how neighboring properties impact the subject parcel:
  - **Drainage & Runoff Interaction**: Analyze how stormwater runoff, drainage patterns, or flood waters flow between adjacent parcels and the subject parcel based on relative topography/slope and flood classifications.
  - **Spillover & Hazard Risks**: If neighboring parcels are in high-hazard flood zones (Zone AE or Zone VE) while the subject lot is in Zone X, evaluate the severe risk of localized backflow, flood boundary migration, or sheet runoff compromising the subject lot. Conversely, if the subject parcel is high-risk, analyze how neighboring runoff could exacerbate water accumulation.
  - **Shared Watershed & Retention Requirements**: Analyze on-site civil engineering needs, such as dedicated stormwater detention basins, drainage swales, grading modifications, retaining walls, or drainage easements to mitigate runoff from adjacent properties.
  - **Development Feasibility Impact**: Conclude on the overall impact of neighboring hydrological conditions on the subject parcel's site preparation CapEx, grading plans, permitting requirements, and vertical construction feasibility.

## 4. Final Memorandum Reporting Requirements
In the final memorandum under `## Risk Assessment`:
- Explicitly state the subject lot's FEMA flood zone classification and associated structural/insurance implications.
- Create a dedicated subsection: `### Neighboring Property Flood and Hydrological Risk Analysis`.
- Present a clear breakdown or table of ALL adjacent parcels with their exact IDs, FEMA flood zones, and topography.
- Provide in-depth critical commentary analyzing runoff, drainage patterns, and shared hydrological risks, explaining exactly how neighboring flood conditions impact the subject parcel's development feasibility.
