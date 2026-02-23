# Peer Review — Gestion RJ (Night Audit App)

**Date**: 9 février 2026
**Portée**: Frontend (rj_tabs.js, rj_layout.html, CSS), Backend (Flask routes), Utilitaires (rj_filler, rj_reader, jour_mapper, adjustment_handler), Templates d'onglets

---

## Résumé Exécutif

**86 problèmes identifiés** au total:
- **7 CRITIQUES** — bugs qui cassent des fonctionnalités ou causent des pertes de données
- **14 HAUTS** — dysfonctionnements visibles ou risques de sécurité
- **28 MOYENS** — code fragile, duplication, ou comportement inattendu
- **37 BAS** — améliorations de style, performance, ou maintenabilité

---

## CRITIQUES (7)

### C1. `fill_sheet()` — `get_sheet()` avec un nom string au lieu d'un index
**Fichier**: `utils/rj_filler.py`, ligne 386
**Impact**: **TOUTES les sauvegardes Recap/Transelect/GEAC échouent**

```python
# BUG: xlwt.Workbook.get_sheet() n'accepte QUE des entiers
sheet = self.wb.get_sheet(sheet_name)  # TypeError: 'Recap' n'est pas un int
```

Le même bug existe dans `fill_dueback_day()` (ligne 430), `fill_dueback_by_col()` (ligne 459), et `fill_setd_day()` (ligne 476) — ils passent tous des noms de string comme `'DUBACK#'` et `'SetD'`.

Toutes les autres méthodes (reset_tabs, update_controle, envoie_dans_jour, calcul_carte, fill_jour_day) font correctement une boucle pour trouver l'index d'abord.

**Correction**: Ajouter une méthode helper `_get_sheet_by_name(name)` et l'utiliser partout.

---

### C2. `rj_status()` — clé de réponse incompatible avec le frontend
**Fichier**: `routes/audit/rj_core.py`, ligne 165 vs `static/js/audit/rj_tabs.js`, ligne 191
**Impact**: Le frontend ne détecte jamais qu'un fichier est chargé

Le backend retourne `{'uploaded': True, ...}` mais le frontend vérifie `data.file_loaded`:
```javascript
if (data.file_loaded) { ... }  // Ne match pas 'uploaded'
```

De plus, le champ `filename` n'est pas retourné par `/api/rj/status` (seulement `file_size` et `current_day`), mais `updateFileStatus(data.filename, data.file_size)` le requiert.

---

### C3. `send_recap_to_jour()` — `data.get('day', type=int)` invalide
**Fichier**: `routes/audit/rj_macros.py`, ligne 275
**Impact**: `type` est ignoré par `dict.get()`, le jour n'est jamais un int

```python
day = data.get('day', type=int)  # dict.get() ne supporte pas 'type'
# Devrait être: day = int(data.get('day', 0))
```

`type=` est un paramètre de `request.args.get()` (Flask), pas de `dict.get()`.

---

### C4. `save_dueback_simple()` — format JSON attendu ≠ format envoyé
**Fichier**: `routes/audit/rj_fill.py` lignes 285-364 vs `rj_tabs.js` lignes 815-871
**Impact**: Le save DueBack ne fonctionne pas

Le backend attend: `{ 'C': { previous: 0, current: 50 }, 'D': { ... } }`
Le frontend envoie: `{ entries: [{ col_letter: 'C', previous: 0, current: 50 }] }`

Le backend itère avec `for col_letter, values in data.items()` mais reçoit `entries` comme clé, pas des lettres de colonnes.

---

### C5. `RJ_FILES` — aucune protection thread/race condition
**Fichier**: `routes/audit/rj_core.py`, ligne 18
**Impact**: Corruption de données si 2 requêtes modifient le RJ simultanément

```python
RJ_FILES = {}  # dict global, pas de lock
```

Scénario: User clique "Save Recap" et "Save Transelect" rapidement — les deux lisent le même BytesIO, chacun crée son propre RJFiller, et le dernier à écrire écrase les changements du premier.

---

### C6. XSS dans `notify()`
**Fichier**: `static/js/audit/rj_tabs.js`, ligne 27
**Impact**: Injection HTML possible via messages d'erreur du serveur

```javascript
notification.innerHTML = `<span>${message}</span>...`;
// Si message contient du HTML, il sera exécuté
```

Un message d'erreur backend contenant `<script>` ou `<img onerror=...>` s'exécuterait.

---

### C7. BytesIO position non réinitialisée après écriture
**Fichier**: Multiples routes (rj_fill.py, rj_macros.py)
**Impact**: Les lectures suivantes peuvent échouer ou lire des données corrompues

Après `RJ_FILES[session_id] = output_buffer`, le buffer est positionné à la fin. La prochaine route qui fait `file_bytes = RJ_FILES[session_id]` puis `file_bytes.seek(0)` fonctionne... MAIS si une route oublie le `seek(0)`, elle lit un buffer vide. Les routes le font correctement pour l'instant, mais c'est fragile.

---

## HAUTS (14)

### H1. Preview colonnes > O (15) — header incorrect
**Fichier**: `rj_tabs.js`, ligne 598
`String.fromCharCode(65 + c)` ne fonctionne que pour A-Z (colonnes 0-25). Pour le jour sheet qui a 117 colonnes, les headers seront des caractères invalides.

### H2. `macroExecuteAll()` — le `return` dans le finally block est dans le if
**Fichier**: `rj_tabs.js`, lignes 390-397
Si `d1.success` est false, on fait `return` sans restaurer le bouton (le `finally` ne s'exécute pas car le return est dans le `try`).

### H3. `bare except` dans multiples routes
**Fichiers**: `rj_core.py` ligne 162, `rj_macros.py` ligne 131
`except:` sans type attrape tout, y compris SystemExit et KeyboardInterrupt.

### H4. `session.get('user_session_id', 'default')` — tous les users non-auth partagent le même RJ
**Fichier**: Toutes les routes
Si la session expire ou n'a pas de `user_session_id`, TOUS les users tombent sur `'default'`, partageant le même fichier.

### H5. `_Workbook__worksheets` — accès à un attribut privé Python
**Fichier**: `utils/rj_filler.py`, multiples lignes
Si xlwt change son implémentation interne, tout casse. Devrait utiliser `self.wb._Workbook__worksheets` via une méthode wrapper.

### H6. `fillDueBackReception()` cherche `data.column_b_current` mais l'API retourne `data.data.previous/current/net`
**Fichier**: `rj_tabs.js` ligne 440 vs `rj_fill.py` ligne 241-245
Le frontend vérifie `data.column_b_current` mais le backend retourne `{ success: true, data: { previous, current, net } }`.

### H7. Pas de validation d'entrée sur les montants financiers
**Fichier**: Backend routes
Les montants sont convertis en `float()` sans vérification de bornes. Des valeurs comme `NaN`, `Infinity`, ou des montants aberrants (999999999) passent.

### H8. `update_deposit()` — la recherche de date ne fait rien
**Fichier**: `utils/rj_filler.py`, lignes 336-341
La boucle de recherche de date contient `pass` — elle ne trouve jamais la date et tombe toujours sur "premier rang vide".

### H9. Pattern répété 9x pour la gestion des boutons spinner
**Fichier**: `rj_tabs.js`
Chaque fonction async (save, macro, etc.) répète le même pattern de 8 lignes pour disable/spinner/restore du bouton. Devrait être un wrapper.

### H10. `loadSheetPreview()` — `loadingEl.style.display = 'block'` dans le catch sans vérifier null
**Fichier**: `rj_tabs.js`, ligne 640
Si `loadingEl` est null, cette ligne crash.

### H11. `resetRJ()` vs `resetAllSheets()` — les deux appellent `/api/rj/reset`
**Fichier**: `rj_tabs.js`, lignes 135 et 302
`resetRJ()` et `resetAllSheets()` font exactement la même chose, mais `resetRJ()` fait aussi un `location.reload()`.

### H12. Pas de CSRF protection
**Fichier**: Toutes les routes POST
Les endpoints POST n'ont pas de token CSRF. Un site malveillant pourrait soumettre des formulaires vers l'app.

### H13. `col_idx_to_letter` manquant pour colonnes > Z
**Fichier**: `utils/rj_filler.py`
`excel_col_to_index()` gère les colonnes multi-lettres (AA, AB...) mais il n'y a pas de fonction inverse pour l'affichage.

### H14. `envoie_dans_jour` et `calcul_carte` lisent depuis `self.rb` (ancien) pas le workbook modifié
**Fichier**: `utils/rj_filler.py`, lignes 509-524
Si l'utilisateur a modifié Recap via `fill_sheet()` dans la même session, `envoie_dans_jour()` copiera les anciennes valeurs car il lit depuis `self.rb` (le workbook original), pas les valeurs fraîchement écrites.

---

## MOYENS (28)

| # | Fichier | Description |
|---|---------|-------------|
| M1 | rj_tabs.js | `event?.target?.closest?.('button')` — `event` est implicite, ne fonctionne pas dans tous les navigateurs |
| M2 | rj_tabs.js | `fillSurplusDeficit()` utilise `Math.abs()` partout — perd le signe des valeurs négatives intentionnelles |
| M3 | rj_tabs.js | `saveSD()` collecte tous les `[data-field]` y compris ceux d'autres onglets si le DOM n'est pas nettoyé |
| M4 | rj_layout.html | `switchRJTab()` exécute les scripts avec `document.body.appendChild(newScript)` — les scripts ne sont jamais supprimés |
| M5 | rj_layout.html | Les scripts ajoutés au body persistent et peuvent dupliquer des fonctions après changement d'onglet |
| M6 | rj_core.py | `download_rj()` ne réinitialise pas la position après `send_file()` — le prochain `seek(0)` est nécessaire |
| M7 | rj_core.py | `preview_rj()` ne valide pas `sheet_name` — un utilisateur peut demander n'importe quel nom de feuille |
| M8 | rj_fill.py | `save_dueback_simple()` crée un RJFiller puis un RJReader sur le même BytesIO — double lecture inutile |
| M9 | rj_fill.py | `fill_rj_sheet()` n'accepte que 4 sheets (recap, transelect, geac, controle) — pas de 'depot' ou 'daily' |
| M10 | rj_macros.py | `sync_duback_setd()` bare `except:` avec `pass` masque toutes les erreurs |
| M11 | rj_filler.py | `sync_duback_to_setd()` — `op_row_idx = op_row_idx - 1` — possible off-by-one |
| M12 | rj_filler.py | Fuzzy match dans `sync_duback_to_setd()` (ligne 300-303) — peut matcher le mauvais nom |
| M13 | jour_mapper.py | `_apply_hp_deductions()` — ne valide pas le signe de `hp_amount` avant de soustraire |
| M14 | jour_mapper.py | `_formula_column_cf()` — logique "always negative" force les crédits à être négatifs même s'ils sont légitimement positifs |
| M15 | rj_mapper.py | `DUEBACK_RECEPTIONIST_COLUMNS` est hardcodé — les réceptionnistes changent souvent |
| M16 | rj_mapper.py | `get_dueback_row_for_day()` docstring dit "0-indexed" mais retourne des valeurs 1-indexed (Day 1 → 4, 5) |
| M17 | style.css | `.rj-tab-btn:hover` n'a pas de transition — le changement de couleur est brusque |
| M18 | Templates | Les templates d'onglets n'ont pas de gestion d'erreur si le RJ n'est pas chargé |
| M19 | rj_tabs.js | `tabCache` n'est jamais invalidé quand le RJ est modifié (sauf upload et reset) |
| M20 | rj_tabs.js | `setupExcelNavigation()` — ArrowUp/ArrowDown non gérés pour navigation verticale |
| M21 | rj_fill.py | Chaque route crée un nouveau `RJFiller` — ouvre le workbook à chaque requête |
| M22 | rj_core.py | `RJ_FILES` et `SD_FILES` n'ont pas de limite — un attaquant pourrait remplir la mémoire |
| M23 | rj_tabs.js | `downloadRJ()` filename utilise la date locale du client, pas la date d'audit du RJ |
| M24 | adjustment_handler.py | `apply_adjustments()` crée des valeurs négatives si la colonne n'existait pas — peut fausser les calculs |
| M25 | rj_fill.py | `update_deposit()` — la logique de recherche de date dans la feuille depot est incomplète (pass dans la boucle) |
| M26 | rj_layout.html | `formatCurrency()` défini 2 fois (layout.html et rj_tabs.js) |
| M27 | rj_layout.html | `notify()` défini 2 fois (layout.html et rj_tabs.js) — la version rj_tabs.js écrase celle du layout |
| M28 | rj_tabs.js | Pas de debounce sur les boutons de sauvegarde — double-clic possible |

---

## Suggestions d'Améliorations Prioritaires

### Priorité 1 — Corrections Critiques (à faire maintenant)

1. **Fixer `_get_sheet_by_name()`** — créer un helper dans RJFiller et remplacer tous les `get_sheet(string)`
2. **Aligner les clés API** — `uploaded` → `file_loaded`, ajouter `filename` dans status
3. **Fixer le format JSON DueBack** — aligner frontend et backend
4. **Fixer `send_recap_to_jour()`** — remplacer `data.get('day', type=int)` par `int(data.get('day'))`
5. **Fixer `fillDueBackReception()`** — utiliser `data.data.current` au lieu de `data.column_b_current`
6. **Sanitizer `notify()`** — utiliser `textContent` au lieu de `innerHTML`

### Priorité 2 — Stabilité (cette semaine)

7. **Ajouter un threading.Lock** autour de RJ_FILES pour éviter les race conditions
8. **Wrapper pour button spinner** — extraire le pattern répété en une fonction `withSpinner(btn, asyncFn)`
9. **Invalider `tabCache`** après chaque save/macro (pas seulement upload/reset)
10. **Ajouter `response.ok` checks** sur tous les fetch() calls

### Priorité 3 — Robustesse (ce mois)

11. **envoie_dans_jour lit les anciennes valeurs** — relire le buffer après chaque écriture, ou garder le filler en mémoire
12. **Limiter RJ_FILES** — max 10 sessions, expiration après 8h
13. **Validation des montants** — bornes raisonnables (0-10M$)
14. **CSRF tokens** — ajouter Flask-WTF ou un token custom
