# BALANCING RULES — MASTER REFERENCE

**Sheraton Laval — Night Audit RJ Balancing**
**Canonical, authoritative reference for humans, agents, and code.**

_Last updated: 2026-04-08_
_Status: Authoritative — supersedes any agent's recollection of "what a column should be"._

---

## READ FIRST — Agent Reading Protocol

Every agent (balance-reconciliation-analyst, tech-lead-orchestrator, planner, balancer code reviewer) **must read Parts 1, 2, and 3 of this document before making any claim about what a column "should" be, what is "a bug," or what DC "should" equal**.

1. **Before claiming a column is wrong:** check Part 2 for the canonical formula and cite the Guide source line.
2. **Before claiming DC is unbalanced:** walk the 4-class reconciliation in Part 3. A non-zero DC is not automatically a bug.
3. **Before claiming code is buggy:** compare `calculate_jour` against the Guide formula in Part 2. The Guide is the source of truth. If `calculate_jour` disagrees with the Guide, the Guide wins and the code is the candidate for change — but only after confirming with the user.
4. **When a diff is found:** map it to an error pattern in Part 5 before calling it a bug.
5. **For DC ≠ 0:** walk Part 3's 4-class decomposition before declaring it unbalanced. A DC residual ≤ 0.15 is acceptable. A DC equal to an InterHotel XferIn value is a declared variance, not a bug.

**Source documents quoted verbatim (French, as authored):**
- `RJ_Balancing_Guide_Sheraton.docx` — referenced as **[Sheraton]**
- `RJ_Balancing_Complete_Guide.docx` — referenced as **[Complete]**
- `RJ_Audit_Methodology.docx` — referenced as **[Method]**

All three guides live at the repo root (`/home/v/Documents/Projects/audit-pack/`). This document is self-contained: agents reading it should not need to open the docx files.

---

## Part 1 — Column Letter ↔ Index Mapping

The RJ `jour` sheet has ~117 columns. Columns 0-3 are meta:

| Letter | Index | Role |
|:-:|:-:|:--|
| A | 0 | Jour (day number 1-31) |
| B | 1 | Bal_Ouv (opening balance — auto from previous day's col 3) |
| C | 2 | **Diff.Caisse (DC)** — must = 0.00 |
| D | 3 | Bal_Ferm (closing balance) |

Credits (col 4-57) and debits (col 60-86) follow. Excel-letter ↔ index uses 0-based letters (A=0, B=1, … Z=25, AA=26, AB=27, …). So AK = 26+10 = **36**, AP = 26+15 = **41**, AU = 26+20 = **46**, BJ = 52+9 = **61**, BF = 26+5 = **31** _(but see note below — "BF" in the Sheraton Guide refers to the column labelled "Diff Forfait", which the code places at index 57)_, CA = 78, CF = 83.

> ⚠️ **Letter-to-index contradiction flagged.** [Sheraton] uses the letter label "BF" for "Diff Forfait" (its Table 2 row: "BF | Diff Forfait | … = −(Forfait − G4)"), yet pure Excel-letter arithmetic gives BF = 31. The rj_balancer code puts Diff Forfait at **index 57** (letter BF counted from E=4? No — letter BF 0-indexed = 31, 1-indexed = 32; 57 is letter BF only if the column layout has gaps). This means **the Guide's letter labels track the physical Excel column positions in the actual RJ workbook, which has merged/blank/spacer columns; they are NOT a pure alphabetic mapping**. Always trust the `COL_NAMES` index mapping when cross-referencing code to Guide. The letter is a human label only. **TBD: user should confirm the exact letter↔index table if agents need to address columns by letter.**

### Canonical index table (authoritative: from `utils/rj_balancer.py` `COL_NAMES`, cross-checked against [Sheraton] Table 2 and [Complete] Tables 0-1)

| Guide letter | Index | Code name | French label | What it represents | Primary source |
|:-:|:-:|:--|:--|:--|:--|
| E  | 4  | Pause    | Pause Spesa                  | SJ Piazza Pause + SJ Banquet Pause                           | SJ |
| F  | 5  | Boi_Link | Compensation résiduelle      | Manual DC compensation (auditor fills to force DC=0)         | Manual |
| G  | 6  | Bie_Link | Compensation HP              | = −(SJ Admin + SJ Promo) when no detailed HP file            | Manual / HP |
| J  | 9  | Nou_Piaz | Piazza Nourriture            | SJ Piazza Nourr − HP Piazza food (Admin+Promo) − adj − CL    | SJ − HP |
| K  | 10 | Boi_Piaz | Piazza Alcool                | SJ Piazza Alcool − HP Piazza boisson                         | SJ − HP |
| L  | 11 | Bie_Piaz | Piazza Bières                | SJ Piazza Bières − HP Piazza bière                           | SJ − HP |
| M  | 12 | Min_Piaz | Piazza Minéraux              | SJ Piazza Non-Alcool Bar − HP Piazza min                     | SJ − HP |
| N  | 13 | Vin_Piaz | Piazza Vins                  | SJ Piazza Vins − HP Piazza vin                               | SJ − HP |
| O  | 14 | Nou_Mar  | Spesa/Marché Nourriture      | SJ Spesa Nourr − HP Tabagie food (Admin+Promo) − adj         | SJ − HP |
| T  | 19 | Nou_SCh  | ServCh Nourriture            | SJ Chambres Nourriture                                       | SJ |
| U  | 20 | Boi_SCh  | ServCh Alcool                | SJ Chambres Alcool                                           | SJ |
| V  | 21 | Bie_SCh  | ServCh Bières                | SJ Chambres Bières                                           | SJ |
| W  | 22 | Min_SCh  | ServCh Minéraux              | SJ Chambres Non-Alcool Bar                                   | SJ |
| X  | 23 | Vin_SCh  | ServCh Vins                  | SJ Chambres Vins                                             | SJ |
| Y  | 24 | Nou_Bqt  | Banquet Nourriture           | SJ Banquet Nourriture (− HP Bqt Nourr if applicable)         | SJ (− HP) |
| Z  | 25 | Boi_Bqt  | Banquet Alcool               | SJ Banquet Alcool (crédit=+, débit=−)                        | SJ |
| AA | 26 | Bie_Bqt  | Banquet Bières               | SJ Banquet Bières                                            | SJ |
| AB | 27 | Min_Bqt  | Banquet Minéraux             | SJ Banquet Non-Alcool Bar                                    | SJ |
| AC | 28 | Vin_Bqt  | Banquet Vins                 | SJ Banquet Vins                                              | SJ |
| AD | 29 | Pourb    | Pourboires (F&B)             | SJ total (Piaz+Bqt+Spesa) Pourboire À Payer − HP Pourb       | SJ − HP |
| AE | 30 | Equip    | Équipement A/V               | SJ Banquet Équip Audio Visuel (débit → négatif)              | SJ |
| AF | 31 | Divers   | Divers Banquet               | SJ Banquet EQ. DIVERS (crédit=+, débit=−; or 0 if in DR)     | SJ |
| AG | 32 | LocSal   | Location de Salles           | SJ Piazza Loc + SJ Banquet Loc + DR Loc Salle Forfait        | SJ + DR |
| AH | 33 | SOCAN    | SOCAN / Résonne              | SJ Banquet SOCAM                                             | SJ |
| AJ | 35 | Tabag    | Tabagie                      | SJ Spesa Tabagie + SJ Piazza Tab − HP Tabagie items          | SJ − HP |
| AK | 36 | Chamb    | Chambres                     | DR Chambres Total − G4                                       | DR |
| AL | 37 | TelLoc   | Téléphone Local              | DR Tel Local Today                                           | DR p.1 |
| AM | 38 | TelInt   | Téléphone Interurbain        | DR Interurbain Today                                         | DR p.1 |
| AN | 39 | —        | Téléphones Publics           | DR Telephones Publics Today (present in Guide, not in COL_NAMES) | DR p.1 |
| AO | 40 | Nettoy   | Nettoyeur                    | DR Nettoyeur / Dry Cleaning Today                            | DR p.2 |
| AP | 41 | Geac     | GEAC Mch/Liqueur comp.       | = geac_ux row 55 = −(FD − AR)                                | GEAC |
| AQ | 42 | StMart   | St-Martin Électrique         | SJ Banquet EQ. DIVERS crédit (or DR Equip Divers)            | SJ / DR |
| AS | 44 | AutGL    | Autres Grand Livre           | DR Autres GL + Autres GL T − SJ Depot Util                   | DR p.2 |
| AT | 45 | Sonifi   | Sonifi                       | DR Sonifi Today                                              | DR p.2 |
| AU | 46 | AutRev   | Autre Revenu                 | SJ Fr/Étage + DR Lit Pliant + DR InterHotel + DR Non-Tax     | SJ + DR |
| AV | 47 | LocBout  | Location Boutique            | DR Location Boutique Today                                   | DR p.2 |
| AW | 48 | Intrnt   | Internet                     | DR Internet (± signe!) + SJ Banquet Internet + SJ Spesa Internet | DR + SJ |
| AX | 49 | TVQ      | TVQ (Taxe Vente Québec)      | SJ TVQ + DR TVQ (Ch+Aut+Int+Comptab)                         | SJ + DR |
| AY | 50 | TPS      | TPS (Taxe Produits Services) | SJ TPS − TPS sur pannes + DR TPS (Ch+Aut+Int+Comptab)        | SJ + DR |
| AZ | 51 | TVH      | Taxe Hébergement             | DR Taxe Hébergement Today                                    | DR p.2 |
| BA | 52 | Massage  | Massage                      | DR Massage Today                                             | DR p.2 |
| BB | 53 | Vest     | Vestiaire                    | SJ Banquet Vestiaire                                         | SJ |
| BC | 54 | Ristour  | Ristournes / Autre À Payer   | DR Autre À Payer Taxable Today                               | DR p.2 |
| —  | 55 | Fax      | Fax / Photocopies            | DR Fax & Photocopies                                         | DR p.2 |
| BF | 57 | DifForf  | Diff Forfait                 | = −(SJ Forfait − G4)                                         | SJ + AK |
| BI | 60 | AmxElav  | Amex Elavon                  | Transelect TOTAUX row 37 Amex Elavon                         | Transelect |
| BJ | 61 | Discov   | Discover                     | Transelect TOTAUX row 37 Discover (sign per X24 rule)        | Transelect |
| BK | 62 | MC       | MasterCard                   | Transelect TOTAUX row 37 Master                              | Transelect |
| BL | 63 | Visa     | Visa                         | Transelect TOTAUX row 37 Visa                                | Transelect |
| BM | 64 | Debit    | Carte Débit                  | Transelect TOTAUX row 37 Débit                               | Transelect |
| BN | 65 | AmxGlb   | Amex Global                  | Transelect TOTAUX row 37 Amex Global                         | Transelect |
| BQ | 68 | HPAdmP   | HP Admin Pourboire           | HP Journalier row 32 col Administration Pourb (positive)     | HP |
| BR | 69 | HPProP   | HP Promo Pourboire           | HP Journalier row 32 col Promotion Pourb (positive)          | HP |
| BU | 72 | Argent   | Argent Reçu                  | Recap Argent Reçu (row 23-24)                                | Recap |
| BV | 73 | RmbSrv   | Remboursement Serveur        | = −(DR Remb Serveur p.5). **Never Recap Due Back N/B.**      | DR p.5 |
| BW | 74 | RmbGrt   | Remboursement Gratuité       | = −(SJ Pourboire Charge)                                     | SJ |
| BY | 76 | DueBk    | Due Back Réception           | = −(Recap Due Back Réception row 16)                         | Recap |
| CA | 78 | S&D      | Surplus/Déficit caisse       | = −(Recap Surplus/Déficit row 19). Déficit=positif → col78=négatif. | Recap |
| CB | 79 | CertCd   | Certificat Cadeau / GiveX    | SJ Cert Cadeau + DR GiveX                                    | SJ + DR |
| CF | 83 | TrC/R    | Transfer C/R (A/R)           | **Always = DR Facture Direct p.6. NEVER AR Guest Folios.**   | DR p.6 |

**Gaps in COL_NAMES (columns cited in [Sheraton] Table 2 but not in code's `COL_NAMES`):** AN (Téléphones Publics, index 39 — rarely non-zero), and the Guide's CB (Bon d'Achat/Gift Card/Bon Remanc total, index 79 — code maps 79 to CertCd which absorbs both).

---

## Part 2 — Column Formulas (canonical)

Format:
```
col N (LETTER — Code/Label)
  = expression (with source annotations)
Source: [Guide] section/table/paragraph
Notes: …
```

### Credits (cols 4-57)

```
col 4 (E — Pause Spesa)
  = SJ.piazza_pause + SJ.banquet_pause
Source: [Sheraton] Table 2 R25; [Complete] Table 0 R1
```

```
col 9 (J — Piazza Nourriture)
  = SJ.piazza_nourr
    − HP.piazza_food_admin
    − HP.piazza_food_promo
    − adj_piaz                 (auditor manual)
    − cl_nourr                 (Club Lounge total — see §Club Lounge)
Source: [Sheraton] Table 2 R3, Table 10 R1; [Complete] Table 0 R4
Notes: Toujours positif. Si déduction CL rend la valeur ~0, garder à 0.
```

```
col 10 (K — Piazza Alcool)
  = SJ.piazza_alcool − HP.piazza_boi_admin − HP.piazza_boi_promo
Source: [Sheraton] Table 2 R4; [Complete] Table 0 R5
Notes: [Sheraton] R4 dit "Pas de déduction HP alcool" mais le code et [Complete] soustraient HP Boisson. Code wins — HP boisson IS deducted when present.
```

```
col 11 (L — Piazza Bières)
  = SJ.piazza_bieres − HP.piazza_biere_admin − HP.piazza_biere_promo
Source: [Sheraton] Table 2 R5, Table 10 R2
```

```
col 12 (M — Piazza Minéraux)
  = SJ.piazza_min − HP.piazza_min_admin − HP.piazza_min_promo
Source: [Sheraton] Table 2 R6, Table 10 R3
```

```
col 13 (N — Piazza Vins)
  = SJ.piazza_vins − HP.piazza_vin_admin − HP.piazza_vin_promo
Source: [Sheraton] Table 2 R7, Table 10 R4
```

```
col 14 (O — Spesa/Marché Nourriture)
  = SJ.spesa_nourr − HP.tabagie_food_admin − HP.tabagie_food_promo − adj_mar
Source: [Sheraton] Table 2 R23, Table 10 R5; [Complete] Table 0 R9
Notes: "HP Tabagie = Spesa/Marché dans HP fichier" [Sheraton] Table 10 R5.
```

```
col 19 (T — ServCh Nourriture)
  = SJ.chambres_nourr      [− HP adj_servch if applicable]
Source: [Sheraton] Table 2 R8
```

```
cols 20-23 (U,V,W,X — ServCh Alcool, Bières, Min, Vins)
  = SJ.chambres_<cat>       (direct, no HP deduction normally)
Source: [Sheraton] Table 2 R9-R12
```

```
col 24 (Y — Banquet Nourriture)
  = SJ.banquet_nourr        [− HP Banquet Nourr if applicable]
Source: [Sheraton] Table 2 R13
```

```
cols 25-28 (Z,AA,AB,AC — Banquet Alcool, Bières, Min, Vins)
  = SJ.banquet_<cat>
Source: [Sheraton] Table 2 R14-R17
Notes: Débit SJ → NÉGATIF. Crédit SJ → POSITIF.
```

```
col 29 (AD — Pourboires F&B)
  = max(0, SJ.piazza_pourb + SJ.banquet_pourb + SJ.spesa_pourb
          − HP_pourb_admin − HP_pourb_promo)
Source: [Sheraton] Table 2 R18; [Complete] Table 0 R12
Notes: HP pourb goes into cols 68/69, not 29. Floor at 0 (HP can't make tips negative). HP pourb must NOT be deducted twice.
```

```
col 30 (AE — Équipement Audio Visuel)
  = SJ.bqt_eq_audio − SJ.piaz_eq_audio
Source: [Sheraton] Table 2 R19; [Complete] Table 0 R13
Notes: Débit SJ → négatif. Crédit SJ → positif.
```

```
col 31 (AF — Divers Banquet)
  = SJ.bqt_eq_divers
Source: [Sheraton] Table 2 R20; [Complete] Table 0 R14
Notes: Crédit=+, débit=−. Mettre 0 si déjà capturé dans DR (erreur Fév 4: +565 entré alors que déjà dans DR).
```

```
col 32 (AG — Location de Salles)
  = SJ.piazza_loc + SJ.banquet_loc + DR.loc_salle_forfait
Source: [Sheraton] Table 2 R21; [Complete] Table 0 R15
```

```
col 33 (AH — SOCAN)
  = SJ.banquet_socam
Source: [Sheraton] Table 2 R22; [Complete] Table 0 R16
```

```
col 35 (AJ — Tabagie)
  = SJ.spesa_tab + SJ.piazza_tab − HP.tabagie_items_admin − HP.tabagie_items_promo
Source: [Sheraton] Table 2 R24, Table 10 R6; [Complete] Table 0 R17
```

```
col 36 (AK — Chambres)
  = DR.chambres_total − G4
    where G4 = CL_total if CL_total > 0 else 0
          or G4 = SJ.forfait − |col 57|   (equivalent reformulation)
Source: [Sheraton] Table 2 R1+R27, [Complete] Table 0 R18
Notes: G4 = Club Lounge deduction from Chambres OR forfait reconciliation. The auditor supplies g4_montant when it differs.
```

```
cols 37-39 (AL, AM, AN — Téléphones Local, Interurbain, Public)
  = DR.tel_<kind> Today
Source: [Sheraton] Table 2 R28-R30
```

```
col 40 (AO — Nettoyeur)
  = DR.nettoyeur Today
Source: [Sheraton] Table 2 R31
```

```
col 41 (AP — GEAC Mch/Liqueur compensation)
  = geac.col41  = −(FD − AR) if FD ≠ AR else 0
       equivalently = geac_ux cell D41 (row 41-row index 40) or row 55/56
Source: [Sheraton] §5.2 P38-P42, Table 2 R32, Table 6 R1-R4
Notes: POSITIVE if FD < AR; NEGATIVE if FD > AR. Row 55 of geac_ux holds the pre-computed compensation. If the 'doesn't balance' checkbox is marked, the variance is acknowledged → no col 41 entry beyond what's already there ([Sheraton] Table 7).
```

```
col 42 (AQ — St-Martin Électrique)
  = SJ.banquet_eq_divers  (credit only)  OR  DR Equip Divers
Source: [Sheraton] Table 2 R33; [Complete] Table 0 R22
Notes: Populated only when SJ has the item as a credit (not a debit).
```

```
col 44 (AS — Autres Grand Livre)
  = DR.autres_gl + DR.autres_gl_t − SJ.depot_util
Source: [Sheraton] Table 2 R34, §10 P90, Table 15; [Complete] Table 0 R23
Notes: Conserve le signe DR (généralement négatif). DEPOT UTIL appartient à AS, pas à CF — "ne pas mettre DEPOT UTIL dans CF, c'est l'erreur classique" [Sheraton] Table 15.
```

```
col 45 (AT — Sonifi)
  = DR.sonifi Today
Source: [Sheraton] Table 2 R35
```

```
col 46 (AU — Autre Revenu) ⭐ MOST-FORGOTTEN COLUMN
  = SJ.piaz_fretage              (SJ line "FR/ETAGE" under PIAZZA, if present)
  + SJ.ch_fretage                (SJ line "FR/ETAGE" under CHAMBRES)
  + DR.lit_pliant                (DR p.2 "MACHINE LIT PLIANT Today")
  + DR.autres_a_payer_non_tax    (DR p.5 — "Autres À Payer Non-Taxable", if present)
  + DR.interhotel_xferin         (DR p.7 — "InterHotel XferIn Today") ⭐⭐⭐
  + any_other_non_taxable_revenue (DR Daily Revenue misc)
Source: [Sheraton] §8 P77-P83, Table 2 R36, Table 12, Table 13; [Complete] §5.7 P47-P48, Table 0 R25
Notes:
  - InterHotel XferIn ≈ 9.99/day of accumulation. Monday=1 day=9.99,
    Tuesday=2 days=19.98, Sunday often 5 days=49.95 ([Sheraton] Table 12 R2).
  - **The InterHotel value is structurally inside BF via New Balance but
    has NO dedicated credit column** ([Complete] P48 "dans le BF mais pas
    de colonne dans le jour"). The Guide's rule is to route it into col 46.
  - CRITICAL: The #1 most-forgotten line. DC = ±9.99 (or multiple) →
    InterHotel missing from col 46 ([Sheraton] Table 17 R2, §15 P144).
  - The code currently only sums piaz_fretage + ch_fretage + lit_pliant.
    Any InterHotel/Non-Tax routing must be applied by the auditor or the
    webapp's auto-fix path.
```

```
col 47 (AV — Location Boutique)
  = DR.loc_boutique Today
Source: [Sheraton] Table 2 R37
```

```
col 48 (AW — Internet) ⭐ SIGN-ERROR TRAP
  = DR.internet    (OFTEN NEGATIVE — keep the sign!)
  + SJ.banquet_internet
  + SJ.spesa_internet
Source: [Sheraton] §9 P85-P89, Table 2 R38, Table 14; [Complete] §5.3 P39-P40, Table 0 R27
Notes:
  - DR Internet is negative on many days (−33.74, −20.92, −9.01, …).
    Keep the negative sign. Entering positive = DC off by 2×|amount|.
  - "Erreur fréquente: entrer le positif au lieu du négatif" [Complete] P40.
  - Example: DR = −33.74, SJ Bqt = 200 → col 48 = 166.26
    Example: DR = +14.77, SJ Bqt = 100 → col 48 = 114.77
```

```
col 49 (AX — TVQ)
  = SJ.tvq
  + DR.tvq_chambres
  + DR.tvq_autres
  + DR.tvq_internet   (can be negative → algebraic add)
  + DR.tvq_comptab
Source: [Sheraton] Table 2 R39; [Complete] Table 0 R28
Notes: Ajout algébrique. Les TPS/TVQ Internet peuvent être négatifs → les soustraire.
```

```
col 50 (AY — TPS)
  = SJ.tps − TPS_on_pannes
  + DR.tps_chambres + DR.tps_autres + DR.tps_internet + DR.tps_comptab
  + DR.tps_tel (if present)
  where TPS_on_pannes = (panne_visa + panne_mc + panne_interact + panne_amex + panne_lien) × 0.05
Source: [Sheraton] Table 2 R40; code utils/rj_balancer.py L660-663
Notes: The panne TPS subtraction is in the code but NOT explicit in the Guide — it compensates for SJ TPS including pannes (non-real tax). Confirmed via [Sheraton] §6.2 pannes section and code.
```

```
col 51 (AZ — Taxe Hébergement)
  = DR.taxe_hebergement Today
Source: [Sheraton] Table 2 R41. Toujours positif.
```

```
col 52 (BA — Massage)
  = DR.massage Today
Source: [Sheraton] Table 2 R42
```

```
col 53 (BB — Vestiaire)
  = SJ.banquet_vestiaire
Source: [Sheraton] Table 2 R43
Notes: Omission fréquente ([Sheraton] §15 P155).
```

```
col 54 (BC — Ristournes / Autre À Payer)
  = DR.autre_a_payer (Taxable) Today
Source: [Sheraton] Table 2 R44
```

```
col 55 (— — Fax / Photocopies)
  = DR.fax
Source: [Complete] Table 0 R34 (col 55 Fax/Photo)
Notes: Guide Sheraton lists Fax in Table 2 row labelled "BC Ristournes" ambiguously; the code uses col 55 for fax which aligns with [Complete].
```

```
col 57 (BF — Diff Forfait)
  = −(SJ.forfait − G4)   if SJ.forfait > 0 else 0
    where G4 = CL_total if CL_total > 0 else auditor-supplied g4_montant
Source: [Sheraton] Table 2 R2; [Complete] Table 0 R35
Notes: Si Club Lounge s'applique, G4 = CL total. Si forfait classique sans CL, G4 = auditor input.
```

### Debits (cols 60-86)

```
col 60 (BI — Amex Elavon)      = Transelect row 37 col 0  (macro calcul_carte)
col 61 (BJ — Discover)         = Transelect row 37 col 1  (+ manual X24 sign flip)
col 62 (BK — MasterCard)       = Transelect row 37 col 2
col 63 (BL — Visa)             = Transelect row 37 col 3
col 64 (BM — Carte Débit)      = Transelect row 37 col 4
col 65 (BN — Amex Global)      = Transelect row 37 col 5
Source: [Sheraton] Table 2 R50-R55; [Complete] §10 P82, Table 1 R1-R6
Notes on BJ (Discover): Its sign is controlled by the X24 rule, not by the
raw Transelect value. X24<0 (weekday pannes): BJ positive. X24>0 (Sunday
batch): BJ negative. See Part 6 §Transelect X24.
```

```
col 68 (BQ — HP Admin Pourboire)
  = HP.piaz_pourb_admin + HP.tab_pourb_admin + HP.bqt_pourb_admin
    (HP Journalier row 32, paiement type 14-Administration)
Source: [Sheraton] Table 2 R48, Table 10 R7; [Complete] Table 1 R7
Notes: TOUJOURS POSITIF (débit).
```

```
col 69 (BR — HP Promo Pourboire)
  = HP.piaz_pourb_promo + HP.tab_pourb_promo + HP.bqt_pourb_promo
Source: [Sheraton] Table 2 R49, Table 10 R8; [Complete] Table 1 R8
Notes: TOUJOURS POSITIF (débit).
```

```
col 72 (BU — Argent Reçu)
  = Recap.argent_recu
Source: [Sheraton] Table 2 R56; [Complete] Table 1 R9
```

```
col 73 (BV — Remboursement Serveur)
  = −DR.remb_serveur     (ALWAYS DR p.5 Débourse, NEVER Recap Due Back N/B)
Source: [Sheraton] Table 2 R57; [Complete] §5.2 P37-P38, Table 1 R10
Notes: #1 recurring source-confusion error per [Method] §6.2.
```

```
col 74 (BW — Remboursement Gratuité)
  = −SJ.pourb_charge
Source: [Sheraton] Table 2 R58; [Complete] Table 1 R11
```

```
col 76 (BY — Due Back Réception)
  = −Recap.due_back_rec  if due_back_rec > 0 else 0
Source: [Sheraton] Table 2 R59; [Complete] Table 1 R12
Notes: Always negative.
```

```
col 78 (CA — Surplus/Déficit caisse)
  = −Recap.surplus_deficit
Source: [Sheraton] Table 2 R60; [Complete] Table 1 R13
Notes: Recap stores surplus as negative number; jour debit needs the
opposite sign. Déficit (missing cash) → col 78 positive. Surplus → col 78 negative.
```

```
col 79 (CB — Cert Cadeau / GiveX)
  = SJ.cert_cadeau + DR.givex
Source: [Sheraton] Table 2 R45-R46; [Complete] Table 1 R14
```

```
col 83 (CF — Transfer C/R) ⭐ ALWAYS DR FD
  = DR.facture_direct   (DR p.6 Settlements "Facture Direct Today")
Source: [Sheraton] §5.1 P34-P35, Table 2 R47, Table 5; [Complete] §5.1 P35-P36, Table 1 R15
Notes: ABSOLUTE RULE. "CF ≠ AR Summary Total Transfers — c'est une erreur fréquente!" [Sheraton] Table 5 R1. "CF ≠ FD − DEPOT UTIL" [Sheraton] Table 5 R2 (erreur du 30 mars). Col 83 is CIRCULAIRE with col 3 BF — changing it changes BF too, net DC impact = 0 ([Complete] §5.1, [Method] §Step 2).
```

### Bal_Ferm (col 3)

```
col 3 (D — Bal_Ferm)
  = −(DR.new_balance)  −  (Advance_Deposit_on_Hand_Today)
    where Adv_Dep_Today = Yesterday + Received − Applied − Cancelled − DNA
Source: [Sheraton] §11 P93, Table 16; [Complete] §2 P9+P12, §7 P59; [Method] §3.1
```

### Columns with NO documented formula (gaps)

The guides do NOT give formulas for these indices (either never used, rarely non-zero, or handled outside the balancer scope):

- **col 5 Boi_Link** — residual manual compensation, defined operationally (Part 3)
- **col 6 Bie_Link** — HP compensation fallback = −(SJ Admin + SJ Promo), only when no detailed HP file
- **col 33 SOCAN** — formula present but trivial
- **col 34, 43, 56, 58, 59** — never mentioned
- **col 66, 67, 70, 71, 75, 77, 80, 81, 82, 84, 85, 86** — never mentioned
- **col 79 CertCd / CB** — mentioned in [Sheraton] Table 2 R45-R46 but with two different meanings (Gift Card AND Cert Cadeau); code conflates them.

**Coverage: approximately 37 of 86 columns have explicit Guide formulas.** The remaining 49 are either always zero, handled by macros, or out-of-scope. Every non-zero credit/debit the auditor must worry about is in the 37 documented columns.

---

## Part 3 — DC Reconciliation Rules (the core)

### The absolute rule

> **"Le Diff.Caisse (colonne C de la feuille JOUR) doit toujours être égal à 0.00 à la fin du balancement de chaque nuit. C'est la règle absolue."** — [Sheraton] §1 P4
>
> **"Le DC dans la colonne D du jour doit toujours arriver à 0. S'il n'est pas à 0, il y a soit une erreur de saisie, soit un montant manquant."** — [Complete] §1 P5

### The DC formula

```
DC = Bal_Ferm − Bal_Ouv − ΣCrédits + ΣDébits

where:
  Bal_Ferm = −(DR New Balance p.7) − Advance Deposit on Hand Today
  Bal_Ouv  = col 3 of the previous day (automatic)
  ΣCrédits = sum of cols 4-57
  ΣDébits  = sum of cols 60-86
```

> "Si DC > 0 : trop de débits ou pas assez de crédits → chercher crédit manquant ou débit en trop.
> Si DC < 0 : trop de crédits ou pas assez de débits → chercher débit manquant ou crédit en trop." — [Sheraton] Table 1

### The 4 accepted DC-reconciling classes (in diagnostic order)

A non-zero DC is ONLY acceptable if it is fully explained by a combination of:

1. **Transelect X24** — POS terminal variance
   - Trigger: `abs(tr.x24) > 0.01`
   - Target column: col 61 (BJ Discover) — via sign flip
   - Sign: X24 negative (weekday) → BJ positive. X24 positive (Sunday batch) → BJ negative.
   - Source: [Sheraton] §6 P45-P61, Table 8; [Complete] §5.5 P43-P44

2. **GEAC col 41** — Facture Direct vs AR variance
   - Trigger: `geac.fd ≠ geac.ar`
   - Target column: col 41 (AP Mch/Liqueur comp)
   - Formula: `col 41 = −(FD − AR)`. Positive if FD<AR, negative if FD>AR.
   - Reference: geac_ux row 55/56 pre-computes the compensation
   - Exception: if the "Check box if amounts don't balance" checkbox is set in geac_ux, the variance is officially acknowledged — no col 41 entry needed ([Sheraton] Table 7).
   - Source: [Sheraton] §5.2 P38-P42, Table 6; [Complete] §5.9 P51-P52

3. **Recap I10 — Surplus/Déficit caisse**
   - Trigger: non-zero `recap.surplus_deficit`
   - Target column: col 78 (CA S&D)
   - Sign: déficit (missing cash) → col 78 positive; surplus → col 78 negative
   - Source: [Sheraton] Table 2 R60; [Complete] §3.6 P24-P25

4. **XTransferIn / InterHotel XferIn** — structural
   - Trigger: `dr.interhotel_xferin > 0` (typically 9.99 or a multiple)
   - Canonical target: col 46 (AU Autre Revenu)
   - Structural fact: the value is ALREADY in BF via New Balance, but has no automatic credit column. Adding it to col 46 zeroes its effect on DC.
   - Source: [Sheraton] §8 P77-P83, Tables 12-13; [Complete] §5.7 P47-P48

### User-clarified rule for class 4 (2026-04-08)

If the automated balancer cannot auto-route InterHotel XferIn into col 46 for any reason, it is acceptable to **leave it in DC as a declared variance**, provided:

- the webapp shows the user the **exact amount** (e.g. 9.99, 49.95);
- the webapp **labels the remaining DC as "InterHotel XferIn"**;
- the webapp offers **two paths**:
  1. **Auto-fix**: one-click add amount to col 46, DC → 0
  2. **Accept as declared variance**: leave DC = amount, flag as "débalancement explicable par XTransferIn = 9.99"

**Both outcomes are valid. The only outcome that is NOT acceptable is an unexplained DC.**

### Tolerance rule — circular residual

> "Résiduel accepté ≤ 0.15$. Un résiduel de 0.00 à 0.15$ après toutes les corrections est typiquement circulaire. … Ne JAMAIS inventer une entrée pour forcer DC à 0 — cela créerait une fausse écriture comptable." — [Sheraton] Table 18

Circular residuals arise because some items traverse CHAMBRE → folio → AR → New Balance → BF → DC (e.g. a room charge of 0.12 in the SJ). They self-balance and should not be "fixed."

### The don't-invent-entries rule

> "Ne JAMAIS inventer une entrée pour forcer DC à 0 — cela créerait une fausse écriture comptable." — [Sheraton] Table 18

If, after mapping DC to the 4 classes, there is still residual > 0.15 that cannot be explained by an error in Part 5, the correct action is to **surface the unexplained amount to the auditor**, not to fabricate a compensation.

### Diagnostic table (Guide Sheraton Table 17 — verbatim)

| Symptôme DC | Montant typique | Première vérification |
|---|---|---|
| DC ≠ 0 après tout | Toute valeur | 1. InterHotel AU? 2. X24/Discover? 3. HP pourb BQ/BR? 4. CF = FD? |
| DC = +/− 9.99 ou multiple | 9.99, 19.98, 29.97... | InterHotel XferIn manquant dans AU. Vérifier DR p.7. |
| DC = +/− HP Promo total | Varie | HP Promo non déduit de J, O, AJ. BQ/BR = 0? |
| DC = +/− X24 | Pannes SJ | Discover BJ non entré. Calculer X24 = Transelect total bank − POSITOUCH. |
| DC = +/− (FD − AR) | Varie | AP = 0 mais FD ≠ AR. Calculer AP = −(FD−AR). Corriger CF = FD. |
| DC positif = +564.98 (dimanche) | ~564.98 | Batch weekend. BJ doit être NÉGATIF (−564.98). X24 est positif ce jour. |
| DC = +/− DEPOT UTIL | 700, 500... | AS = DR GL seulement, ou AS = DR GL − DEPOT UTIL? CF = FD ou FD − DEPOT UTIL? |
| Résiduel circulaire ≤ 0.15 | 0.12, 0.05... | Charge CHAMBRE dans SJ (folio client → AR → BF circulaire). Acceptable. |
| GEAC Visa variance cochée | Varie | Case 'doesn't balance' cochée dans GEAC = reconnu. Pas d'entrée DC supplémentaire requise. |
| AS = valeur inattendue | Varie | Vérifier DR Autres GL TOTAL Today. Si DEPOT UTIL dans SJ: AS = DR − DEPOT UTIL. |
| BF incorrect | Varie | Vérifier AK = DR Chambres − Club Lounge. BF = −(Forfait SJ − G4) où G4 = DR − AK. |
| DC = +/− Club Lounge | CL value | CL positif: déduire de J. CL négatif: gérer via NB/BF différemment. |

---

## Part 4 — The 21-Point Checklist (verbatim, [Complete] §13)

From [Complete] P96-P118, reproduced verbatim:

> Pour chaque jour, vérifier dans l'ordre:
>
> 1. Col 3 (BF) = −(DR New Balance) − (Adv Dep on Hand Today) au centime près
> 2. Chaque crédit F&B (cols 9-35) = SJ − HP − adj
> 3. Col 36 = DR Chambres − G4
> 4. Col 44 = DR Autres GL (+ Autres GL T) (− SJ Depot Util si applicable)
> 5. Col 48 = DR Internet (VÉRIFIER LE SIGNE!) + SJ Bqt Internet
> 6. Taxes (cols 49-51) = somme SJ + DR composantes
> 7. Tous les débits CC (cols 60-65) = transelect TOTAUX
> 8. Col 68/69 = HP pourboire seulement
> 9. Col 72 = Recap Argent Reçu
> 10. Col 73 = −(DR Remb Serveur)
> 11. Col 74 = −(SJ Pourb Charge)
> 12. Col 76 = −(Recap Due Back Réception)
> 13. Col 78 = Recap S&D
> 14. Col 83 = DR Facture Direct
> 15. Transelect X24 = 0
> 16. Geac CC variance = 0
> 17. Geac FD vs AR → col 41
> 18. Club Lounge déduit si applicable
> 19. DR InterHotel XferIn comptabilisé
> 20. HP Autres comptabilisé
> 21. DR Débourse comptabilisé (si non-zero)

### Alternate checklist — [Sheraton] §14 P108-P128

[Sheraton] has a complementary checklist also worth codifying; the webapp's live panel should merge both:

> ☐ D = −New Balance − Adv Dep on Hand
> ☐ AK = DR Chambres Total − Club Lounge (si CL > 0)
> ☐ CF = DR Facture Direct p.6 (jamais AR Summary, jamais FD − DEPOT UTIL)
> ☐ AP = −(FD − AR) si FD ≠ AR dans GEAC_UX — sinon 0
> ☐ AS = DR Autres GL (± DEPOT UTIL si présent dans SJ)
> ☐ AW = DR Internet (±) + SJ Banquet Internet — signe conservé
> ☐ AY = TPS Chamb + SJ TPS + TPS Autres + TPS Inet (algébrique)
> ☐ AX = TVQ Chamb + SJ TVQ + TVQ Autres + TVQ Inet (algébrique)
> ☐ AU = FR/Étage + Lit Pliant + InterHotel XferIn + Non-Tax (TOUS inclus)
> ☐ HP: J, O, AJ correctement réduits (Admin + Promo déduits)
> ☐ BQ = HP Admin Pourb, BR = HP Promo Pourb (tous deux positifs)
> ☐ HP total = SJ Admin + SJ Hotel Promotion (vérification croisée)
> ☐ BJ (Discover) = X24 avec signe inversé (+ si jour normal, − si dimanche)
> ☐ BF = −(SJ Forfait − G4) où G4 = DR Chambres − AK
> ☐ CC BI, BK, BL, BM, BN = Transelect TOTAUX correspondants
> ☐ BU = Recap Argent Reçu, BV = −DR Remb Serveur, BW = −SJ Pourb Charge
> ☐ BY = −Recap Due Back Réception, CA = Recap Surplus/Déficit
> ☐ DC = 0.00 (ou résiduel circulaire ≤ 0.15 identifié et documenté)

### Coverage assessment

The 21-point checklist does **not** cover every column individually. It groups F&B (cols 9-35) into one check (#2), taxes into one (#6), and CC debits into one (#7). The critical, error-prone columns each get their own check (36, 44, 48, 72, 73, 74, 76, 78, 83). The structural items (Club Lounge, InterHotel, HP Autres, Débourse) have dedicated checks (#18-21). The checklist targets ~30 specific columns out of 86 but those are the only ones that are ever non-zero in practice.

---

## Part 5 — Error Patterns Library

Every documented symptom, organised by DC signature. Each entry: **symptom → root cause → fix column → source**.

### Sign errors

- **DC = 2×|DR Internet| (positive)** → DR Internet entered with wrong sign in col 48 → fix col 48 = DR Internet (keep negative) + SJ Bqt Internet → [Sheraton] §9, [Complete] §5.3, [Method] §6.1, §8.3 (Mar 14 example)
- **DC = +564.98 on Sunday** → Discover entered positive on Sunday (batch weekend reversed sign) → fix col 61 Discover = negative → [Sheraton] Table 9, Table 17 R6
- **BV positive** → must always be negative → fix col 73 → [Sheraton] §15 P136
- **EQ. DIVERS +565 on col 31** → SJ debit entered as positive → fix col 31 = 0 (if already in DR) or = −565 → [Sheraton] §15 P134, [Complete] Table 2 Fév 4

### Wrong source

- **DC = ±57.07 on Mar 12** → col 73 populated from Recap Due Back N/B instead of DR Remb Serveur → fix col 73 = −(DR Remb Serveur) → [Complete] Table 2 Mar 12, [Method] §8.4
- **DC = ±741 on Mar 11** → col 83 populated from AR Guest Folios instead of DR Facture Direct → fix col 83 = DR FD (CIRCULAR — actual DC impact from fixing col 83 alone = 0, but the wrong value is still wrong) → [Complete] Table 2 Mar 11, [Sheraton] Table 5
- **col 83 = FD − DEPOT UTIL** → DEPOT UTIL wrongly subtracted from col 83; it belongs in col 44 → fix col 83 = FD, col 44 = DR GL − DEPOT UTIL → [Sheraton] Table 5 R2 (erreur du 30 mars)

### Omission (missing entries)

- **DC = ±9.99, ±19.98, ±49.95** → InterHotel XferIn missing from col 46 → fix col 46 += DR.interhotel_xferin OR accept as declared variance → [Sheraton] Table 17 R2, §15 P144
- **DC = ±HP Promo total** → HP Promo not deducted from cols 9/14/35 → recompute credits minus HP Promo → [Sheraton] Table 17 R3, §15 P146
- **DC = ±X24** → Discover col 61 not entered; X24 uncompensated → fix col 61 per X24 sign rule → [Sheraton] Table 17 R4, §15 P148
- **DC = ±(FD − AR)** → col 41 GEAC compensation missing → fix col 41 = −(FD − AR) → [Sheraton] Table 17 R5, §15 P147
- **DC = 165.45 (Mar 4)** → DR Nettoyeur 153.95 not entered in col 40 + X24 11.50 → fix col 40 = 153.95, then compensate X24 → [Method] §8.1
- **DC = −2.51 residual after X24 (Mar 13)** → HP Autres 2.51 not deducted (HP Autres has no dedicated col) → deduct manually from an F&B column → [Complete] Table 2 Mar 13, [Method] §8.2
- **BQ/BR = 0 despite HP containing pourboires** → HP pourb not entered in cols 68/69 → [Sheraton] §15 P145

### Wrong column

- **EQ. DIVERS entered in AF instead of AQ** → depends on credit vs debit: credit → AQ (col 42), debit → AF (col 31) → [Sheraton] §15 P139
- **Club Lounge deducted from J when it should be added back** → CL negative case: CL adds back to col 9 via sign rule → [Sheraton] §15 P141

### Macro-not-run

- **DC very large (>10,000)** → cols 60-65 empty AND col 41 empty → macros calcul_carte and geac not run → run macros → [Complete] Table 2 Mar 24, [Method] §10.4
- **Mar 24 DC = −13,716.54** → col 48 sign + col 83 source + macros combined → fix each → [Complete] Table 2 Mar 24

### Circular / acceptable residuals

- **DC ≤ 0.15** → circular residual from room-charge folio loop → ACCEPT → [Sheraton] §13 P99-P105, Table 18
- **GEAC "doesn't balance" checkbox ON** → variance officially acknowledged → no extra DC entry required → [Sheraton] Table 7, Table 17 R9
- **AR Invoices = AR Payments** → they self-cancel; col 83 is unaffected → do NOT subtract them from col 83 → [Complete] §5.1 P36, Table 2 Mar 24

### Pattern recognition heuristics ([Method] §10)

- **|DC| exactly equals a DR Today value** → that value is probably missing from its jour column. Check all DR items against their columns.
- **DC ≈ 2 × small amount** → sign error (most common: DR Internet).
- **DC close to X24 but off by small δ** → the δ is usually HP Autres, DR Débourse, or a missing manual adjustment.
- **DC very large (>10,000)** → macros not run, or col 83 wrong source, or multiple errors compounding.
- **DC tiny (<5)** → rounding, tiny HP Autres, or tiny DR Débourse.

---

## Part 6 — Specific Item Handling

### InterHotel XferIn

- **What:** Inter-hotel transfer credit posted to DR page 7 "InterHotel XferIn Today".
- **Frequency pattern:** ~9.99 per day of accumulation. Monday = 1 day = 9.99; Tuesday = 2 days = 19.98; Sunday often = 5 days = 49.95. Verify exact amount in DR p.7 every day ([Sheraton] Table 12 R1-R2).
- **Structural location:** Already inside Bal_Ferm via New Balance. No dedicated credit column in the jour by default ([Complete] §5.7 P48).
- **Canonical target:** col 46 (AU — Autre Revenu). The AU formula explicitly includes it ([Sheraton] §8 Table 13).
- **Two acceptable auditor outcomes (user rule, 2026-04-08):**
  1. **Auto-route**: webapp one-click adds the exact amount to col 46 → DC loses the 9.99 offset.
  2. **Declared variance**: auditor leaves col 46 untouched; webapp labels the residual DC as "InterHotel XferIn = 9.99" and the auditor accepts it.
- **Unacceptable outcome:** unexplained DC of 9.99/19.98/etc.

### GEAC reconciliation

- **Sheet:** `geac_ux` inside the RJ workbook.
- **Top section (rows 3-11):** CC reconciliation. Row 5 = Daily Cash Out (bank), Row 7 = Deposits received, Row 9 = Total, Row 11 = Daily Revenue, Row 14 = variance (should be 0) ([Complete] §11 P85).
- **Bottom section (Balance Sheet, from row 36):** Row 36 = Balance Today (DR vs Guest Ledger). Row 40 = Facture Direct vs Front Office Transfers (AR). Row 52 = New Balance (DR vs GL) — **same variance as row 36, cumulative, not additional** ([Complete] §5.9 P52, §11 P86-P88).
- **Row 55/56:** pre-computed compensation for col 41. = −(FD − AR).
- **Code extraction:** `parse_rj_geac` reads `ws.cell_value(40, 1)` for FD and `ws.cell_value(40, 6)` for AR (row index 40 = row 41 1-based).
- **Exception (the checkbox):** if "Check box if amounts don't balance" is ticked, the variance is officially recognised — no col 41 entry beyond what's there → typically happens Mondays after a Sunday with large PANNE VISA ([Sheraton] Table 7).

### Transelect X24

- **What:** Variance between POSITOUCH (restaurant POS) totals and bank deposits for restaurant CC.
- **Location:** `transelect` sheet, row 13 col 24 (`parse_rj_transelect` reads `ws.cell_value(13, 24)`).
- **Computation:** `X24 = Total bank restaurant − Total POSITOUCH restaurant`
  - Total bank = sum of Bank Report column (Réception Chambres section, Visa+Master+Amex+Débit for restaurant)
  - Total POSITOUCH = restaurant/banquet/spesa section TOTAL row, POSITOUCH column ([Sheraton] §6.1 P49-P53)
- **Sign convention:**
  - Weekday (Mon–Sat): X24 negative (bank < POSITOUCH, pannes unrecovered) → col 61 (Discover BJ) = **positive** (−X24)
  - Sunday: X24 positive (Sat+Sun batch deposits Monday) → col 61 = **negative** ([Sheraton] Table 8, Table 9)
- **Panne impact:** PANNE VISA/MASTER/INTERACT/AMEX create the bank-vs-POS gap. PANNE LIEN HOTEL is not recoverable — it is already in New Balance, no separate entry ([Sheraton] §6.2 P58-P61).
- **Target column:** col 61. Alternate: col 5 (Boi_Link) manual compensation if Discover route not used.

### Recap cash count workflow

**Source sheet:** `Recap` inside the RJ workbook.

**Workflow (auditor inputs marked ⌨️):**

1. Comptant LightSpeed (from LightSpeed system) + Comptant Positouch ⌨️ = Total cash
2. Minus Remb Gratuité (typed from Recap's own row)
3. Minus Remb Client
4. Yields Due Back Réception ⌨️ and Due Back N/B
5. Surplus/Déficit ⌨️ = computed by the auditor after counting the physical drawer

**Rows consumed by the balancer ([Complete] §10 structure, `parse_rj_recap`):**
- `argent_recu` (row ~23-24) → col 72
- `remb_grat` → (not a direct jour col; explains col 74 indirectly)
- `remb_client` → informational
- `due_back_rec` (row ~16) → col 76 (inverted sign)
- `due_back_nb` → informational only (NEVER col 73 — that's DR Remb Serveur)
- `surplus_deficit` (row ~19) → col 78 (inverted sign)

### Club Lounge

- **Source:** DR p.3 "Club Lounge" section. Fields: Nourriture Lounge, Alcool Lounge, Bière Lounge, Minéraux Lounge, Vin Lounge, Autres Lounge.
- **Code computation:** `cl_total = abs(cl_nourr) + abs(cl_vin) + abs(cl_alcool) + abs(cl_biere) + abs(cl_min) + abs(cl_autres)` then `cl_nourr_total = cl_total`.
- **Deduction rule:**
  - CL positive (normal — CL active): deduct from col 9 (Piazza Nourriture) via `calc[9] -= cl_nourr`
  - CL negative: **add back** (handled via NB/BF differently — see [Sheraton] Table 17 R12 "CL négatif: gérer via NB/BF différemment")
- **G4 interaction:** When CL is active, `G4 = cl_total` and `col 36 = DR.chambres_total − G4`; `col 57 Diff Forfait = −(forfait − G4)`. This routes the CL amount out of Chambres into the Forfait diff.
- **Warning from code:** `"Club Lounge: Nourr=..., Autres=... -- deduit de col 9"`

### HP Admin vs HP Promo

Both types produce the same kind of deduction but live in different HP paiement codes (14-Administration vs 15-Promotion).

- **Food/Bev items** (Nourriture, Boisson, Biere, Vin, Mineraux) → deducted from the matching F&B credit column (cols 9, 10, 11, 12, 13 for Piazza; col 14 for Spesa Nourr; etc.). **Both Admin AND Promo deducted.**
- **Tabagie items** → deducted from col 35 (Tabag)
- **Pourboire** → cols 68 (Admin) / 69 (Promo) — **ALWAYS POSITIVE** as debits
- **Autres** → NO dedicated column. Must be manually deducted from an F&B column or accepted as variance.
- **Cross-check:** HP Journalier row 33 Total Somme de Total MUST equal SJ ADMINISTRATION + SJ HOTEL PROMOTION. If not: HP file or SJ is broken.

### Débourse (DR p.5)

- **What:** DR page 5 "Débourse" section, primarily the Remboursement Serveur line.
- **Column mapping:** Remb Serveur → col 73. Other Débourse sub-items (e.g. small 0.12 values) have no dedicated column.
- **Fallback:** if a small Débourse residual cannot be routed, treat it analogously to InterHotel: declare it as variance or deduct from col 73.
- **Source:** [Sheraton] Table 2 R57, [Complete] §3.2 P17, [Method] §4.2 P66.

### HP Autres

- **What:** The `Autres` column in HP `données` rows (non-food, non-pourb items — e.g. taxe cadeau, frais divers).
- **Column:** NONE.
- **Handling:** manually deduct from an F&B column OR declare as variance. Typical magnitudes are tiny (2.51, 0.80).
- **Detection:** Sum of HP deductions applied to jour < (SJ Admin + SJ Promo). The gap IS the Autres value.
- **Source:** [Method] §6.5, §8.2 (Mar 13 example).

---

## Part 7 — Source Document Map

### `sales_journal.txt` (SJ)

Plain-text POS export. Sections (department headers): **PIAZZA, BANQUET, CHAMBRES, SPESA, CAFE LINK, BAR CUPOLA**.

**Debit-name trick** ([Method] §2.2 P15): The SJ has a single numeric column; debits vs credits are distinguished by known debit names (VISA, MASTERCARD, AMEX, INTERAC, CHAMBRE, PANNE*, ADMINISTRATION, HOTEL PROMOTION, FORFAIT, DEPOT UTIL, POURBOIRE CHARGE, CERT CADEAU).

**Fields consumed by the jour:**

| SJ line | Consumed by | Formula role |
|---|:-:|---|
| PIAZZA NOURRITURE | col 9 | base credit |
| PIAZZA ALCOOL | col 10 | base credit |
| PIAZZA BIERES | col 11 | base credit |
| PIAZZA NON ALCOOL BAR | col 12 | base credit |
| PIAZZA VINS | col 13 | base credit |
| PIAZZA POURB À PAYER | col 29 | base credit − HP pourb |
| PIAZZA EQ AUDIO (debit) | col 30 | subtracted (bqt − piaz) |
| PIAZZA LOC SALLE | col 32 | base credit |
| PIAZZA TAB | col 35 | base credit |
| PIAZZA PAUSE SPESA | col 4 | base credit |
| PIAZZA INTERNET | col 48 | added |
| PIAZZA FR/ETAGE | col 46 | added |
| CHAMBRES NOURRITURE | col 19 | base |
| CHAMBRES ALCOOL | col 20 | base |
| CHAMBRES BIERES | col 21 | base |
| CHAMBRES NON ALCOOL BAR | col 22 | base |
| CHAMBRES VINS | col 23 | base |
| CHAMBRES FR/ETAGE | col 46 | added |
| BANQUET NOURRITURE | col 24 | base |
| BANQUET ALCOOL / BIERES / NON ALCOOL BAR / VINS | cols 25-28 | base |
| BANQUET POURB À PAYER | col 29 | part of sum |
| BANQUET EQUIP AUDIO VISUEL | col 30 | base |
| BANQUET EQ. DIVERS | col 31 (or 42) | sign-sensitive |
| BANQUET LOC SALLE | col 32 | base |
| BANQUET SOCAM | col 33 | base |
| BANQUET PAUSE SPESA | col 4 | base |
| BANQUET VESTIAIRE | col 53 | base |
| BANQUET INTERNET | col 48 | base |
| SPESA NOURRITURE | col 14 | base credit |
| SPESA TABAGIE | col 35 | base |
| SPESA POURBOIRE A PAYER | col 29 | part of sum |
| SPESA INTERNET | col 48 | added |
| TVQ | col 49 | part of sum |
| TPS | col 50 | part of sum (minus panne TPS) |
| FORFAIT (debit) | col 57, G4 | diff calc |
| ADMINISTRATION (debit) | HP cross-check | must equal HP Admin total |
| HOTEL PROMOTION (debit) | HP cross-check | must equal HP Promo total |
| POURBOIRE CHARGE (debit/credit) | col 74 | inverted |
| CERT CADEAU (debit) | col 79 | base |
| DEPOT UTIL (debit) | col 44 | subtracted |
| PANNE VISA/MASTER/INTERACT/AMEX/LIEN (debit) | col 50 | TPS-on-pannes subtracted |

### `daily_revenue.pdf` (or .xls — DR)

7-page PMS export (OPERA).

| Page | Section | Extracted into |
|:-:|---|---|
| 1 | Chambres par catégorie | col 36 (sum of Room Chrg lines Today) |
| 1 | TELEPHONE LOCAL / INTERURBAIN / PUBLICS | cols 37, 38, 39 |
| 2 | NETTOYEUR (Dry Cleaning) | col 40 |
| 2 | SONIFI | col 45 |
| 2 | LOCATION BOUTIQUE | col 47 |
| 2 | MACHINE LIT PLIANT | col 46 |
| 2 | FAX & PHOTOCOPIES | col 55 |
| 2 | MASSAGE | col 52 |
| 2 | AUTRE A PAYER (Taxable) | col 54 |
| 2 | INTERNET | col 48 ⚠ can be negative |
| 2 | AUTRES GRAND LIVRE + GL T | col 44 |
| 2 | GIVEX | col 79 |
| 3 | TAXE HEBERGEMENT | col 51 |
| 3 | TPS CHAMBRES, TVQ CHAMBRES | cols 50, 49 |
| 3 | Club Lounge (Nourr, Alcool, Biere, Min, Vin, Autres) | col 9 deduction, G4 |
| 3-4 | F&B by OPERA dept | cross-reference only |
| 5 | TPS/TVQ Autres, TPS/TVQ Internet | cols 50, 49 (algebraic) |
| 5 | Comptabilité TPS/TVQ | cols 50, 49 |
| 5 | Débourse — Remboursement Serveur | col 73 (inverted) |
| 5 | Autre À Payer Non-Taxable | col 46 |
| 5-6 | Settlements: Amex/Visa/MC/Debit/Cheque | cross-reference to Transelect |
| 6 | FACTURE DIRECT | col 83 (AUTHORITATIVE for col 83) |
| 6 | Bon d'Achat + Gift Card + Bon Remanc | col 79 |
| 6 | CERTIFICAT CADEAUX | col 79 |
| 7 | Adv Dep Applied / Cancel / DNA | Adv Dep formula |
| 7 | **InterHotel XferIn** | col 46 (or declared variance) |
| 7 | Balance Today / Prev Day / New Balance | col 3 (BF) |

### `ar_summary.pdf` / `.xls` (AR)

One page. Fields: Balance Previous Day, Front Office Transfers (Guest Folios), Adjustments, Invoices, Payments, End of Day balance.

**Critical rule:** col 83 is **DR Facture Direct, not AR Guest Folios**. AR Summary is used ONLY for GEAC col 41 reconciliation (FD vs AR comparison). If AR Invoices == AR Payments, they self-cancel and do NOT affect col 83 ([Complete] §5.1 P36).

### `hp.xlsx` (HP — Hotel Promotion)

**Sheets:** `données`, `Journalier`, `mensuel`.

**`données` sheet:** Row 12 = headers. Rows 13-1000 = transactions. Columns:

| Col | Field |
|:-:|---|
| A | Date |
| B | Aera (Piazza / Tabagie / Banquet / …) |
| C | Nourriture |
| D | Boisson |
| E | Biere |
| F | Vin |
| G | Mineraux |
| H | Tabagie |
| I | Autres |
| J | Pourboire |
| K | Paiement (14-Admin / 15-Promo / 17-Promesse) |
| L | Total |
| M | raison |
| N | qui |

Named range `_xlnm.Database = A12:O1000`. DSUM criteria in rows 1-2.

**`Journalier` sheet:** Pivot, filter by day via cell B3. Row 32 = pourboires (→ cols 68/69). Row 33 = Grand Total (must equal SJ Admin + SJ Promo).

### `advance_deposit.xls` (AD)

Fields: Yesterday balance, Received Today, Applied Today, Cancelled, DNA (No-Shows).

**Formula:** `Today = Yesterday + Received − Applied − Cancelled − DNA`. Feeds col 3 (BF).

### `market_segment.pdf` / `.xls` (MS)

Not in the jour formula chain; used for market-segment reporting only. Extracted for completeness but does NOT feed any balancing column.

### `transelect` (RJ internal sheet)

Not a separate file — a sheet inside the RJ Excel.

**Structure ([Complete] §10 P74-P83):**

- Rows 6-7: terminal headers (BAR A/B/C, SPESA D, ROOM E, EXTRA, Banquet)
- Rows 8-12: amounts by CC type × terminal
- Row 13: totals per terminal. **Col 21 = TOTAL1, Col 22 = TOTAL2, Col 23 = POSITOUCH, Col 24 = VARIANCE (X24)**
- Rows 17-24: réception — Bank Report (FreedomPay) vs Daily Revenue; Escompte, NET
- Row 28: TOTAUX bank deposits by CC type
- Row 31: TOTAUX TRANSELECT (POS portion)
- Row 34: TOTAUX GEAC (OPERA portion, net after escompte for Amex)
- **Row 37: total_carte_crédit → copied by macro `calcul_carte` into jour cols 60-65**

**X24 rule:** X24 must = 0. Discover is adjusted manually to force X24 → 0.

### `geac_ux` (RJ internal sheet)

Not a separate file.

**Structure ([Complete] §11 P85-P89):**

- Rows 3-11: CC reconciliation — Row 5 Daily Cash Out, Row 7 Deposits, Row 9 Total, Row 11 Daily Revenue. Must match.
- Row 36: Balance Today (DR vs Guest Ledger) — variance detection
- Row 40 (code reads index 40): Facture Direct vs Front Office Transfers (AR). Compensation if differ.
- Row 52: New Balance (DR vs GL) — same variance as row 36, cumulative
- **Row 55: compensation amount → col 41**. If FD=AR and CC balances, row 55 = 0.

### `Recap` (RJ internal sheet)

See Part 6 §Recap cash count workflow.

---

## Part 8 — Manual Auditor Inputs

These are fields the auditor types that CANNOT be derived from source documents. The webapp MUST surface them as required inputs.

| Input | Code parameter | Role | Source of truth |
|---|---|---|---|
| **Auditor name** | controle row 1 | audit metadata | Human |
| **Day** | controle row 2-4 | date | Human / system |
| **Month, Year** | controle row 2-4 | date | Human / system |
| **g4_montant** | `g4` in `calculate_jour` | col 36 Chambres subtraction AND col 57 Diff Forfait adjustment | Auditor judgment (unless CL total overrides) |
| **adj_piaz** | `adj_piaz` | Manual adjustment to col 9 (Piazza Nourr) | Auditor |
| **adj_mar** (alias adj_spesa) | `adj_mar` | Manual adjustment to col 14 (Spesa Nourr) | Auditor |
| **adj_bqt** | _(not present in code)_ | Potential manual adjustment to col 24 | Auditor — TBD if needed |
| **adj_sch** | _(not present in code)_ | Potential manual adjustment to col 19 | Auditor — TBD if needed |
| **club_nourr_override** | `club_nourr_override` | Overrides computed CL total for col 9 deduction | Auditor |
| **club_autres_override** | `club_autres_override` | Overrides CL Autres bucket | Auditor |
| **Comptant Positouch** | Recap input | Cash count | Auditor |
| **Due Back Réception** | Recap input → col 76 | Cash due-back | Auditor |
| **Surplus/Déficit** | Recap input → col 78 | Physical drawer count vs system | Auditor |
| **Banquet pourb split** | controle row 28 | Pourboire allocation between waiters | Auditor |
| **SAC pourb split** | controle row 29 | Pourboire allocation | Auditor |
| **InterHotel declared-variance flag** | _(webapp only)_ | Auditor accepts DC residual = InterHotel amount | Auditor |
| **GEAC "doesn't balance" checkbox** | geac_ux cell | Variance acknowledgement | Auditor |
| **col 5 (Boi_Link) manual compensation** | direct cell | Residual X24 absorption | Auditor |
| **col 6 (Bie_Link) HP fallback** | direct cell | Used only when no detailed HP file | Auditor |

---

## Part 9 — Tolerances and Edge Cases

### DC tolerance

- **DC ≤ 0.15 circular residual** → ACCEPT. Arises from folio-loop charges that self-balance ([Sheraton] Table 18).
- **Code threshold:** `abs(dc) < 0.02` for the "DC = 0" 21-point check. The Guide's 0.15 is the looser human tolerance; the code uses a stricter automated tolerance.

### GEAC "doesn't balance" checkbox exception

When the auditor ticks "Check box if amounts don't balance" in `geac_ux`, the variance is officially acknowledged. No additional DC entry is needed. Typical trigger: Mondays after a Sunday with large PANNE VISA ([Sheraton] Table 7).

### Sunday batch weekend pattern

Banks don't deposit Sundays. Monday's deposit includes Sat+Sun. Result:
- Sunday X24 = POSITIVE (bank > POSITOUCH because includes Saturday)
- Sunday col 61 (Discover BJ) = NEGATIVE (reversed from weekday)
- Following Monday: X24 returns to normal (negative if pannes exist)

Source: [Sheraton] Table 9, Table 17 R6.

### Month-end

Not explicitly documented. The jour row for day 31 (or 30/28/29 depending on month) is the last; BF rolls to first of next month in the next workbook. **TBD: Guide is silent on special month-end handling.**

### Holidays

Not documented. **TBD.**

### Zero-activity outlets

When Banquet has no entries, all banquet cols (24-28, 30-33, 53) = 0. The formulas still evaluate to 0 — no special case required.

### Panne-lien hotel

PANNE LIEN HOTEL transactions are non-recoverable; they live in New Balance. No separate jour entry ([Sheraton] §6.2 P61).

### Contradictions flagged between guides

1. **[Sheraton] Table 2 R4 says "Pas de déduction HP alcool"** but [Complete] Table 0 R5 and the code DO deduct HP Piazza boisson. → **Code/[Complete] wins**. The Sheraton guide's note likely reflects the common case (HP rarely has alcohol items) rather than an exclusion rule.

2. **Letter labels vs index math (see Part 1)**: Guide letters match physical Excel columns, not pure alphabetic index. Always use indices from `COL_NAMES`, treat letters as human labels only.

3. **col 79 (CB)** — [Sheraton] Table 2 R45-R46 lists both "Gift Card/Bon" and "Cert Cadeau" at CB, but they're distinct line items in DR. Code conflates into `SJ.cert_cadeau + DR.givex`. → **TBD: if a day has non-trivial Bon d'Achat separate from Cert Cadeau, the code may under-credit col 79.**

4. **Row 55 vs Row 56 for GEAC compensation**: [Complete] §11 P89 says row 55; [Sheraton] §5.2 P42 mentions row 56. Code reads row index 40. → The three refer to the same compensation cell; the exact row depends on geac_ux layout version. **Code wins** (it reads the active FD/AR cells directly).

---

## Part 10 — Agent Reading Protocol (expanded)

Every future agent touching balancing must:

1. **Read Parts 1-3 before making any claim** about what a column "should" be, what DC "should" equal, or whether something "is a bug."
2. **Cite the Guide when making a claim.** "Col 46 should include InterHotel" alone is insufficient. "Col 46 should include InterHotel per [Sheraton] §8 Table 13" is correct.
3. **Map every diff to an error pattern in Part 5** before calling it a bug. If no pattern matches, the diff is a candidate for new documentation, not automatic code-change.
4. **For DC ≠ 0, walk the 4-class reconciliation in Part 3** before declaring unbalanced:
   - Class 1: X24 → col 61 Discover
   - Class 2: GEAC FD−AR → col 41
   - Class 3: Recap S&D → col 78
   - Class 4: InterHotel XferIn → col 46 OR declared variance (user rule 2026-04-08)
5. **Column formulas in Part 2 are authoritative.** `calculate_jour` may have bugs, but the Guide is the source of truth. If code disagrees with Guide, surface the contradiction to the user BEFORE making changes.
6. **Never invent DC compensation.** Residuals > 0.15 that can't be explained must be surfaced to the auditor ([Sheraton] Table 18).
7. **Manual auditor inputs (Part 8) are sacrosanct.** Do not fabricate values for g4_montant, adj_piaz, adj_mar, Recap inputs, etc. If they're missing, ask.
8. **When in doubt, quote the Guide.** This file is self-contained by design.

### How the balancer code should read this file

Pseudocode for a future "read the master doc first" enforcement:

```python
# At the start of any BalancerService.check_balance() call
with open('docs/BALANCING_RULES_MASTER.md') as f:
    _ = f.read()  # Ensure the file exists and is readable.
# The LLM agents attached to this service are instructed to reference
# this file; the Python code itself enforces existence, not content.
```

---

## Appendix A — Column formula coverage scorecard

| Category | Count |
|---|:-:|
| Columns with explicit Guide formula | **37** |
| Columns consumed by the balancer (`COL_NAMES`) | 53 |
| Columns in jour sheet total | ~117 |
| Columns with no documented formula (gaps) | col 5, 6, 33, 34, 42(partial), 43, 52(partial), 55(partial), 56, 58, 59, 66, 67, 70, 71, 75, 77, 80, 81, 82, 84, 85, 86 |

**37 of ~86 relevant columns have explicit documented formulas.** The remaining columns are either always-zero, macro-populated, or handled as fallback/manual-compensation columns. Every column that ever contains a non-zero value during normal operation IS documented.

---

## Appendix B — Decision tree for DC ≠ 0 ([Method] §9, verbatim)

> When DC ≠ 0, follow this exact order:
>
> **Step 1:** Check Bal_Ferm (col 3). Calculate −(DR New Balance) − (Adv Dep Today). If doesn't match col 3, fix the BF first. Check each Adv Dep component.
>
> **Step 2:** Check col 83 (Transfer C/R). Is it DR Facture Direct or AR Guest Folios? If AR, change to DR FD. Remember: col 83 is CIRCULAR — changing it changes BF too, so net DC impact = 0. This column never explains a DC error by itself.
>
> **Step 3:** Check col 48 (Internet). Is DR Internet negative and col 48 positive? Impact = 2 × |DR Internet|.
>
> **Step 4:** Check col 73 (Remb Serveur). Must be DR, not Recap.
>
> **Step 5:** Check all F&B credits (cols 9-35). For each: SJ − HP − adj.
>
> **Step 6:** Check col 36 (Chambres). DR Chambres Total − G4. Verify G4.
>
> **Step 7:** Check cols 60-65 (CC debits). Should match Transelect TOTAUX row 37. If not, macro calcul_carte not run.
>
> **Step 8:** Check for missing DR items. Go through EVERY non-zero Today value in DR and verify it appears somewhere in the jour. Key ones to miss: Nettoyeur (40), Fax (55), Sonifi (45), Massage (52), Autre À Payer (54), GiveX (79).
>
> **Step 9:** Check for items without columns. DR Débourse, DR InterHotel XferIn, HP Autres, DR Club Lounge.
>
> **Step 10:** Exhaustive number search. If still unexplained, combinatorial search over every number from every document.
>
> **Step 11:** Decompose the final DC. DC = X24 + GEAC + Recap + identified errors. If DC = sum of known variances, compensate with col 5 and col 41. Otherwise surface residual to auditor.

---

_End of BALANCING_RULES_MASTER.md — authoritative as of 2026-04-08._
