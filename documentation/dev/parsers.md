# Document Parsers

Source: `utils/parsers/`

The parser subsystem extracts structured data from night audit PDF and Excel reports,
which is then used to auto-fill the RJ workbook.

---

## Architecture

All parsers inherit from `BaseParser` (abstract base class) and follow a three-step pattern:

1. **parse()** -- Extract raw data from file bytes into `self.extracted_data`
2. **validate()** -- Check data integrity, populate `validation_errors` and `validation_warnings`
3. **get_result()** -- Return a standardized result dict with `success`, `data`, `field_mappings`, `confidence`, `errors`, `warnings`

Each parser also defines `FIELD_MAPPINGS` (field name to RJ cell reference) and exposes
`get_fillable_data()` which returns `{cell_ref: value}` ready for Excel writing.

### ParserFactory

`ParserFactory` in `utils/parsers/__init__.py` is the single entry point for creating parsers.

```python
ParserFactory.create(doc_type, file_bytes, filename=None, **kwargs)
```

**Dispatch table** (`PARSERS` dict):

| `doc_type` key | Parser Class | Accepted Extensions |
|---|---|---|
| `daily_revenue` | `DailyRevenueParser` | `.pdf` |
| `advance_deposit` | `AdvanceDepositParser` | `.pdf` |
| `freedompay` | `FreedomPayParser` | `.xls`, `.xlsx` |
| `hp_excel` | `HPExcelParser` | `.xls`, `.xlsx`, `.xlsm` |
| `ar_summary` | `ARSummaryParser` | `.pdf` |
| `sales_journal` | `SalesJournalParser` | `.rtf`, `.txt` |
| `sd_deposit` | `SDParser` | `.xls`, `.xlsx` |
| `market_segment` | `MarketSegmentParser` | `.pdf` |
| `cashier_summary` | `CashierSummaryParser` | `.pdf`, `.txt` |
| `transaction_summary` | `TransactionSummaryParser` | `.xlsx` |
| `recap_text` | `RecapTextParser` | `.txt` |

**Auto-detection**: `ParserFactory.detect_type(filename)` matches filename substrings
(e.g. `daily_rev`, `dlyrev`, `freedompay`, `cshsum`) to parser types for ZIP upload dispatch.

---

## Parser Details

### DailyRevenueParser

- **Input**: Daily Revenue PDF (7-page report from GEAC/UX PMS, `dlyrev`)
- **Library**: pdfplumber
- **Extraction**: Revenue departments (pages 1-2), non-revenue/taxes (pages 2-5), settlements (pages 5-6), deposits (page 6), balance (page 7)
- **Output fields**: `revenue.*`, `non_revenue.*`, `settlements.*`, `deposits_received.*`, `advance_deposits.*`, `balance.*`, `rj_mapping.geac_ux.*`, `rj_mapping.jour.*`
- **Target sheets**: Jour (via JourMapper), GEAC/UX
- **Key patterns**: `_get_today(text, label)` extracts first decimal number after a label; handles trailing `-` for negatives (e.g. `92589.85-` = -92589.85)

### AdvanceDepositParser

- **Input**: Advance Deposit Balance Sheet PDF from LightSpeed
- **Target sheet**: geac_ux (Row 44)
- **FIELD_MAPPINGS**: `adv_deposit` -> `B44`, `adv_deposit_applied` -> `J44`
- **Key patterns**: Regex search for "ending balance", "deposit on hand", "deposits applied"
- **Confidence**: 0.85 if deposit found, 0.5 for balance_forward only

### ARSummaryParser

- **Input**: AR Summary PDF (`arsum`) from GEAC/UX PMS
- **Target sheet**: geac_ux
- **FIELD_MAPPINGS**: `ar_previous_balance` -> `B6`, `ar_end_of_day` -> `B7`, `ar_transfers` -> `B8`
- **Key patterns**: Handles reversed (right-to-left) PDF text. Auto-detects orientation with `_find_value()` (tries forward then backward search). Validates balance equation: previous + transfers + adjustments + invoices + payments + cc_charges + service = eod.

### FreedomPayParser

- **Input**: FreedomPay/Fusebox Excel export, OR auto-fill mode from Daily Revenue card totals
- **Target sheets**: geac_ux (Row 6 Daily Cash Out, Row 12 Daily Revenue), transelect (fusebox rows B21-B24)
- **Dual mode**: `mode='file'` parses actual Excel; `mode='autofill'` copies DR card totals directly (since FreedomPay = DR, variance should be $0)
- **Extra methods**: `get_geac_fillable()`, `get_transelect_fillable()`, `get_daily_revenue_fillable()`

### HPExcelParser

- **Input**: HP-ADMIN Excel file (Honor Paid / comped meals tracking)
- **Target sheet**: jour (HP deduction columns)
- **Constructor**: Accepts `day=N` kwarg for day-specific deductions
- **Sheets parsed**: `mensuel` (monthly totals), `donnees` (daily per-transaction data)
- **Output**: `jour_deductions` dict mapping jour column indices to deduction amounts
- **Area-product mapping** (`AREA_PRODUCT_TO_JOUR`): Maps (department, product) tuples to jour column indices. Example: `('Piazza', 'nourriture')` -> col 9, `('Tabagie', 'tabagie')` -> col 35
- **Tips**: Tracks `bq_tips` (paiement code "14 - Administration" -> jour col 68) and `br_tips` (code "15 - Promotion" -> jour col 69)

### SalesJournalParser

- **Input**: Sales Journal RTF/TXT from Positouch/LightSpeed POS
- **Target sheets**: Recap, TransElect, HP, Jour
- **Extraction**: Department revenues (Piazza, Banquet, Chambres, Spesa, etc.), taxes (TPS/TVQ), payment methods (comptant, visa, mc, amex, interac), adjustments (hotel_promotion, forfait, empl_30)
- **Sub-item standardization**: Maps POS names like `alcool`->`boisson`, `biere`->`bieres`, `non_alcool`->`mineraux` to match jour column expectations
- **RTF handling**: Strips RTF markup before parsing; determines debit vs credit by trailing-space heuristic

### SDParser

- **Input**: SD (Suivi des Depots) Excel file with 31 daily sheets
- **Target sheet**: SetD
- **Constructor**: Accepts `day=N` kwarg
- **Employee matching**: 4-strategy fuzzy matching (exact, last name, first name, substring) against `SETD_PERSONNEL_COLUMNS` (135 personnel)
- **Output**: `setd_fillable` dict `{col_letter: variance_amount}` ready for SetD writing

### MarketSegmentParser

- **Input**: Market Segment Production PDF (`mktsegprd`) from Galaxy Lightspeed
- **Target sheet**: DBRS
- **Extraction**: TODAY and MTD totals (guests, rooms, revenue, avg rate, occupancy), segment breakdown by category (transient T-codes, group G-codes, contract W-codes)

### CashierSummaryParser

- **Input**: Daily Cashout (`cshsum`) or Cashier Cashout (`cshout`) PDF
- **Target sheet**: GEAC (cashout data), Recap (cash drop)
- **Card codes**: AX=Amex, VI=Visa, MC=MasterCard, DB=Facture, IN=Interac, DI=Discover
- **Department allowances**: Extracts per-department charges and allowances from Hotel Dpt Description table; uses "All Cashiers" grand total block when available to avoid double-counting

### TransactionSummaryParser

- **Input**: FreedomPay TransactionSummarybyCardType Excel (`.xlsx`)
- **Target sheet**: Transelect (reception section)
- **Extraction**: Per card type totals from subtotal rows (`Total:Amex - Credit`, etc.) and grand total from `YULLS PMS` row
- **FIELD_MAPPINGS**: `amex_total` -> `transelect_rec_amex`, etc.

### RecapTextParser

- **Input**: Server Recap TXT file (Sales Journal Report per server)
- **Target sheets**: Recap (grand totals), Transelect Restaurant (per-server breakdown)
- **Extraction**: Per-server payment breakdown (VISA, MC, AMEX, INTERAC, cash) aggregated to grand totals

---

## Data Flow: Parser to JourMapper

The `fill-jour` endpoint orchestrates the full pipeline:

1. Frontend sends `parsed_data` dict containing results from multiple parsers (keyed by `doc_type`)
2. `JourMapper` is instantiated with `daily_rev_data`, `sales_journal_data`, `ar_summary_data`, `hp_data`, `manual_values`, `adjustments`
3. `JourMapper.compute_all()` iterates over `DAILY_REV_TO_JOUR` mapping, resolves each field using dot-path notation (e.g. `revenue.chambres.total`), applies operations (`direct`, `subtract`, `accumulate`, `formula`)
4. Returns `{column_index: value}` dict
5. `RJFiller.fill_jour_day(day, jour_values)` writes to the jour sheet at the correct row

---

## Adding a New Parser

1. Create `utils/parsers/my_parser.py` extending `BaseParser`
2. Define `FIELD_MAPPINGS` class attribute
3. Implement `parse()` and `validate()`
4. Register in `ParserFactory.PARSERS` and `ACCEPTED_EXTENSIONS` in `__init__.py`
5. Add `FILENAME_PATTERNS` entry for auto-detection (ZIP upload)
6. Add type info in `ParserFactory.get_type_info()` with `target_sheet`
