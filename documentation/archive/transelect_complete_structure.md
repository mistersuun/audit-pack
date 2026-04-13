# TRANSELECT - Structure Complète et Détaillée

**Date:** 2025-12-25
**Source:** `Rj 12-23-2025-Copie.xls` - Sheet `transelect`
**Dimensions:** 40 rows × 32 cols (A-AF)

---

## VUE D'ENSEMBLE

Le sheet Transelect contient **2 SECTIONS PRINCIPALES** + **3 TABLEAUX DE SOMMAIRE**:

1. **Section Restaurant/Bar/Banquet** (Rows 6-13)
2. **Section Réception/Chambres** (Rows 17-24)
3. **Tableaux de Sommaire** (Rows 26-39) - Réconciliation finale

---

## SECTION 1: RESTAURANT/BAR/BANQUET (Rows 6-13)

### Structure des Colonnes

#### Terminaux (Cols B-U): 20 terminaux au total

**BAR (3 terminaux):**
- Col B: Terminal A
- Col C: Terminal B
- Col D: Terminal C

**SPESA (1 terminal):**
- Col E: Terminal D

**ROOM (1 terminal):**
- Col F: Terminal E

**EXTRA (3 terminaux):**
- Col G: A0774167
- Col H: B0774167
- Col I: DK531139

**BANQUET (12 terminaux):**
- Col J: BO531139
- Col K: BP531139
- Col L: CK531139
- Col M: BS531139
- Col N: BR531139
- Col O: BU531139
- Col P: DN531139
- Col Q: DI531139
- Col R: DL531139
- Col S: DM531139
- Col T: DJ531139
- Col U: DK531139

#### Colonnes de Calcul et Réconciliation

- **Col V: TOTAL 1** - Somme de tous les terminaux (B-U)
- **Col W: TOTAL 2** - Total additionnel (à clarifier)
- **Col X: POSITOUCH** - Total du système POS (à matcher)
- **Col Y: VARIANCE** ⚠️ **COLONNE DE BALANCE** - Différence entre totaux
- **Col Z: ESCOMPTE** - % d'escompte
- **Col AA: $** (escompte) - Montant en $ de l'escompte
- **Col AB: NET** - Net après escompte (pour GEAC)

### Lignes (Types de Cartes)

- **Row 8: DÉBIT**
- **Row 9: VISA**
- **Row 10: MASTER**
- **Row 11: DISCOVER**
- **Row 12: AMEX**
- **Row 13: TOTAL** - Totaux par colonne

### Exemple de Données (Row 9 - VISA):

```
Row 9: VISA
  B (Bar A):        673.64
  C (Bar B):        882.71
  D (Bar C):        198.07
  J (Banquet BO):   222.26
  K (Banquet BP):   391.49
  L (Banquet CK):    85.97
  ──────────────────────────
  V (TOTAL 1):     1754.42
  W (TOTAL 2):      699.72
  X (POSITOUCH):  13228.69
  Y (VARIANCE):  -10774.55  ← Différence! Ne balance pas!
  Z (ESCOMPTE%):      0.02
  AA ($ escompte):   42.95
  AB (NET):        2411.19
```

**Interprétation:**
- Total des terminaux = 1754.42 + 699.72 = 2454.14
- POS system dit = 13228.69
- **VARIANCE = -10774.55** ⚠️ Il manque des terminaux ou données!

---

## SECTION 2: RÉCEPTION/CHAMBRES (Rows 17-24)

### Structure des Colonnes

#### Terminaux Source (Cols B-D)

- **Col B: Bank Report** - FreedomPay (rapport bancaire)
- **Col C: Réception 8** - Terminal 8
- **Col D: Réception K053** - Terminal K053

#### Colonnes de Calcul

- **Col I: TOTAL Bank Report** - Total des terminaux
- **Col P: Daily Revenue** - Revenu journalier (à matcher)
- **Col Q: VARIANCE** - Différence (doit être 0)
- **Col R: ESCOMPTE** - % d'escompte par type de carte
- **Col S: $** (escompte) - Montant en $ de l'escompte
- **Col T: NET GEAC** - Net qui va dans GEAC

### Lignes (Types de Cartes)

- **Row 19: DÉBIT**
- **Row 20: VISA**
- **Row 21: MASTER**
- **Row 22: DISCOVER**
- **Row 23: AMEX**
- **Row 24: TOTAL**

### Exemple de Données (Row 20 - VISA):

```
Row 20: VISA
  B (FreedomPay):   7625.85
  C (Terminal 8):        0
  D (Terminal K053):     0
  ───────────────────────────
  I (TOTAL):        7625.85
  P (Daily Rev):    7625.85
  Q (VARIANCE):          0   ✅ Balance!
  R (ESCOMPTE%):      0.02
  S ($ escompte):   133.45
  T (NET GEAC):    7492.40
```

**Formules:**
- **TOTAL (I)** = B + C + D
- **VARIANCE (Q)** = TOTAL (I) - Daily Revenue (P)
- **$ escompte (S)** = TOTAL × ESCOMPTE% (R)
- **NET GEAC (T)** = TOTAL (I) - $ escompte (S)

---

## SECTION 3: TABLEAUX DE SOMMAIRE (Rows 26-39)

### Tableau 1: TOTAUX (Rows 26-28)

Répartition par processeur de cartes:

```
           E          F        G         I        P        Q
      AMEX ELAVON | DISCOVER | MASTER | VISA | DEBIT | AMEX GLOBAL
Row 28: 5714.14   |    0     |12120.56|10079.99|1707.45|  220.42
```

### Tableau 2: TOTAUX TRANSELECT (Rows 29-31)

Totaux de la section Restaurant uniquement:

```
           E          F        G         I        P        Q
      AMEX ELAVON | DISCOVER | MASTER | VISA | DEBIT | AMEX GLOBAL
Row 31:    0      |    0     | 1525.51|2454.14|1707.45|  220.42
```

### Tableau 3: TOTAUX GEAC (Rows 32-34)

Totaux de la section Réception (qui vont dans GEAC):

```
           E          F        G         I        P        Q
      AMEX ELAVON | DISCOVER | MASTER | VISA | DEBIT | AMEX GLOBAL
Row 34: 5562.72   |    0     |10595.05|7625.85|   0   |     0
```

### Tableau 4: Réconciliation Finale (Rows 36-39)

**Row 37: Totaux bruts par processeur**
```
amex elavon | discover | master  |  visa   | débit  | amex global
  5714.14   |    0     | 12120.56| 10079.99| 1707.45|   220.42
```

**Row 39: Breakdown détaillé**
```
ax      | (B)     | dc | (E) | mc      | (G)      | visa    | (P)    | débit  | (R)
0       | 5562.72 | 0  |  0  | 1525.51 | 10595.05 | 2454.14 |7625.85 |1707.45 | 0
```

---

## FORMULES ET CALCULS AUTOMATIQUES

### Section 1: Restaurant

**TOTAL 1 (Col V):**
```
V = SUM(B:U)  // Somme de tous les terminaux
```

**VARIANCE (Col Y):**
```
Y = (V + W) - X  // Différence avec POS
```

**$ escompte (Col AA):**
```
AA = AB × Z  // Net × Taux d'escompte
```

**NET (Col AB):**
```
AB = (V + W) - AA  // Total moins escompte
```

### Section 2: Réception

**TOTAL Bank Report (Col I):**
```
I = B + C + D  // Somme des terminaux
```

**VARIANCE (Col Q):**
```
Q = I - P  // Doit être 0!
```

**$ escompte (Col S):**
```
S = I × R  // Total × Taux d'escompte
```

**NET GEAC (Col T):**
```
T = I - S  // Total moins escompte
```

### Validation Globale

**La réconciliation est correcte si:**
1. Section Restaurant: VARIANCE (Y) proche de 0 pour chaque type de carte
2. Section Réception: VARIANCE (Q) = 0 pour chaque type de carte
3. Somme Row 37 = Somme Row 39

---

## COMPARAISON AVEC L'UI ACTUELLE

### ✅ CE QUI EST PRÉSENT DANS L'UI:

- Section Restaurant: Terminaux BAR (701, 702, 703)
- Section Restaurant: Terminal SPESA (704)
- Section Restaurant: Terminal ROOM (705)
- Section Restaurant: Quelques terminaux EXTRA et Banquet (G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U)
- Les 5 types de cartes (DÉBIT, VISA, MASTER, DISCOVER, AMEX)
- Section Réception: FreedomPay, Terminal 8, K053

### ❌ CE QUI MANQUE DANS L'UI:

**Colonnes Critiques:**
1. **Col Y: VARIANCE** ⚠️ **COLONNE DE BALANCE - MANQUANTE!**
2. **Col Z: ESCOMPTE (%)** - Taux d'escompte par carte
3. **Col AA: $ escompte** - Montant en dollars
4. **Col AB: NET** - Montant net pour GEAC

**Colonnes de Totaux:**
5. **Col V: TOTAL 1** - Visible mais pas calculé automatiquement
6. **Col W: TOTAL 2** - Manquant
7. **Col X: POSITOUCH** - Visible mais pas calculé automatiquement

**Section Réception:**
8. **Col I: TOTAL** - Manquant ou pas calculé
9. **Col P: Daily Revenue** - Manquant
10. **Col Q: VARIANCE** - **MANQUANT!**
11. **Col R-T: ESCOMPTE, $, NET** - Tous manquants

**Tableaux de Sommaire:**
12. **Rows 26-28: TOTAUX** - Complètement manquant
13. **Rows 29-31: TOTAUX TRANSELECT** - Complètement manquant
14. **Rows 32-34: TOTAUX GEAC** - Complètement manquant
15. **Rows 36-39: Réconciliation finale** - Complètement manquant

---

## MODIFICATIONS NÉCESSAIRES À L'UI

### 1. Section Restaurant - Ajouter Colonnes

```html
<th>TOTAL 1 (V)</th>
<th>TOTAL 2 (W)</th>
<th>POSITOUCH (X)</th>
<th>VARIANCE (Y)</th>  ← CRITIQUE!
<th>ESCOMPTE% (Z)</th>
<th>$ (AA)</th>
<th>NET (AB)</th>
```

### 2. Section Réception - Ajouter Colonnes

```html
<th>TOTAL (I)</th>
<th>Daily Rev (P)</th>
<th>VARIANCE (Q)</th>  ← CRITIQUE!
<th>ESCOMPTE% (R)</th>
<th>$ (S)</th>
<th>NET GEAC (T)</th>
```

### 3. Ajouter Section Sommaire

Créer 4 nouveaux tableaux après les deux sections principales:
- TOTAUX (par processeur)
- TOTAUX TRANSELECT (Restaurant)
- TOTAUX GEAC (Réception)
- Réconciliation finale

### 4. Calculs Automatiques JavaScript

**Pour chaque type de carte:**
- Calculer TOTAL 1 (somme des terminaux)
- Calculer VARIANCE (différence avec POS/Daily Revenue)
- Calculer $ escompte (total × %)
- Calculer NET (total - escompte)
- **Afficher avertissement si VARIANCE ≠ 0**

### 5. Validation Visuelle

```javascript
if (Math.abs(variance) > 0.01) {
  // Afficher en rouge
  cell.style.backgroundColor = '#fee';
  cell.style.color = '#c00';
} else {
  // Afficher en vert
  cell.style.backgroundColor = '#efe';
  cell.style.color = '#060';
}
```

---

## ORDRE DE PRIORITÉ POUR L'IMPLÉMENTATION

### 🔴 PRIORITÉ 1 (CRITIQUE):
1. **Ajouter colonne VARIANCE (Y)** dans section Restaurant
2. **Ajouter colonne VARIANCE (Q)** dans section Réception
3. **Auto-calcul des VARIANCE** avec validation visuelle

### 🟡 PRIORITÉ 2 (IMPORTANT):
4. Ajouter colonnes ESCOMPTE (Z, R)
5. Ajouter colonnes $ escompte (AA, S)
6. Ajouter colonnes NET (AB, T)
7. Auto-calcul de tous les totaux

### 🟢 PRIORITÉ 3 (UTILE):
8. Ajouter tableaux de sommaire
9. Vérifier que les 20 terminaux sont tous présents et éditables
10. Ajouter validation finale (sommaire doit balancer)

---

## NOTES IMPORTANTES

1. **VARIANCE est LA colonne critique** - C'est celle qui permet de savoir si la réconciliation balance
2. Les taux d'ESCOMPTE varient par type de carte (VISA: 0.02%, AMEX: 0.03%, etc.)
3. Les terminaux peuvent changer - l'UI doit permettre d'éditer les numéros de terminaux
4. Certains jours, certains terminaux peuvent être à 0 (fermés ou pas utilisés)
5. La réconciliation DOIT balancer (VARIANCE = 0) sinon il y a une erreur

---

## EXEMPLE COMPLET D'UNE LIGNE

**Row 9 - VISA dans Section Restaurant:**

| Type | B | C | D | E | F | G | H | I | J | K | L | ... | V | W | X | Y | Z | AA | AB |
|------|---|---|---|---|---|---|---|---|---|---|---|-----|---|---|---|---|---|----|----|
| VISA | 673.64 | 882.71 | 198.07 | 0 | 0 | 0 | 0 | 0 | 222.26 | 391.49 | 85.97 | ... | 1754.42 | 699.72 | 13228.69 | -10774.55 | 0.02 | 42.95 | 2411.19 |

**Calculs:**
- V = 673.64 + 882.71 + 198.07 + ... = 1754.42
- Y = (1754.42 + 699.72) - 13228.69 = -10774.55 ⚠️
- AA = 2454.14 × 0.02% = 42.95
- AB = 2454.14 - 42.95 = 2411.19

**Problème détecté:** VARIANCE de -10774.55 indique qu'il manque ~10,774$ dans les terminaux par rapport au POS!
