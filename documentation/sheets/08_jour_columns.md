# Jour Sheet -- Complete 117 Column Reference

The Jour sheet is the central daily revenue ledger of the RJ workbook. It contains **233 rows x 117 columns** (A through DM, indices 0-116).

**Row layout:**
- Row 0 = blank
- Row 1 = headers
- Rows 2-32 = days 1-31

**Row formula:** `get_jour_row_for_day(day) = day + 1` (0-indexed). Day 1 is row 2, day 31 is row 32.

All monetary values are in CAD. Columns are populated from multiple source parsers: Daily Revenue report (7 pages), Sales Journal (POS), Transelect (cards), Recap (cash), and calculated formulas.

---

## Group 1: Opening & Balance (A-D, cols 0-3)

| Col | Letter | Label FR | Label EN | Source | Operation | Sign Handling | CRM Metric |
|-----|--------|----------|----------|--------|-----------|---------------|------------|
| 0 | A | Jour | Day Number | Static | day number | -- | -- |
| 1 | B | Solde d'ouverture | Opening Balance | Excel formula | carried forward | keep_sign | `DailyJourMetrics.opening_balance` |
| 2 | C | Diff. Caisse | Cash Difference | Excel formula | calculated | keep_sign | `DailyJourMetrics.cash_difference` |
| 3 | D | Nouveau Solde (negatif) | New Balance (negative) | PAGE 7: `balance.new_balance` | formula: `-(balance.new_balance) - deposits.deposit_on_hand` | negate_result | `DailyJourMetrics.closing_balance` |

Notes:
- Col D is the closing balance. The sign is inverted from the source (always stored negative), then Deposit on Hand from the Advance Deposit Balance Sheet is subtracted.

---

## Group 2: Cafe Link / Pause Spesa (E-I, cols 4-8)

| Col | Letter | Label FR | Label EN | Source | Operation | Sign Handling | CRM Metric |
|-----|--------|----------|----------|--------|-----------|---------------|------------|
| 4 | E | Nou_Link | Cafe Link Nourriture | SALES JOURNAL: `sales_journal.cafe_link.nourriture` | direct | keep_sign | `DailyJourMetrics.cafe_link_total` (summed) |
| 5 | F | Boi_Link | Cafe Link Boisson | SALES JOURNAL: `sales_journal.cafe_link.boisson` | direct | keep_sign | (part of cafe_link_total) |
| 6 | G | Bie_Link | Cafe Link Bieres | SALES JOURNAL: `sales_journal.cafe_link.bieres` | direct | keep_sign | (part of cafe_link_total) |
| 7 | H | Min_Link | Cafe Link Mineraux | SALES JOURNAL: `sales_journal.cafe_link.mineraux` | direct | keep_sign | (part of cafe_link_total) |
| 8 | I | Vin_Link | Cafe Link Vins | SALES JOURNAL: `sales_journal.cafe_link.vins` | direct | keep_sign | (part of cafe_link_total) |

---

## Group 3: Piazza / Cupola (J-N, cols 9-13)

| Col | Letter | Label FR | Label EN | Source | Operation | Sign Handling | CRM Metric |
|-----|--------|----------|----------|--------|-----------|---------------|------------|
| 9 | J | Nou_piazza | Piazza Nourriture | SALES JOURNAL: `sales_journal.piazza.nourriture` | direct (minus HP deductions & adjustments) | keep_sign | `DailyJourMetrics.piazza_total` (summed) |
| 10 | K | Boi_piazza | Piazza Alcool (Boisson) | SALES JOURNAL: `sales_journal.piazza.boisson` | direct | keep_sign | (part of piazza_total) |
| 11 | L | Bie_piazza | Piazza Bieres | SALES JOURNAL: `sales_journal.piazza.bieres` | direct | keep_sign | (part of piazza_total) |
| 12 | M | Min_piazza | Piazza Non Alcool Bar (Mineraux) | SALES JOURNAL: `sales_journal.piazza.mineraux` | direct | keep_sign | (part of piazza_total) |
| 13 | N | Vin_piazza | Piazza Vins | SALES JOURNAL: `sales_journal.piazza.vins` | direct | keep_sign | (part of piazza_total) |

---

## Group 4: Marche La Spesa (O-S, cols 14-18)

| Col | Letter | Label FR | Label EN | Source | Operation | Sign Handling | CRM Metric |
|-----|--------|----------|----------|--------|-----------|---------------|------------|
| 14 | O | Nou_mar | Marche La Spesa Nourriture | SALES JOURNAL: `sales_journal.spesa.nourriture` | direct | keep_sign | `DailyJourMetrics.spesa_total` (summed) |
| 15 | P | Boi_mar | Marche La Spesa Boisson | SALES JOURNAL: `sales_journal.spesa.boisson` | direct | keep_sign | (part of spesa_total) |
| 16 | Q | Bie_mar | Marche La Spesa Bieres | SALES JOURNAL: `sales_journal.spesa.bieres` | direct | keep_sign | (part of spesa_total) |
| 17 | R | Min_mar | Marche La Spesa Mineraux | SALES JOURNAL: `sales_journal.spesa.mineraux` | direct | keep_sign | (part of spesa_total) |
| 18 | S | Vin_mar | Marche La Spesa Vins | SALES JOURNAL: `sales_journal.spesa.vins` | direct | keep_sign | (part of spesa_total) |

---

## Group 5: Service aux Chambres / Room Service (T-X, cols 19-23)

| Col | Letter | Label FR | Label EN | Source | Operation | Sign Handling | CRM Metric |
|-----|--------|----------|----------|--------|-----------|---------------|------------|
| 19 | T | Nou_schbr | Service Chambres Nourriture | SALES JOURNAL: `sales_journal.chambres.nourriture` | direct | keep_sign | `DailyJourMetrics.room_svc_total` (summed) |
| 20 | U | Boi_schbr | Service Chambres Boisson | SALES JOURNAL: `sales_journal.chambres.boisson` | direct | keep_sign | (part of room_svc_total) |
| 21 | V | Bie_schbr | Service Chambres Bieres | SALES JOURNAL: `sales_journal.chambres.bieres` | direct | keep_sign | (part of room_svc_total) |
| 22 | W | Min_schbr | Service Chambres Mineraux | SALES JOURNAL: `sales_journal.chambres.mineraux` | direct | keep_sign | (part of room_svc_total) |
| 23 | X | Vin_schbr | Service Chambres Vins | SALES JOURNAL: `sales_journal.chambres.vins` | direct | keep_sign | (part of room_svc_total) |

---

## Group 6: Banquet (Y-AC, cols 24-28)

| Col | Letter | Label FR | Label EN | Source | Operation | Sign Handling | CRM Metric |
|-----|--------|----------|----------|--------|-----------|---------------|------------|
| 24 | Y | Nou_bqt | Banquet Nourriture | SALES JOURNAL: `sales_journal.banquet.nourriture` | direct | keep_sign | `DailyJourMetrics.banquet_total` (summed) |
| 25 | Z | Boi_bqt | Banquet Boisson | SALES JOURNAL: `sales_journal.banquet.boisson` | direct | keep_sign | (part of banquet_total) |
| 26 | AA | Biere Banquet | Banquet Bieres | SALES JOURNAL: `sales_journal.banquet.bieres` | direct | keep_sign | (part of banquet_total) |
| 27 | AB | Min_bqt | Banquet Mineraux | SALES JOURNAL: `sales_journal.banquet.mineraux` | direct | keep_sign | (part of banquet_total) |
| 28 | AC | Vin_bqt | Banquet Vins | SALES JOURNAL: `sales_journal.banquet.vins` | direct | keep_sign | (part of banquet_total) |

---

## Group 7: Adjustments & Other Revenue (AD-AJ, cols 29-35)

| Col | Letter | Label FR | Label EN | Source | Operation | Sign Handling | CRM Metric |
|-----|--------|----------|----------|--------|-----------|---------------|------------|
| 29 | AD | Pourboires | Gratuities/Tips | SALES JOURNAL: `sales_journal.adjustments.pourboire_charge` | direct | keep_sign | `DailyJourMetrics.tips_total` |
| 30 | AE | Equipement | Equipment | analytics.py: `equipement` | -- | keep_sign | (part of other_revenue) |
| 31 | AF | Divers | Miscellaneous | analytics.py: `divers` | -- | keep_sign | (part of other_revenue) |
| 32 | AG | Location Salle Forfait | Banquet Room Rental (Forfait) | PAGE 2: `revenue.autres_revenus.location_salle_forfait` | direct | keep_sign | (part of other_revenue) |
| 33 | AH | SOCAN | SOCAN Royalties | analytics.py: `socan` | -- | keep_sign | -- |
| 34 | AI | Re:sonne | Re:sonne Royalties | analytics.py: `resonne` | -- | keep_sign | -- |
| 35 | AJ | Tabagie | Tobacco/Convenience | SALES JOURNAL: `sales_journal.spesa.tabagie` | direct | keep_sign | `DailyJourMetrics.tabagie_total` |

---

## Group 8: Revenue Departments (AK-AO, cols 36-40)

| Col | Letter | Label FR | Label EN | Source | Operation | Sign Handling | CRM Metric |
|-----|--------|----------|----------|--------|-----------|---------------|------------|
| 36 | AK | Chambres (- Club Lounge) | Rooms (minus Club Lounge) | PAGE 1: `revenue.chambres.total` - `non_revenue.club_lounge.total` | subtract | keep_sign | `DailyJourMetrics.room_revenue` -- KEY column for ADR, RevPAR, Occupancy |
| 37 | AL | Telephone Local | Telephone Local | PAGE 1: `revenue.telephones.local` | direct | keep_sign | -- |
| 38 | AM | Telephone Interurbain | Telephone Long-Distance | PAGE 1: `revenue.telephones.interurbain` | direct | keep_sign | -- |
| 39 | AN | Telephones Publics | Public Telephones | PAGE 1: `revenue.telephones.publics` | direct | keep_sign | -- |
| 40 | AO | Nettoyeur - Dry Cleaning | Dry Cleaning | PAGE 2: `revenue.autres_revenus.nettoyeur` | direct | keep_sign | -- |

Notes:
- Col AK (Chambres) is the single most important revenue column. It feeds ADR, RevPAR, TRevPAR, and all room revenue KPIs. Club Lounge revenue is subtracted at source.

---

## Group 9: Autres Revenus (AP-AW, cols 41-48)

| Col | Letter | Label FR | Label EN | Source | Operation | Sign Handling | CRM Metric |
|-----|--------|----------|----------|--------|-----------|---------------|------------|
| 41 | AP | MACHINE DISTRIBUTRICE | Vending Machine | PAGE 2: `revenue.autres_revenus.machine_distributrice` | direct | keep_sign | -- |
| 42 | AQ | St-Martin Elec | St-Martin Electrical | analytics.py: `st_martin_elec` | Reserved/Excel | -- | -- |
| 43 | AR | Buanderette | Launderette | analytics.py: `buanderette` | Reserved/Excel | -- | -- |
| 44 | AS | Autres Grand Livre Total | Other General Ledger Total | PAGE 2: `revenue.comptabilite.autres_grand_livre` | direct | keep_sign (can be negative) | -- |
| 45 | AT | Sonifi | Sonifi In-Room Entertainment | PAGE 2: `revenue.autres_revenus.sonifi` | direct | keep_sign | -- |
| 46 | AU | Lit Pliant | Rollaway Bed | PAGE 2: `revenue.autres_revenus.lit_pliant` | direct | keep_sign | -- |
| 47 | AV | Location De Boutique | Boutique Rental | PAGE 2: `revenue.autres_revenus.location_boutique` | direct | keep_sign | -- |
| 48 | AW | Internet | Internet Service | PAGE 2: `revenue.internet.total` | direct | keep_sign | -- |

---

## Group 10: Taxes & Non-Revenue (AX-BH, cols 49-59)

| Col | Letter | Label FR | Label EN | Source | Operation | Sign Handling | CRM Metric |
|-----|--------|----------|----------|--------|-----------|---------------|------------|
| 49 | AX | TVQ Accumulator | TVQ (QST) Provincial Tax | PAGES 3,4,5 + SJ: 10 TVQ sources accumulated | accumulate (sum_all) | keep_sign | `DailyJourMetrics.tvq_total` |
| 50 | AY | TPS Accumulator | TPS (GST) Federal Tax | PAGES 2,3,4,5 + SJ: 10 TPS sources accumulated | accumulate (sum_all) | keep_sign | `DailyJourMetrics.tps_total` |
| 51 | AZ | Taxe Hebergement | Accommodation Tax | PAGE 2: `non_revenue.chambres_tax.taxe_hebergement` | direct | keep_sign | `DailyJourMetrics.tvh_total` |
| 52 | BA | Massage | Massage/Spa | PAGE 2: `revenue.autres_revenus.massage` | direct | keep_sign | -- |
| 53 | BB | Vestiaire | Coat Check | analytics.py: `vestiaire` | -- | keep_sign | -- |
| 54 | BC | Gift Card & Bon d'achat | Gift Card Accumulator | PAGES 2,6: `revenue.givex.total` + `settlements.bon_dachat` + `settlements.gift_card` + `settlements.bon_dachat_remanco` | accumulate | keep_sign | -- |
| 55 | BD | Fax / Photo | Fax/Photocopy | analytics.py: `fax_photo` | -- | keep_sign | -- |
| 56 | BE | Billet Promo | Promo Tickets | analytics.py: `billet_promo` | -- | keep_sign | -- |
| 57 | BF | Forfait / Club Lounge | Club Lounge & Forfait Calc | DERIVED: `derived.diff_forfait` | formula: `-forfait + club_lounge_value` | keep_sign | -- |
| 58 | BG | Fin des | End-of-period | analytics.py: `fin_des` | -- | keep_sign | -- |
| 59 | BH | Total Credit | Total Credit | analytics.py: `total_credit` | Excel formula | -- | -- |

**TVQ accumulator sources (col AX):**
1. `non_revenue.chambres_tax.tvq`
2. `non_revenue.telephones_tax.tvq_local`
3. `non_revenue.telephones_tax.tvq_interurbain`
4. `non_revenue.autres_tax.tvq_autres`
5. `non_revenue.internet_nonrev.tvq`
6. `non_revenue.restaurant_piazza.tvq`
7. `non_revenue.banquet.tvq`
8. `non_revenue.la_spesa.tvq`
9. `non_revenue.services_chambres.tvq`
10. `sales_journal.taxes.tvq`

**TPS accumulator sources (col AY):** Same structure as TVQ but with TPS fields.

---

## Group 11: Card Payments (BI-BN, cols 60-65)

Source: `calcul_carte` macro from Transelect row 37.

| Col | Letter | Label FR | Label EN | Source | Operation | Sign Handling | CRM Metric |
|-----|--------|----------|----------|--------|-----------|---------------|------------|
| 60 | BI | Amex ELAVON | Amex ELAVON | TRANSELECT: `transelect.amex_total` | direct | keep_sign | `DailyJourMetrics.amex_elavon_total` |
| 61 | BJ | Discover | Discover | TRANSELECT: `transelect.discover_total` | direct | keep_sign | `DailyJourMetrics.discover_total` |
| 62 | BK | Master Charge | MasterCard | TRANSELECT: `transelect.master_total` | direct | keep_sign | `DailyJourMetrics.mastercard_total` |
| 63 | BL | Visa | Visa | TRANSELECT: `transelect.visa_total` | direct | keep_sign | `DailyJourMetrics.visa_total` |
| 64 | BM | Carte Debit | Debit Card | TRANSELECT: `transelect.debit_total` | direct | keep_sign | `DailyJourMetrics.debit_total` |
| 65 | BN | Amex GLOBAL | Amex GLOBAL | TRANSELECT: `transelect.amex_global_total` | direct | keep_sign | `DailyJourMetrics.amex_global_total` |

Notes:
- All six card types sum to `DailyJourMetrics.total_cards`.
- Escrow/discount percentages are tracked separately in cols CS-CV (96-99).

---

## Group 12: Misc & HP Tips (BO-BR, cols 66-69)

| Col | Letter | Label FR | Label EN | Source | Operation | Sign Handling | CRM Metric |
|-----|--------|----------|----------|--------|-----------|---------------|------------|
| 66 | BO | Repas NB | Meal Count | analytics.py: `repas_nb` | -- | -- | -- |
| 67 | BP | Star Hot 50 | Star Hot 50 | analytics.py: `star_hot_50` | -- | -- | -- |
| 68 | BQ | H/P Administration 14 | HP Admin Tips (Auth 14) | SALES JOURNAL: `sales_journal.adjustments.administration` | direct | keep_sign | -- |
| 69 | BR | Hotel Promotion 15 | HP Promo Tips (Auth 15) | SALES JOURNAL: `sales_journal.adjustments.hotel_promotion` | direct | keep_sign | -- |

---

## Group 13: Recap Sync (BU-CA, cols 72-78)

Source: `envoie_dans_jour` macro from Recap sheet cells H19:N19.

| Col | Letter | Label FR | Label EN | Source | Operation | Sign Handling | CRM Metric |
|-----|--------|----------|----------|--------|-----------|---------------|------------|
| 72 | BU | Argent Recu | Cash Received | Recap H19 | macro sync | keep_sign | -- |
| 73 | BV | Remb. Serveurs | Server Reimbursements | Recap I19 | macro sync | keep_sign | -- |
| 74 | BW | Remb. Gratuite | Complimentary Reimbursements | Recap J19 | macro sync | keep_sign | -- |
| 75 | BX | (Reserved) | (Reserved) | -- | -- | -- | -- |
| 76 | BY | Due Back Recep | Due Back Reception | Recap L19 | macro sync | keep_sign | -- |
| 77 | BZ | (Reserved) | (Reserved) | -- | -- | -- | -- |
| 78 | CA | Surplus / Deficit | Surplus or Deficit | Recap N19 | macro sync | keep_sign | -- |

---

## Group 14: Settlements & Transfers (CC-CI, cols 80-86)

| Col | Letter | Label FR | Label EN | Source | Operation | Sign Handling | CRM Metric |
|-----|--------|----------|----------|--------|-----------|---------------|------------|
| 80 | CC | Certificat Cadeaux | Gift Certificates | PAGE 6: `settlements.certificat_cadeaux` | direct | keep_sign | -- |
| 81 | CD | (Reserved) | (Reserved) | -- | -- | -- | -- |
| 82 | CE | (Reserved) | (Reserved) | -- | -- | -- | -- |
| 83 | CF | A/R Misc & FO Transfers | A/R Misc + Front Office Transfers | PAGES 2,7: `non_revenue.ar_activity.total` + `balance.front_office_transfers` | combined: `-(total_transfers - payments)` | always_negative | -- |
| 84 | CG | Transfert Royal | Transfer Royal | analytics.py: `transfert_royal` | -- | -- | -- |
| 85 | CH | Tr. Bancaire | Bank Transfer | analytics.py: `tr_bancaire` | -- | -- | -- |
| 86 | CI | Cash Operation | Cash Operation | analytics.py: `cash_operation` | -- | -- | -- |

---

## Group 15: Room Statistics (CK-CR, cols 88-95)

| Col | Letter | Label FR | Label EN | Source | Operation | Sign Handling | CRM Metric |
|-----|--------|----------|----------|--------|-----------|---------------|------------|
| 88 | CK | Chambres Simples | Simple Rooms | PMS/Excel | count | -- | `DailyJourMetrics.rooms_simple` |
| 89 | CL | Chambres Doubles | Double Rooms | PMS/Excel | count | -- | `DailyJourMetrics.rooms_double` |
| 90 | CM | Chambres Suites | Suite Rooms | PMS/Excel | count | -- | `DailyJourMetrics.rooms_suite` |
| 91 | CN | Chambres Comp | Complimentary Rooms | PMS/Excel | count | -- | `DailyJourMetrics.rooms_comp` |
| 92 | CO | Nb Clients | Guest Count | PMS/Excel | count | -- | `DailyJourMetrics.nb_clients` |
| 93 | CP | Hors Usage | Out of Service | PMS/Excel | count | -- | `DailyJourMetrics.rooms_hors_usage` |
| 94 | CQ | Ch. a Refaire | Rooms to Redo | PMS/Excel | count | -- | `DailyJourMetrics.rooms_ch_refaire` |
| 95 | CR | Disponible | Rooms Available | PMS/Excel | count (default 252) | -- | `DailyJourMetrics.rooms_available` |

Notes:
- Total rooms sold = simple + double + suite (col 88+89+90).
- Occupancy rate = total_rooms_sold / disponible * 100.
- Property capacity: 252 rooms (Sheraton Laval).

---

## Group 16: Escrow Percentages (CS-CV, cols 96-99)

| Col | Letter | Label FR | Label EN | Source | Operation | Sign Handling | CRM Metric |
|-----|--------|----------|----------|--------|-----------|---------------|------------|
| 96 | CS | Esc. Amex | Escrow % Amex | Transelect | percentage | -- | avg_escrow_pct.amex |
| 97 | CT | Esc. Diners | Escrow % Diners | Transelect | percentage | -- | -- |
| 98 | CU | Esc. Master | Escrow % MasterCard | Transelect | percentage | -- | avg_escrow_pct.master |
| 99 | CV | Esc. Visa | Escrow % Visa | Transelect | percentage | -- | avg_escrow_pct.visa |

---

## Group 17: Net Card Amounts (CW-CZ, cols 100-103)

| Col | Letter | Label FR | Label EN | Source | Operation | Sign Handling | CRM Metric |
|-----|--------|----------|----------|--------|-----------|---------------|------------|
| 100 | CW | Net Amex | Net Amex Amount | Calculated: gross - escrow | formula | -- | -- |
| 101 | CX | Net Diners | Net Diners Amount | Calculated: gross - escrow | formula | -- | -- |
| 102 | CY | Net Master | Net MasterCard Amount | Calculated: gross - escrow | formula | -- | -- |
| 103 | CZ | Net Visa | Net Visa Amount | Calculated: gross - escrow | formula | -- | -- |

---

## Group 18: F&B POS Summary Totals (DG-DM, cols 110-116)

These are calculated sums across all five F&B outlets (Cafe Link + Piazza + Spesa + Room Service + Banquet).

| Col | Letter | Label FR | Label EN | Source | Operation | Sign Handling | CRM Metric |
|-----|--------|----------|----------|--------|-----------|---------------|------------|
| 110 | DG | NOURRITURE | Total Food | CALCULATED: sum of cols 4,9,14,19,24 | accumulate | keep_sign | `DailyJourMetrics.total_nourriture` |
| 111 | DH | ALCOOL | Total Alcohol | CALCULATED: sum of cols 5,10,15,20,25 | accumulate | keep_sign | -- |
| 112 | DI | BIERES | Total Beer | CALCULATED: sum of cols 6,11,16,21,26 | accumulate | keep_sign | `DailyJourMetrics.total_bieres` |
| 113 | DJ | MINERAUX | Total Non-Alcoholic | CALCULATED: sum of cols 7,12,17,22,27 | accumulate | keep_sign | `DailyJourMetrics.total_mineraux` |
| 114 | DK | VINS | Total Wine | CALCULATED: sum of cols 8,13,18,23,28 | accumulate | keep_sign | `DailyJourMetrics.total_vins` |
| 115 | DL | (Reserved) | (Reserved) | -- | -- | -- | -- |
| 116 | DM | TOTAL BOISSON | Total Beverage | CALCULATED: sum of DH+DI+DJ+DK (all beverage categories) | accumulate | keep_sign | `DailyJourMetrics.total_boisson` |

Notes:
- Col DM (Total Boisson) sums all 20 beverage columns across all 5 outlets and all 4 beverage categories (alcool, bieres, mineraux, vins).
- Food % = DG / (DG + DM); Beverage % = DM / (DG + DM). These feed `DailyJourMetrics.food_pct` and `beverage_pct`.

---

## Unmapped / Reserved Columns

The following column indices exist in the 117-column range but are not mapped in `DAILY_REV_TO_JOUR` or `JOUR_COLS`. They are either populated by Excel formulas, reserved for future use, or legacy fields:

| Col Range | Letters | Purpose |
|-----------|---------|---------|
| 70-71 | BS-BT | Reserved |
| 75 | BX | Reserved (between Recap sync fields) |
| 77 | BZ | Reserved (between Recap sync fields) |
| 79 | CB | Reserved |
| 81-82 | CD-CE | Reserved |
| 87 | CJ | Reserved |
| 104-109 | DA-DF | Reserved (between net cards and F&B totals) |
| 115 | DL | Reserved (between Vins total and Total Boisson) |

---

## Source File Reference

- **Mapping definitions:** `/utils/daily_rev_jour_mapping.py` -- `DAILY_REV_TO_JOUR` dict (68 mapped columns)
- **Analytics column map:** `/utils/analytics.py` -- `JOUR_COLS` dict (all named columns read by analytics)
- **Database model:** `/database/models.py` -- `DailyJourMetrics` class (45 persisted metrics)
- **F&B outlet groupings:** `/utils/analytics.py` -- `FB_OUTLETS` dict (5 outlets x 5 categories)
