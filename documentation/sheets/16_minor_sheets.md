# Minor Tracking Sheets

## Overview

Six small-to-medium sheets in the RJ workbook handle specialized tracking for ancillary hotel services: spa/massage, coat check, music licensing (SOCAN and Re:Sonne), in-room entertainment (Sonifi), and internet service (Datavalet). These sheets are used primarily for monthly reconciliation and third-party reporting rather than daily audit workflow.

None of these sheets are currently integrated into the web application.

---

## 1. Massage

### Sheet Details

| Property    | Value                                |
|-------------|--------------------------------------|
| Excel Sheet | `Massage`                            |
| Dimensions  | 36 rows x 9 cols                     |
| Row 0       | Month identifier (date serial 46014) |
| Row 1       | Headers                              |
| Rows 2-32   | Daily values (days 1-31)             |

### Column Reference

| Col | Header             | Description                                  |
|-----|--------------------|----------------------------------------------|
| 0   | JOUR               | Day number                                   |
| 1   | R/J                | Revenue from daily report (RJ)               |
| 2   | SANS TAXES         | Revenue excluding taxes                      |
| 3   | FACTURE            | Invoice total                                |
| 4   | numero de facture  | Invoice number                               |
| 5   | MASSAGE sans taxe  | Massage revenue before tax                   |
| 6   | total              | Total amount                                 |
| 7   | (unnamed)          | --                                           |
| 8   | VARIANCE           | Difference between RJ and invoice amounts    |

### Sample Data

Daily massage revenue entries with invoice tracking. The VARIANCE column flags discrepancies between the RJ-reported amount and the actual invoice, enabling monthly reconciliation.

### Data Flow & Integration

```
Daily RJ (massage revenue line) ──> Massage sheet (col 1: R/J)
Spa invoices ──────────────────────> Massage sheet (cols 3-6: invoice detail)
                                         │
                                         └── VARIANCE = R/J - Invoice (col 8)
```

### Analytics Potential

- Monthly spa revenue reconciliation.
- Variance analysis to catch missed or duplicate charges.
- Trend analysis of spa utilization across days of the week.

---

## 2. Vestiaire#

### Sheet Details

| Property    | Value                          |
|-------------|--------------------------------|
| Excel Sheet | `Vestiaire#`                   |
| Dimensions  | 45 rows x 7 cols               |
| Structure   | Metadata and contact info      |

### Column Reference

Contains intervention records and contact information (e.g., Francois Dubuc, address details). This sheet tracks coat check / wardrobe service charges or inventory rather than daily revenue.

### Data Flow & Integration

Standalone reference sheet. Not connected to daily audit calculations.

### Analytics Potential

- Limited. Primarily a reference/contact sheet for the coat check service provider.

---

## 3. SOCAN

### Sheet Details

| Property    | Value                                          |
|-------------|------------------------------------------------|
| Excel Sheet | `SOCAN`                                        |
| Dimensions  | 57 rows x 13 cols                              |
| Purpose     | Music royalty tracking for SOCAN                |
| Account     | 040445                                         |
| Tariff      | Tarif 8 (receptions)                           |
| Reporting   | Monthly, to SOCAN Toronto office               |

### Column Reference

Tracks music licensing fees owed to the Society of Composers, Authors and Music Publishers of Canada (SOCAN) based on hotel events, banquet activity, and room counts. The tariff 8 structure applies to receptions and events.

### Sample Data

Monthly fee calculations based on event counts and room nights, reported under account 040445.

### Data Flow & Integration

```
Banquet/event data ──> SOCAN sheet ──> Monthly royalty report to SOCAN
```

### Analytics Potential

- Monthly music licensing cost tracking.
- Correlation between event volume and royalty obligations.

---

## 4. resonne

### Sheet Details

| Property    | Value                                          |
|-------------|------------------------------------------------|
| Excel Sheet | `resonne`                                      |
| Dimensions  | 57 rows x 13 cols                              |
| Purpose     | Music royalty tracking for Re:Sonne             |
| Tariff      | Tarif 5B (receptions)                          |
| Reporting   | Monthly, to Re:Sonne Toronto office (Bay St)   |

### Column Reference

Mirrors the SOCAN sheet structure but tracks fees owed to Re:Sonne, a separate music licensing organization. Uses tariff 5B for receptions.

### Data Flow & Integration

```
Banquet/event data ──> resonne sheet ──> Monthly royalty report to Re:Sonne
```

### Analytics Potential

- Same as SOCAN: licensing cost tracking and event-volume correlation.
- Combined SOCAN + Re:Sonne gives total music royalty obligations.

---

## 5. Sonifi

### Sheet Details

| Property    | Value                                          |
|-------------|------------------------------------------------|
| Excel Sheet | `Sonifi`                                       |
| Dimensions  | 65 rows x 94 cols                              |
| Purpose     | In-room entertainment revenue reconciliation   |
| Header      | RECONCILIATION REVENUE                         |

### Column Reference

| Col   | Header    | Description                          |
|-------|-----------|--------------------------------------|
| 0     | DATE      | Day of month                         |
| 1-93  | Price pts | Individual sale price columns        |

Known price points include: $8.95, $9.95, $10.95, $10.99, $11.95, $12.95, $22.99, $32.99. The 94 columns cover many price tiers and content categories across the month.

### Sample Data

Each row represents a day, with counts or revenue at each price point for in-room movies and entertainment purchases.

### Data Flow & Integration

```
Sonifi system export ──> Sonifi sheet ──> Revenue reconciliation
                                              │
                                              └── Feeds into jour sheet (Location Film line)
```

### Analytics Potential

- Revenue by content price tier.
- Daily viewing patterns and peak entertainment days.
- Average revenue per occupied room from entertainment.

---

## 6. Internet

### Sheet Details

| Property    | Value                                          |
|-------------|------------------------------------------------|
| Excel Sheet | `Internet`                                     |
| Dimensions  | 41 rows x 94 cols                              |
| Purpose     | Internet service revenue via Datavalet          |
| Hotel       | Groupe Hotelier Grand Chateau / Sheraton Laval  |
| Provider    | Datavalet                                       |

### Column Reference

Similar to the Sonifi sheet: 94 columns covering daily breakdown by service tier and price point for WiFi/internet access sold to guests.

### Data Flow & Integration

```
Datavalet system export ──> Internet sheet ──> Revenue reconciliation
                                                    │
                                                    └── Feeds into jour sheet (Internet line)
                                                    └── Feeds into AD sheet (col 31: Internet)
```

### Analytics Potential

- Revenue by internet service tier.
- Daily internet usage patterns.
- Penetration rate (internet purchases vs occupied rooms).
