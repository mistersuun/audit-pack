# Analyse des Macros VBA du RJ

**Date:** 2026-01-02
**Source:** Extraction depuis `Rj 12-23-2025-Copie.xls`

---

## 🔍 MACROS "TURBO" D'EFFACEMENT TROUVÉES

### 1. **efface_recap()** - Effacer Recap

**Ligne:** 5609-5621
**Module:** Module12.bas

```vba
Sub efface_recap()
    Application.Goto Reference:="eff_recap"
    Selection.ClearContents
    Range("A1").Select
End Sub
```

**Ce qu'elle fait:**
- Utilise une plage nommée "eff_recap"
- Efface le contenu de cette plage
- Retourne à la cellule A1

**Note:** Utilise une plage nommée "eff_recap" définie dans Excel

---

### 2. **efface()** - Effacer Recap (Version détaillée)

**Ligne:** 5529-5546
**Module:** Module7.bas

```vba
Sub efface()
    Range("B6:C20").Select
    Selection.ClearContents
    Range("D9:D10").Select
    Selection.ClearContents
    Range("D12:D14").Select
    Selection.ClearContents
    Range("D16").Select
    Selection.ClearContents
    Range("D18").Select
    Selection.ClearContents
End Sub
```

**Ce qu'elle fait:**
- **B6:C20:** Colonnes B et C (Lecture et Corr), rows 6-20
- **D9:D10:** Colonne D (Net), rows 9-10
- **D12:D14:** Colonne D (Net), rows 12-14
- **D16:** Colonne D (Net), row 16
- **D18:** Colonne D (Net), row 18

**IMPORTANT:** Cette macro efface aussi certaines cellules de la colonne D (Net), ce qui est étrange car D devrait contenir des formules.

**Hypothèse:** Peut-être que certaines cellules de D ne contiennent pas de formules mais des valeurs saisies?

---

### 3. **eff_trans()** - Effacer Transelect

**Ligne:** 10327-10339
**Module:** (dernière partie du fichier)

```vba
Sub eff_trans()
    Application.Goto Reference:="eff_trans"
    Range("B9:U13,X9:X13,B20:H24,J20:P24").Select
    Range("P20").Activate
    Selection.ClearContents
    Range("B9").Select
End Sub
```

**Ce qu'elle fait:**
- Utilise une plage nommée "eff_trans"
- Efface les plages spécifiques:
  - **B9:U13** - Probablement les données de cartes (DÉBIT, VISA, MASTER, etc.) pour BAR A, B, C
  - **X9:X13** - Colonne X
  - **B20:H24** - Probablement Bank Report section
  - **J20:P24** - Autres sections

---

### 4. **efface_rapport_geac()** - Effacer GEAC/UX

**Ligne:** 7914-7927
**Module:** Module17.bas

```vba
Sub efface_rapport_geac()
    Range("B6:C6,E6,G6:H6,J6,B8:C8,E8,G8:H8,J8,B12:C12,E12,G12:H12,J12,B32:C32,E32,B37:C37,E37,B41:C41,G41:H41,B44:C44,J44:K44,B47:C47,E47,B50:C50,E50,B53:C53,E53").Select
    Selection.ClearContents
    Range("a1").Select
End Sub
```

**Ce qu'elle fait:**
- Efface de nombreuses cellules spécifiques dans GEAC/UX
- Cellules effacées:
  - Row 6: B6:C6, E6, G6:H6, J6
  - Row 8: B8:C8, E8, G8:H8, J8
  - Row 12: B12:C12, E12, G12:H12, J12
  - Row 32: B32:C32, E32
  - Row 37: B37:C37, E37
  - Row 41: B41:C41, G41:H41
  - Row 44: B44:C44, J44:K44
  - Row 47: B47:C47, E47
  - Row 50: B50:C50, E50
  - Row 53: B53:C53, E53

---

### 5. **eff_daily()** - Effacer Daily

**Ligne:** 5446-5458
**Module:** Module5.bas

```vba
Sub eff_daily()
    Application.Goto Reference:="eff_daily"
    Range("B2:B41,B44,B47").Select
    Selection.ClearContents
End Sub
```

**Ce qu'elle fait:**
- Utilise une plage nommée "eff_daily"
- Efface:
  - **B2:B41** - Colonne B, rows 2-41
  - **B44** - Cellule B44
  - **B47** - Cellule B47

**Note:** Peut-être utilisé pour un autre onglet (pas Recap/Transelect/GEAC)?

---

### 6. **Eff_depot()** - Effacer Dépôt

**Ligne:** 5410-5423
**Module:** Module4.bas

```vba
Sub Eff_depot()
    Application.Goto Reference:="eff_depot"
    Selection.ClearContents
    Range("A10").Select
End Sub
```

**Ce qu'elle fait:**
- Utilise une plage nommée "eff_depot"
- Efface le dépôt

---

## 📊 AUTRES MACROS IMPORTANTES

### envoie_dans_jour() - Copier dans l'onglet "jour"

**Ligne:** 6638-6665

```vba
Sub envoie_dans_jour()
    Value = InputBox("La date a-t-elle été changé o/n?")

    If Value = "o" Or Value = "O" Then
        Range("h19:n19").Select
        Selection.Copy

        Dim test
        test = Trim(Str(Worksheets("controle").Range("vjour").Value))
        test = "ar_" + test
        Application.Goto Reference:=test
        Selection.PasteSpecial Paste:=xlValues, Operation:=xlNone, SkipBlanks:=False, Transpose:=False
        Application.CutCopyMode = False
    Else
        Application.Goto Reference:="home_controle"
    End If
End Sub
```

**Ce qu'elle fait:**
1. Demande si la date a été changée
2. Si oui:
   - Copie H19:N19
   - Récupère le jour depuis Controle ("vjour")
   - Construit une référence "ar_" + jour (ex: "ar_23")
   - Colle les valeurs à cet emplacement dans l'onglet "jour"

**Exemple:** Si vjour = 23, colle à la plage nommée "ar_23"

---

## 🎯 RÉSUMÉ: CELLULES À EFFACER

### Recap
**Option 1 (efface_recap):** Utilise plage nommée "eff_recap"
**Option 2 (efface):**
- B6:C20 (Lecture et Corr)
- D9:D10, D12:D14, D16, D18 (certaines cellules de Net)

### Transelect
- B9:U13 (données cartes BAR)
- X9:X13
- B20:H24 (Bank Report)
- J20:P24

### GEAC/UX
- Liste complexe de cellules spécifiques (voir ci-dessus)

---

## 💡 IMPLÉMENTATION PYTHON

### Option 1: Utiliser les Plages Nommées

Si on peut lire les plages nommées depuis Excel:

```python
import xlrd

def get_named_range(workbook, name):
    """Get the cell references for a named range"""
    # xlrd peut lire les plages nommées
    for n in workbook.name_obj_list:
        if n.name == name:
            # Parse et retourne les cellules
            pass
```

### Option 2: Hard-code les Cellules

Plus simple et plus fiable:

```python
def clear_recap_values(sheet):
    """
    Efface les valeurs dans Recap comme le fait la macro VBA efface()
    """
    # Colonnes B et C, rows 6-20 (0-indexed: rows 5-19, cols 1-2)
    for row in range(5, 20):
        sheet.write(row, 1, '')  # Colonne B (Lecture)
        sheet.write(row, 2, '')  # Colonne C (Corr)

    # Certaines cellules de colonne D
    # D9:D10 (rows 8-9, col 3)
    sheet.write(8, 3, '')
    sheet.write(9, 3, '')

    # D12:D14 (rows 11-13, col 3)
    sheet.write(11, 3, '')
    sheet.write(12, 3, '')
    sheet.write(13, 3, '')

    # D16 (row 15, col 3)
    sheet.write(15, 3, '')

    # D18 (row 17, col 3)
    sheet.write(17, 3, '')

def clear_transelect_values(sheet):
    """
    Efface les valeurs dans Transelect comme le fait la macro VBA eff_trans()
    """
    # B9:U13 (rows 8-12, cols 1-20)
    for row in range(8, 13):
        for col in range(1, 21):
            sheet.write(row, col, '')

    # X9:X13 (rows 8-12, col 23)
    for row in range(8, 13):
        sheet.write(row, 23, '')

    # B20:H24 (rows 19-23, cols 1-7)
    for row in range(19, 24):
        for col in range(1, 8):
            sheet.write(row, col, '')

    # J20:P24 (rows 19-23, cols 9-15)
    for row in range(19, 24):
        for col in range(9, 16):
            sheet.write(row, col, '')

def clear_geac_values(sheet):
    """
    Efface les valeurs dans GEAC/UX comme le fait la macro VBA efface_rapport_geac()
    """
    cells_to_clear = [
        # Row 6 (index 5)
        (5, 1), (5, 2), (5, 4), (5, 6), (5, 7), (5, 9),
        # Row 8 (index 7)
        (7, 1), (7, 2), (7, 4), (7, 6), (7, 7), (7, 9),
        # Row 12 (index 11)
        (11, 1), (11, 2), (11, 4), (11, 6), (11, 7), (11, 9),
        # Row 32 (index 31)
        (31, 1), (31, 2), (31, 4),
        # Row 37 (index 36)
        (36, 1), (36, 2), (36, 4),
        # Row 41 (index 40)
        (40, 1), (40, 2), (40, 6), (40, 7),
        # Row 44 (index 43)
        (43, 1), (43, 2), (43, 9), (43, 10),
        # Row 47 (index 46)
        (46, 1), (46, 2), (46, 4),
        # Row 50 (index 49)
        (49, 1), (49, 2), (49, 4),
        # Row 53 (index 52)
        (52, 1), (52, 2), (52, 4),
    ]

    for row, col in cells_to_clear:
        sheet.write(row, col, '')
```

---

## ⚠️ PROBLÈME AVEC LA MACRO `efface()`

La macro `efface()` efface certaines cellules de la colonne D (Net) dans Recap:
- D9:D10
- D12:D14
- D16
- D18

**Questions:**
1. Est-ce que ces cellules contiennent des formules ou des valeurs saisies?
2. Pourquoi effacer la colonne Net si elle est calculée?

**Hypothèse:** Peut-être que ces cellules spécifiques ne contiennent pas de formules mais des valeurs manuelles?

---

## 🚀 RECOMMANDATION POUR LA WEB APP

### Approche Hybride: Template + Nettoyage Ciblé

1. **Créer un template RJ propre:**
   - Ouvrir un RJ existant dans Excel
   - Exécuter toutes les macros d'effacement:
     - `efface_recap()`
     - `eff_trans()`
     - `efface_rapport_geac()`
   - Sauvegarder comme `RJ_TEMPLATE.xls`

2. **Workflow dans la web app:**
   - Charger le template
   - Mettre à jour Controle (nom, date)
   - L'utilisateur remplit les valeurs
   - Pas besoin de coder les macros d'effacement!

**Avantages:**
- Pas besoin de coder toutes les macros VBA en Python
- Le template est déjà "propre"
- Plus simple et plus fiable

---

## 📝 NOTES

### Plages Nommées Utilisées

Les macros utilisent plusieurs plages nommées:
- `eff_recap` - Cellules à effacer dans Recap
- `eff_trans` - Cellules à effacer dans Transelect
- `eff_depot` - Cellules à effacer dans Dépôt
- `eff_daily` - Cellules à effacer dans Daily
- `vjour` - Jour du mois (dans Controle)
- `home_recap`, `home_trans`, `home_controle`, etc. - Cellules "home"
- `ar_1` à `ar_31` - Destinations dans l'onglet "jour" pour chaque jour du mois

### Macros de Navigation

- `aller_recap()` - Va à Recap
- `aller_trans()` - Va à Transelect
- `aller_jour()` - Va à l'onglet "jour"
- `aller_depot()` - Va à Dépôt

### Macros d'Impression

- `Imp_RJ()` - Imprimer RJ
- `imp_trans()` - Imprimer Transelect
- `imp_depot()` - Imprimer Dépôt
- `imp_rapport()` - Imprimer les rapports

---

**Document créé:** 2026-01-02
**Macros VBA extraites:** ✅
**Analyse complète:** ✅
**Prêt pour implémentation:** ✅
