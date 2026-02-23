# Instructions pour réensemencer la base de données avec les screenshots

Les screenshots ont été ajoutés à `seed_tasks_front.py`, mais la base de données doit être réensemencée pour les inclure.

## Étapes:

1. **Arrêter le serveur Flask** (si en cours d'exécution)

2. **Réensemencer la base de données:**
   ```bash
   python seed_tasks.py
   ```

3. **Redémarrer le serveur Flask**

4. **Vérifier dans le navigateur:**
   - Ouvrir la console (F12)
   - Ouvrir une tâche dans le guide
   - Vérifier les messages de debug pour voir si les screenshots sont chargés

## Vérification:

Après le réensemencement, les screenshots devraient apparaître dans la section "Captures d'écran" du guide pour chaque tâche qui en a.

