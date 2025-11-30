# Excel Integration - TODO

This document tracks what Excel files need to be provided for Phase 3 implementation.

## Required Excel Files

Please provide the following Excel files/templates for integration:

### 1. Cash Drawer Balance Sheet
- [ ] Template file
- [ ] Column structure documentation
- [ ] Formulas used
- [ ] Expected input/output fields

### 2. Revenue Reports (if applicable)
- [ ] Daily revenue template
- [ ] What data comes from Lightspeed
- [ ] What calculations are performed

### 3. Other Balance Sheets
- [ ] List any other Excel files used during night audit
- [ ] Document their purpose and structure

## Integration Goals

When Excel files are provided, the webapp will be able to:

1. **Data Entry Forms** - Enter data directly in the webapp instead of Excel
2. **Auto-calculations** - Perform balance calculations automatically
3. **Validation** - Show color-coded feedback (green = balanced, red = discrepancy)
4. **Export** - Generate Excel files for records if needed
5. **History** - Track balances over time

## How to Provide Files

1. Place Excel templates in: `documentation/excel_templates/`
2. Note any password protection
3. Document which cells are inputs vs outputs
4. Explain any macros or complex formulas

---
*This document will be updated when Excel files are received.*
