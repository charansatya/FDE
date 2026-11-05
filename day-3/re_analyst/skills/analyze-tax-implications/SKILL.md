---
name: analyze-tax-implications
description: Investigates property tax holding costs and assessment records for a parcel, calculating monthly carrying costs.
metadata:
  adk_additional_tools:
    - get_tax_assessment_data
---
# Analyze Tax Implications Skill

When investigating financial carrying costs or tax implications for a lot:
1. Locate the `parcel_apn` from the lot property records.
2. Use the `get_tax_assessment_data` tool with that APN to retrieve official tax assessment details (assessed land value, assessed improvement value, official annual property taxes, payment status).
3. **Calculate Monthly Tax Holding Cost**:
   - Explicitly compute the exact monthly carrying cost:
     $$\text{Monthly Tax Carrying Cost} = \frac{\text{Official Annual Taxes}}{12}$$
   - Report both the annual tax liability and the monthly carrying cost figure ($/month).
   - Highlight the carrying cost implications for pre-construction and pre-development holding budgets.
4. Compare the official annual property tax liability against preliminary dataset estimates to identify variances and note whether a tax appeal is warranted.
