# RJ Workbook Documentation Index

**Last Updated:** 2026-01-15
**Total Sheets in Workbook:** 38
**Documented Sheets:** 11 (core sheets)

---

## Quick Reference

| # | Sheet | Purpose | Doc File |
|---|-------|---------|----------|
| 1 | controle | Configuration & settings | [01_controle.md](01_controle.md) |
| 2 | rj | Main daily report | [02_rj.md](02_rj.md) |
| 3 | jour | Master data journal | [03_jour.md](03_jour.md) |
| 4 | Recap | Cash reconciliation | [04_RECAP.md](04_RECAP.md) |
| 5 | DUBACK# | DueBack tracking | [05_DUEBACK.md](05_DUEBACK.md) |
| 6 | transelect | Credit card reconciliation | [06_transelect.md](06_transelect.md) |
| 7 | depot | Bank deposits | [07_depot.md](07_depot.md) |
| 8 | geac_ux | GEAC system balance | [08_geac_ux.md](08_geac_ux.md) |
| 9 | Nettoyeur | Staff gratuities detail | [09_Nettoyeur.md](09_Nettoyeur.md) |
| 10 | somm_nettoyeur | Gratuities summary | [10_somm_nettoyeur.md](10_somm_nettoyeur.md) |
| 11 | SetD | Settlement/suspense | [11_SetD.md](11_SetD.md) |
| 12 | **Procédure** | Complete back audit procedure | [12_procedure_back_complete.md](12_procedure_back_complete.md) |

---

## Data Flow Overview

```
                         ┌─────────────────────┐
                         │     controle        │
                         │  (Configuration)    │
                         │  - Date settings    │
                         │  - Named ranges     │
                         └─────────┬───────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
              ▼                    ▼                    ▼
    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
    │      jour       │  │   transelect    │  │     geac_ux     │
    │ (Master Data)   │  │ (Credit Cards)  │  │ (GEAC Balance)  │
    │ - All daily tx  │  │ - POS cards     │  │ - Room charges  │
    │ - Department    │  │ - Variance      │  │ - Guest ledger  │
    │   revenue       │  │ - Discount calc │  │                 │
    └────────┬────────┘  └────────┬────────┘  └────────┬────────┘
             │                    │                    │
             │         ┌──────────┴──────────┐        │
             │         │                     │        │
             ▼         ▼                     ▼        │
    ┌─────────────────────────────────────────────────┼────────┐
    │                        rj                       │        │
    │               (Main Daily Report)               │        │
    │   - Consolidates all revenue                    │        │
    │   - Statistics                                  │        │
    │   - Credit card summary                         │        │
    │   - Balance calculation                         │        │
    └─────────────────────────────────────────────────┼────────┘
                                                      │
             ┌────────────────────────────────────────┘
             │
             ▼
    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
    │    DUBACK#      │  │     Recap       │  │     depot       │
    │ (DueBack Track) │  │(Cash Reconcile) │  │ (Bank Deposit)  │
    │ - Reception     │  │ - Cash totals   │  │ - Daily amounts │
    │ - Receptionists │  │ - Refunds       │  │ - Account track │
    │ - Column Z calc │  │ - DueBack       │  │                 │
    └────────┬────────┘  │ - Surplus/Def   │  └─────────────────┘
             │           └────────┬────────┘
             │                    │
             └────────────────────┘
                        │
                        ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                    Supporting Sheets                         │
    │                                                              │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
    │  │ Nettoyeur   │  │somm_nettoy  │  │   SetD      │          │
    │  │ (Tips)      │  │ (Summary)   │  │ (Suspense)  │          │
    │  └─────────────┘  └─────────────┘  └─────────────┘          │
    └─────────────────────────────────────────────────────────────┘
```

---

## Key Connections Summary

### jour → Other Sheets

| jour Column | Destination | Sheet |
|-------------|-------------|-------|
| BY (Due back reception) | Column B | DUBACK# |
| BU (Argent recu) | Row 24 | Recap |
| BV (Remb. Serverveurs) | Row 12 | Recap |
| BW (Remb. Gratuite) | Row 11 | Recap |
| CA (Surplus/Def) | Row 19 | Recap |
| C (Diff.Caisse) | Row 49 | rj |

### controle → All Sheets

| controle Value | Usage |
|----------------|-------|
| vjour (day) | Column selection |
| idate (date) | Headers |
| vcie (hotel name) | Report headers |

### Recap ↔ DUBACK#

| Recap | DUBACK# | Notes |
|-------|---------|-------|
| Row 16 (Due Back Réception) | Column B (daily) | ABS value |
| L19 (calculation) | Column B | With sign |

---

## VBA Macros by Sheet

### Navigation Macros
| Macro | Sheet |
|-------|-------|
| `aller_jour()` | jour |
| `aller_trans()` | transelect |
| `aller_depot()` | depot |
| `aller_recap()` | Recap |
| `geac_ux_report()` | geac_ux |

### Clear Macros
| Macro | Sheet |
|-------|-------|
| `efface_recap()` | Recap |
| `Eff_depot()` | depot |
| `eff_trans()` | transelect |
| `efface_rapport_geac()` | geac_ux |

### Print Macros
| Macro | Sheet |
|-------|-------|
| `Imp_RJ()` | rj |
| `imprime_recap()` | Recap |
| `imp_depot()` | depot |
| `imp_trans()` | transelect |

### Data Transfer Macros
| Macro | From | To |
|-------|------|-----|
| `envoie_dans_jour()` | Recap H19:N19 | jour ar_[day] |
| `calcul_carte()` | transelect | jour CC_[day] |
| `calcul_sal()` | controle | salaires |

---

## Named Ranges Reference

| Range | Location | Purpose |
|-------|----------|---------|
| `vjour` | controle B3 | Current day |
| `idate` | controle B28 | Current date |
| `vcie` | controle B20 | Hotel name |
| `ar_[1-31]` | jour | Argent Recu rows |
| `CC_[1-31]` | jour | Credit Card rows |
| `j_[1-31]` | jour | Day navigation |
| `home_recap` | Recap | Navigation |
| `home_trans` | transelect | Navigation |
| `home_depot` | depot | Navigation |
| `eff_recap` | Recap | Clear range |
| `eff_trans` | transelect | Clear range |
| `eff_depot` | depot | Clear range |

---

## All Sheets in Workbook

| # | Sheet Name | Documented |
|---|------------|------------|
| 1 | EJ | No |
| 2 | **controle** | Yes |
| 3 | Analyse 101100 autre | No |
| 4 | Analyse 100401 | No |
| 5 | Diff.Caisse# | Partial |
| 6 | Feuil8 | No |
| 7 | autre GL | No |
| 8 | **rj** | Yes |
| 9 | **jour** | Yes |
| 10 | salaires | No |
| 11 | Feuil1 | No |
| 12 | **depot** | Yes |
| 13 | diff_forfait | No |
| 14 | Sonifi | No |
| 15 | Internet | No |
| 16 | SOCAN | No |
| 17 | résonne | No |
| 18 | Vestiaire# | No |
| 19 | **DUBACK#** | Yes |
| 20 | **somm_nettoyeur** | Yes |
| 21 | **Nettoyeur** | Yes |
| 22 | **SetD** | Yes |
| 23 | AD | No |
| 24 | Massage | No |
| 25 | **transelect** | Yes |
| 26 | 201802 Ristourne | No |
| 27 | **Recap** | Yes |
| 28 | **geac_ux** | Yes |
| 29 | Auditeur | No |
| 30 | Ristourne Analyse | No |
| 31 | Rapp_p1 | No |
| 32 | Rapp_p2 | No |
| 33 | Rapp_p3 | No |
| 34 | Etat rev | No |
| 35 | Budget | No |
| 36 | Feuil6 | No |
| 37 | Feuil7 | No |
| 38 | Feuil2 | No |

---

## Implementation Priority

### High Priority (Core Audit Flow)
1. Recap - Cash reconciliation
2. DUBACK# - DueBack tracking
3. transelect - Credit card reconciliation
4. depot - Bank deposits

### Medium Priority (Data Entry)
5. jour - Master data (mostly auto-filled)
6. Nettoyeur - Staff gratuities
7. geac_ux - GEAC balancing

### Lower Priority (Reports/Supporting)
8. rj - Summary report (output only)
9. controle - Settings
10. somm_nettoyeur - Summary
11. SetD - Suspense tracking
