"""
Seed script to load Front and Back office tasks into the database.
Run this once after setting up the database: python seed_tasks.py

Back office tasks are based on the official training document:
  "Formation Auditeur de Nuit - BACK" (mise à jour 19 décembre 2024)
  Located at: documentation/back/procedure_extracted.txt

Front office tasks are imported from seed_tasks_front.py.
"""

import json
from main import create_app
from database import db, Task

# ================= BACK OFFICE TASKS =================
# Workflow matches the real night audit procedure at Sheraton Laval (Property 858).
# Categories: pre_audit → part1 → part2 → end_shift
# Total estimated time: ~5h30 (23:00 → 04:30 typical)

TASKS_BACK = [
    # ─────────────────────────────────────────────────
    # PRE_AUDIT — Setup & Paper Sorting (~23:00-00:30)
    # ─────────────────────────────────────────────────
    {
        "order": 1,
        "title_fr": "Mise en place de l'espace de travail",
        "category": "pre_audit",
        "role": "back",
        "description_fr": "Préparer le poste, vérifier les courriels et organiser son espace de travail.",
        "steps": [
            "Échange d'information avec le superviseur du soir.",
            "Vérification des courriels (instructions spéciales, groupes, etc.).",
            "Vérification du panneau d'incendie (statut normal).",
            "Nettoyer le bureau, l'équipement de travail et organiser son espace."
        ],
        "tips_fr": "Toujours vérifier les courriels en premier — il peut y avoir des instructions importantes pour la nuit.",
        "system_used": "PC / Outlook",
        "estimated_minutes": 5
    },
    {
        "order": 2,
        "title_fr": "Ouvrir et préparer le RJ du jour",
        "category": "pre_audit",
        "role": "back",
        "description_fr": "Ouvrir le RJ d'hier, sauvegarder sous la date du jour, mettre à jour Contrôle et effacer les onglets.",
        "steps": [
            "Ouvrir le fichier Excel RJ de la date d'hier.",
            "Faire 'Enregistrer sous' en changeant la date au jour actuel.",
            "Dans l'onglet 'Contrôle' du RJ : mettre à jour la date et le nom de l'auditeur.",
            "Effacer les onglets RECAP, TRANSELECT et GEAC/UX.",
            "Charger le RJ dans l'application web (page Gestion RJ → 'Charger RJ').",
            "Attendre la confirmation 'Fichier RJ uploadé avec succès'."
        ],
        "tips_fr": "Ne JAMAIS écraser le fichier d'hier. Toujours 'Enregistrer sous' un nouveau nom. Le bouton Reset efface uniquement les onglets d'entrée, pas l'onglet Jour.",
        "system_used": "Excel / App Web",
        "estimated_minutes": 5
    },
    {
        "order": 3,
        "title_fr": "Triage des papiers F&B et réception",
        "category": "pre_audit",
        "role": "back",
        "description_fr": "Ramasser et trier tous les papiers de la journée par catégorie et mode de paiement.",
        "steps": [
            "Ramasser les papiers de la journée dans le panier sur les caisses.",
            "Séparer les papiers réception (enveloppe grise/brune) des papiers F&B (enveloppes bleues).",
            "Trier les papiers F&B par mode de paiement SUR LA TABLETTE :",
            "  - Débit, Visa, MasterCard, American Express",
            "  - Forfait, Admin & Hotel Prom",
            "  - Rapport journalier des serveurs, Bordereaux de dépôt",
            "DANS LE 2e TIROIR BLANC : séparer par étage.",
            "Compte maître : faire une pile banquet et remettre à la personne du front.",
            "Séparer les caisses des réceptionnistes, relevés de dépôt, feuilles d'ajustement, rapports POSitouch et factures POSitouch."
        ],
        "tips_fr": "Bien séparer F&B (bleu) et réception (gris/brun). Les comptes maîtres de banquet vont à la personne du front.",
        "system_used": "Manuel",
        "estimated_minutes": 15
    },
    {
        "order": 4,
        "title_fr": "Cashier Details, Details Tickets (noter ADJ) et compléter le DueBack",
        "category": "pre_audit",
        "role": "back",
        "description_fr": "Vérifier les Details Tickets (noter les ajustements ADJ code 50+), imprimer les Cashier Details et compléter l'onglet DueBack du RJ.",
        "steps": [
            "Vérifier les Details Tickets (1-99, all Sub departments) dans LightSpeed.",
            "IMPORTANT — Noter tous les ajustements (ADJ) : ce sont les transactions avec un code 50 et plus.",
            "  - Exemple : département 28 code 51 → 28.51, ou 10 code 52 → 10.52",
            "  - Ces ajustements devront être ajoutés dans l'onglet Jour du RJ lors du remplissage.",
            "  - Écrire le département.code et le montant sur une feuille séparée pour référence.",
            "Imprimer le Cashier Detail de chaque département avec code de réceptionniste.",
            "Pour settlements : imprimer seulement les paiements Interac (98-13) et chèques (98-14) séparément.",
            "Compléter l'onglet 'DueBack' du fichier Excel RJ avec les rapports de caisse des réceptionnistes :",
            "  - 1re ligne de la date : inscrire le DueBack précédent de chaque employé (en négatif)",
            "  - 2e ligne de la date : inscrire le DueBack d'aujourd'hui (en positif)",
            "  - Utiliser le total de chaque employé tel qu'inscrit sur leur rapport de caisse."
        ],
        "tips_fr": "Le DueBack précédent est toujours en négatif, le nouveau en positif. Les ADJ (code 50+) sont des ajustements à reporter dans le Jour — ne pas les oublier!",
        "system_used": "LightSpeed / Excel",
        "estimated_minutes": 15
    },
    {
        "order": 5,
        "title_fr": "Fermer le Dépôt Restaurant",
        "category": "pre_audit",
        "role": "back",
        "description_fr": "Fermer le compte Dépôt Restaurant une fois que tous les serveurs ont récupéré leurs pourboires. Entrer dans le folio Dépôt Restaurant dans Cashiering.",
        "steps": [
            "Attendre que tous les serveurs aient terminé leur quart et récupéré leurs pourboires.",
            "Aller dans 'Cashiering' dans LightSpeed.",
            "Rechercher et ouvrir le folio 'Dépôt Restaurant' de la journée.",
            "Vérifier que toutes les transactions sont correctes.",
            "Faire un 'Post' pour fermer le compte Dépôt Restaurant.",
            "Imprimer une copie du folio puis refermer le folio.",
            "Assembler : Cashier Detail du code 90.2 sur le dessus, suivi des copies des rapports de caisse POSitouch des serveurs signés (dans l'ordre du Cashier Detail), suivi de la copie du folio 'Depot Restaurant'.",
            "Encercler et signer le total du Cashier Detail.",
            "Encercler et signer la balance à 0$ du folio 'Depot Restaurant'."
        ],
        "tips_fr": "Ne pas fermer avant que TOUS les serveurs aient récupéré leurs pourboires. Il faut entrer dans le folio Dépôt Restaurant du jour dans Cashiering. La balance doit être à 0$.",
        "system_used": "LightSpeed",
        "estimated_minutes": 10
    },
    {
        "order": 6,
        "title_fr": "Compléter le Nettoyeur (si applicable)",
        "category": "pre_audit",
        "role": "back",
        "description_fr": "Compléter les onglets Valet et Somm_valet du RJ s'il y a eu du nettoyage à sec. Le montant total doit aussi être reporté dans l'onglet Jour (Autres revenus → Nettoyeur).",
        "steps": [
            "Vérifier s'il y a un rapport de nettoyage à sec (rapport jaune de Daoust).",
            "Si oui : utiliser le rapport pour compléter l'onglet 'Valet' du RJ Excel.",
            "Compléter ensuite l'onglet 'Somm_valet' du RJ Excel.",
            "Reporter le montant total du nettoyeur dans l'onglet 'Jour' du RJ → section 'Autres revenus' → champ 'Nettoyeur'.",
            "Dans l'application web (RJ Natif → onglet Jour) : remplir le champ 'Nettoyeur' dans la section 'Autres revenus'.",
            "Si non : passer à l'étape suivante (laisser les onglets vides)."
        ],
        "tips_fr": "Le rapport Daoust est normalement sur papier jaune. Si pas de nettoyage, les onglets restent vides. Ne pas oublier de reporter le total dans l'onglet Jour (Autres revenus → Nettoyeur).",
        "system_used": "Excel / App Web",
        "estimated_minutes": 5
    },
    {
        "order": 7,
        "title_fr": "Fermer les terminaux Moneris",
        "category": "pre_audit",
        "role": "back",
        "description_fr": "Fermer les terminaux Moneris et imprimer le rapport Établissement et la liste des utilisateurs Spesa.",
        "steps": [
            "Aller à la réception, au bar, au service aux chambres et au banquet (si utilisé) pour fermer les terminaux Moneris.",
            "Aller à un terminal POSitouch pour imprimer le rapport 'Établissement'.",
            "Le terminal de la Spesa se ferme automatiquement à 3h00.",
            "Aller récupérer l'information Spesa sur VNC :",
            "  - Se connecter sur VNC → CloseBATCH",
            "  - Sélectionner le dernier document publié et imprimer.",
            "ATTENTION : vérifier s'il y a des lots fermés en double à une heure inhabituelle."
        ],
        "tips_fr": "La Spesa ferme automatiquement à 3h. Attention aux lots en double — ça indique un problème de batch.",
        "system_used": "Moneris / POSitouch / VNC",
        "estimated_minutes": 15
    },

    # ─────────────────────────────────────────────────
    # PART1 — Core Data Entry & Balancing (~00:30-03:00)
    # ─────────────────────────────────────────────────
    {
        "order": 8,
        "title_fr": "Compléter le rapport HP Admin",
        "category": "part1",
        "role": "back",
        "description_fr": "Saisir les factures Hotel Promotion et Administration dans le fichier HP du mois. Les données HP peuvent aussi être entrées dans l'onglet HP/Admin du RJ Natif.",
        "steps": [
            "Ouvrir le fichier HP du mois en cours sur le bureau.",
            "Cliquer la flèche de Date, désélectionner la date, sélectionner 'VIDE'.",
            "Inscrire la date de la journée pour chaque facture Admin ou Hotel Prom.",
            "Pour chaque facture, compléter : Area (département), Nourriture, Boisson, Bière, Vin, Minéraux, Pourboire, Paiement (Admin ou Promotion), Raison, Autorisé par.",
            "Aller dans l'onglet 'Journalier' → Données → Actualiser tout → sélectionner la date → Imprimer.",
            "Aller dans l'onglet 'Donnée' → sélectionner la date → Imprimer.",
            "Sauvegarder et refermer le fichier.",
            "Attacher les factures avec les 2 pages Excel. Mettre le tout à droite de l'écran avec les crayons.",
            "APP WEB HP : Vous pouvez aussi déposer le fichier HP directement dans l'app web (Générateurs → HP/Admin). Les entrées web s'écrivent directement dans le fichier Excel. Sélectionnez le jour, ajoutez les factures, et les données se synchronisent automatiquement.",
            "LIEN RAPIDE : Générateurs → HP / Admin (menu latéral) ou RJ Natif → onglet HP/Admin."
        ],
        "tips_fr": "Nourriture inclut : nourriture, jus, eau, café. Minéraux = bulles non-alcoolisées (Perrier, San Pellegrino, etc.). Tabagie reste vide — mettre dans Nourriture. Vous pouvez utiliser soit l'app web HP (Générateurs → HP/Admin) soit l'onglet HP/Admin du RJ Natif.",
        "system_used": "Excel HP / App Web",
        "estimated_minutes": 15
    },
    {
        "order": 9,
        "title_fr": "Imprimer le Sales Journal (VNC)",
        "category": "part1",
        "role": "back",
        "description_fr": "Se connecter à VNC et imprimer le Sales Journal et le Server Cashout Totals.",
        "steps": [
            "Se connecter à VNC Viewer.",
            "Cliquer sur 'Reports and batches'.",
            "Sélectionner 'Sales Journal Reports'.",
            "Saisir la date avant minuit et cliquer sur 'Deposit'.",
            "Sélectionner 'Server Cashout Totals' et 'Print'.",
            "Conserver le rapport pour les prochaines étapes."
        ],
        "tips_fr": "Toujours utiliser la date AVANT minuit pour le Sales Journal. Conserver le rapport Server Cashout Totals — il servira pour le SD.",
        "system_used": "VNC / POSitouch",
        "estimated_minutes": 8
    },
    {
        "order": 10,
        "title_fr": "Compléter le fichier SD (Sommaire des Dépôts)",
        "category": "part1",
        "role": "back",
        "description_fr": "Ouvrir le SD du mois en cours et saisir les montants des dépôts et des relevés POSitouch.",
        "steps": [
            "Ouvrir le dossier SD sur le bureau et sélectionner le fichier de la date.",
            "Aller dans l'onglet de la date en cours.",
            "Écrire la date et son nom au bas.",
            "Compléter les lignes selon le 'SOMMAIRE JOURNALIER DES DÉPÔTS' (pad gris).",
            "Colonne 'Supposé' : noter les montants inscrits sur POSitouch par employé.",
            "Colonne 'Déposé' : noter les montants des feuilles de dépôt (ce qui a été mis dans le coffre).",
            "NE PAS IMPRIMER le SD maintenant — il faut balancer le RECAP avant. On le modifiera peut-être."
        ],
        "tips_fr": "Ne pas imprimer le SD tout de suite — attendre après le balancement du Recap car il pourrait y avoir des modifications.",
        "system_used": "Excel SD",
        "estimated_minutes": 10
    },
    {
        "order": 11,
        "title_fr": "Balancer le Recap (comptant)",
        "category": "part1",
        "role": "back",
        "description_fr": "Imprimer le Daily Revenue pages 5-6, marquer les variances SD et DueBack, et balancer le Recap.",
        "steps": [
            "Imprimer les pages 5 et 6 du Daily Revenue dans LightSpeed.",
            "Marquer le total de variance (tel quel, + ou -) du SD.",
            "Marquer le total de DueBack.",
            "Compléter l'onglet Recap du RJ avec les données du Daily Revenue.",
            "Entrer les montants comptant (LightSpeed, POSitouch).",
            "Entrer les chèques et dépôts.",
            "S'assurer que le Recap balance avant de continuer."
        ],
        "tips_fr": "Le Recap DOIT balancer avant de passer à la suite. Si ça ne balance pas, revérifier le SD et le DueBack.",
        "system_used": "LightSpeed / Excel / App Web",
        "estimated_minutes": 15
    },
    {
        "order": 12,
        "title_fr": "Finir Recap, Dépôt et SetD",
        "category": "part1",
        "role": "back",
        "description_fr": "Imprimer le Recap et le SD, transférer les données vers Dépôt et SetD du RJ.",
        "steps": [
            "Imprimer le RECAP.",
            "Transférer les informations du RECAP dans le RJ en cliquant sur le bouton de transfert.",
            "Imprimer le fichier SD.",
            "Mettre les copies RECAP (dessus) et SD (2e) sur les caisses des réceptionnistes, puis sous la pile Cashier Details.",
            "Copier les montants de la colonne 'Montant Vérifié' du SD dans l'onglet 'Dépôt' du RJ.",
            "Transcrire les variances (et remboursements s'il y en a) dans l'onglet 'SetD' du RJ."
        ],
        "tips_fr": "Ordre d'empilage : RECAP sur le dessus, SD en 2e. Copier 'Montant Vérifié' du SD vers Dépôt (pas les montants supposés).",
        "system_used": "Excel / App Web",
        "estimated_minutes": 10
    },
    {
        "order": 13,
        "title_fr": "Balancer le Transelect (cartes de crédit)",
        "category": "part1",
        "role": "back",
        "description_fr": "Compléter le Transelect avec le rapport Établissement POSitouch et les fermetures Moneris.",
        "steps": [
            "Aller dans l'onglet 'Transelect' du RJ.",
            "Utiliser le rapport POSitouch 'Établissement' pour compléter la colonne 'N' (POSITOUCH) : Interac + Panne Interac.",
            "Utiliser les rapports des terminaux Moneris + Batch POSitouch pour compléter les champs appropriés.",
            "Vérifier que chaque colonne balance (terminal = banque).",
            "Sauvegarder le RJ.",
            "Mettre les relevés Moneris sous l'écran des auditeurs."
        ],
        "tips_fr": "Variance acceptable : 0.01$. Au-delà, vérifier le batch Moneris. Les sections FreedomPay seront complétées après le PART.",
        "system_used": "Excel / App Web",
        "estimated_minutes": 15
    },
    {
        "order": 14,
        "title_fr": "Imprimer et trier les rapports POSitouch",
        "category": "part1",
        "role": "back",
        "description_fr": "Imprimer le Daily Sales Report, les fichiers batch et les Sales Journal Memo Listings depuis VNC.",
        "steps": [
            "Se connecter sur VNC Viewer.",
            "Ouvrir DailySales : faire les sélections appropriées.",
            "Cliquer 'Yes' puis 'OK'.",
            "Imprimer 1 fois les 10 pages et 1 fois la première page seulement.",
            "Quitter et générer le DailySales.",
            "Aller dans le dossier 'BATCH' :",
            "  - Imprimer 1x 'ACHETEUR.BAT' et 1x 'AUDIT.BAT'.",
            "Aller dans Back Office → Reports and batches → Sales Journal Reports :",
            "  - Sélectionner 'Memo Listing', 'Sales Journals', '...by Costcenter' et Print.",
            "Classer les papiers imprimés selon les catégories."
        ],
        "tips_fr": "Daily Sales = 10 pages + 1 copie de la page 1. Ne pas oublier ACHETEUR.BAT et AUDIT.BAT.",
        "system_used": "VNC / POSitouch",
        "estimated_minutes": 15
    },
    {
        "order": 15,
        "title_fr": "Balancer les frais restaurant aux chambres",
        "category": "part1",
        "role": "back",
        "description_fr": "Vérifier que les frais restaurant facturés aux chambres balancent entre POSitouch et LightSpeed.",
        "steps": [
            "Imprimer le Cashier Detail dept. 4 à 28 (all sub) dans LightSpeed.",
            "Prendre les rapports POSitouch 'Memo Listing' identifiés 'Chambre' et 'Panne Lien'.",
            "Calculer : Total Panne Lien + Total Chambre ± Ajustements LightSpeed = Total LightSpeed.",
            "Comparer avec le total du Cashier Detail département 4-28.",
            "Quand tout balance : mettre les Memo Listings sur le Cashier Detail, brocher ensemble, mettre à côté du dossier bleu daté."
        ],
        "tips_fr": "S'il y a des ajustements manuels dans LightSpeed, il faut les ajouter ou soustraire au calcul.",
        "system_used": "LightSpeed / POSitouch",
        "estimated_minutes": 10
    },
    {
        "order": 16,
        "title_fr": "Vérifier les charges téléphones et Sonifi",
        "category": "part1",
        "role": "back",
        "description_fr": "Imprimer les Cashier Details des appels et de Sonifi, vérifier avec le Call Accounting.",
        "steps": [
            "Imprimer le Cashier Detail des appels locaux (30.1) avec le rapport des appels locaux.",
            "Imprimer le Cashier Detail d'appels longue distance (30.2).",
            "Imprimer le rapport 'Call Accounting'.",
            "Brocher les 2 feuilles avec le suivi Call Accounting. Mettre sur la pile Cashier Details.",
            "Imprimer le Cashier Detail avec Département 35, sous-département 2 (Sonifi).",
            "Mettre le Cashier Detail Sonifi sous l'écran — on le reprendra après le PART.",
            "IMPORTANT : même si tous les rapports sont à '0', les imprimer et encercler les '0'."
        ],
        "tips_fr": "Toujours imprimer les rapports même à 0$ — encercler les zéros pour prouver la vérification.",
        "system_used": "LightSpeed",
        "estimated_minutes": 8
    },

    # ─────────────────────────────────────────────────
    # PART2 — FEUX VERT / POST-PART (~03:00-05:00)
    # ─────────────────────────────────────────────────
    {
        "order": 17,
        "title_fr": "Feux vert — Tourner la nuit (PART)",
        "category": "part2",
        "role": "back",
        "description_fr": "Confirmer que tout est prêt pour le PART. Attendre que l'auditeur du front ait tourné la nuit.",
        "steps": [
            "Vérifier que tous les éléments pré-PART sont complétés :",
            "  - DueBack complété",
            "  - Terminaux Moneris fermés",
            "  - SD rempli (pas imprimé)",
            "  - Recap balancé et imprimé",
            "  - Transelect POSitouch complété",
            "  - Rapports POSitouch imprimés et triés",
            "  - Frais restaurant balancés",
            "  - Téléphones et Sonifi vérifiés",
            "Donner le feu vert à l'auditeur du front pour tourner la nuit.",
            "Attendre que le PART (Post Room and Tax + Run Audit) soit complété.",
            "Le système sera indisponible pendant le PART (~10-15 min)."
        ],
        "tips_fr": "Ne JAMAIS donner le feu vert si le Recap ne balance pas ou si les terminaux ne sont pas fermés.",
        "system_used": "LightSpeed",
        "estimated_minutes": 15
    },
    {
        "order": 18,
        "title_fr": "Compléter Sonifi et Internet (post-PART)",
        "category": "part2",
        "role": "back",
        "description_fr": "Compléter les onglets Sonifi et Internet du RJ avec les données post-PART.",
        "steps": [
            "SONIFI :",
            "  - Imprimer le fichier PDF du courriel SONIFI reçu à 03h00.",
            "  - Comparer avec le Cashier Detail 35.2 qui est sous l'écran.",
            "  - Si charges : compléter l'onglet SONIFI du RJ.",
            "  - Mettre rapport SONIFI sur le dessus, Cashier Detail en arrière, brocher ensemble, initialiser les totaux.",
            "  - Mettre sur la pile Cashier Details.",
            "INTERNET :",
            "  - Prendre le Cashier Detail 36.1 pour compléter la colonne B (Rapport LightSpeed) de l'onglet Internet.",
            "  - Prendre le Cashier Detail 36.5 pour compléter les colonnes F (ADJ Marriott).",
            "  - Mettre les 2 Cashier Details sur la pile.",
            "Prendre TOUTE la pile Cashier Details + RECAP + rapports dépôts + caisses réceptionnistes → mettre dans le dossier bleu daté."
        ],
        "tips_fr": "Le courriel Sonifi arrive à 3h00 AM. Si pas de charges, mettre quand même les rapports à 0$ dans la pile.",
        "system_used": "Outlook / LightSpeed / Excel",
        "estimated_minutes": 10
    },
    {
        "order": 19,
        "title_fr": "Trier les documents auditeur (pile DBRS)",
        "category": "part2",
        "role": "back",
        "description_fr": "Sortir les 5 documents clés de la pile 'Auditeur' et préparer la pile DBRS.",
        "steps": [
            "Dans la pile de rapports 'Auditeur' imprimée pendant l'audit, sortir les 5 documents suivants :",
            "  - Daily Revenue Report",
            "  - Advance Deposit Balance Sheet",
            "  - A/R Summary Report",
            "  - Complimentary Rooms Report",
            "  - Room Type Production",
            "Mettre la pile DBRS (superviseur réception) de côté — on en aura besoin pour les statistiques Jour et le DBRS.",
            "Mettre le 'A/R Summary Report' dans la feuille datée."
        ],
        "tips_fr": "Ces 5 documents sont essentiels pour compléter l'onglet Jour. Ne pas les mélanger avec le reste.",
        "system_used": "Manuel",
        "estimated_minutes": 5
    },
    {
        "order": 20,
        "title_fr": "Balancer FreedomPay et GEAC/UX",
        "category": "part2",
        "role": "back",
        "description_fr": "Compléter les sections FreedomPay du Transelect et balancer l'onglet GEAC/UX.",
        "steps": [
            "TRANSELECT (sections A et B) :",
            "  - Utiliser le Daily Revenue et le rapport FreedomPay pour compléter les sections A et B du Transelect.",
            "  - Sur FreedomPay : Rapport → Transaction Summary by Card Type → Exécuter → Statut → Télécharger l'Excel.",
            "  - Imprimer le document FreedomPay.",
            "  - Compléter les colonnes correspondantes dans le Transelect.",
            "GEAC/UX :",
            "  - Utiliser le rapport 'Daily Cash Out' pour compléter les 2 lignes de la section Daily Cash Out.",
            "  - Compléter la section Daily Revenue avec la page 6 du Daily Revenue.",
            "  - Vérifier que le rapport balance (variance = 0).",
            "  - Si variance : vérifier la saisie. Si toujours une variance, envoyer un courriel à Roula et Mandy.",
            "Imprimer 1 copie (Ctrl+P). Mettre les 2 pages face vers l'arrière sous la pile cartes de crédit."
        ],
        "tips_fr": "Le GEAC/UX doit balancer à 0$. Aucune correction possible de notre part sur une variance GEAC — on prévient Roula et Mandy.",
        "system_used": "FreedomPay / Excel / App Web",
        "estimated_minutes": 15
    },
    {
        "order": 21,
        "title_fr": "Assembler la pile cartes de crédit",
        "category": "part2",
        "role": "back",
        "description_fr": "Assembler tous les documents cartes de crédit dans l'ordre final.",
        "steps": [
            "Assembler la pile cartes de crédit dans cet ordre (du dessus vers l'arrière) :",
            "  1) Payment Breakdown (FuseBox) avec les fermetures terminaux Moneris brochées dessus",
            "  2) Settlement Details (FuseBox)",
            "  3) Pile imprimée par LightSpeed durant l'audition (Credit Card Not in BLT File sur le dessus)",
            "  4) 2 copies du Transelect face vers l'arrière",
            "  5) 2 pages du GEAC/UX face vers l'arrière",
            "Brocher la pile dans le coin haut gauche.",
            "Mettre de côté avec les documents dont on n'a plus besoin."
        ],
        "tips_fr": "Ordre précis obligatoire. Les 2 copies du Transelect et GEAC/UX sont face vers l'arrière.",
        "system_used": "Manuel",
        "estimated_minutes": 5
    },
    {
        "order": 22,
        "title_fr": "Compléter l'onglet Jour (restauration + ajustements)",
        "category": "part2",
        "role": "back",
        "description_fr": "Remplir l'onglet Jour du RJ avec les données de restauration (Sales Journal, HP, Cashier Details) et reporter les ajustements ADJ notés à l'étape 4.",
        "steps": [
            "SECTION RESTAURATION (colonnes E à AJ + AU + AX + AY + BF + BQ + BR) :",
            "  - Utiliser le rapport POSitouch 'SALES JOURNAL for Entire House'.",
            "  - Soustraire les montants du tableur Excel 'Rapport Quotidien des factures Hôtel Promotion'.",
            "  - Vérifier les Cashier Details pour les posts manuels en catégories F&B (rare).",
            "AJUSTEMENTS (ADJ) — Reporter les ajustements notés à l'étape 4 (Details Tickets) :",
            "  - Les codes 50+ sont des ajustements (ex: 28.51, 10.52, etc.)",
            "  - Ajouter chaque ajustement dans la colonne correspondante du département dans l'onglet Jour.",
            "Compléter l'onglet 'Diff_Forfait' si nécessaire (BF).",
            "Si forfaits Location de salle pour groupes : ajouter au 'Location de salle' banquets (colonne AG).",
            "S'il y a des frais internet dans les banquets : les ajouter dans la colonne AW."
        ],
        "tips_fr": "Bien soustraire les HP du Sales Journal avant de reporter. Ne pas oublier les ajustements ADJ (code 50+) notés à l'étape 4 — ils doivent être reportés dans le Jour. Les forfaits location de salle vont dans la colonne AG (banquets).",
        "system_used": "Excel / POSitouch",
        "estimated_minutes": 20
    },
    {
        "order": 23,
        "title_fr": "Compléter l'onglet Jour (Daily Revenue et stats)",
        "category": "part2",
        "role": "back",
        "description_fr": "Remplir les colonnes Daily Revenue, statistiques d'occupation et vérifier Diff.Caisse.",
        "steps": [
            "Compléter les colonnes Daily Revenue : AK-AL-AM-AN-AO-AS-AT-AU-AV-AW-AX-AY-AZ-BA-BB-BC-BD-BF-CB-CC.",
            "Utiliser 'Total Transfers' du A/R Summary Report pour la colonne 'Transfer to A/R' (CF).",
            "Colonne D : mettre en négatif le 'Deposit on Hand Today' (Advance Deposit Balance Sheet) et le New Balance du Daily Revenue.",
            "Utiliser le 'Departures/Arrivals/Stayovers' de la pile DBRS pour :",
            "  - Nombre de clients (colonne CO)",
            "  - Nombre de chambres hors service (colonne CP)",
            "Utiliser le 'Complimentary Rooms Report' pour :",
            "  - Nombre de chambres occupées (colonne CK)",
            "  - Nombre de chambres complémentaires (colonne CN)",
            "Vérifier que la colonne Diff.Caisse (colonne C) est à 0$.",
            "Si Diff.Caisse ≠ 0 : variance dans GEAC/UX ou différence cartes de crédit.",
            "Aller sur l'onglet 'CONTRÔLE' et cliquer le bouton d'impression.",
            "Distribuer les copies : pigeonniers, classeur du chef (semaine), bureau superviseurs, 'Vérification' sur la pile gauche."
        ],
        "tips_fr": "Diff.Caisse DOIT être 0$. Sinon, vérifier le GEAC/UX et les cartes de crédit. Deposit on Hand = toujours en négatif.",
        "system_used": "Excel / LightSpeed",
        "estimated_minutes": 20
    },

    # ─────────────────────────────────────────────────
    # END_SHIFT — Finalisation (~05:00-07:00)
    # ─────────────────────────────────────────────────
    {
        "order": 24,
        "title_fr": "Assembler les documents HP Admin",
        "category": "end_shift",
        "role": "back",
        "description_fr": "Assembler les factures HP/Admin avec les Memo Listings POSitouch.",
        "steps": [
            "Prendre les documents dans le porte-crayon à droite de l'écran :",
            "  - Sales Journal Report for Entire House (2 pages)",
            "  - 2 pages du rapport Excel Hotel Prom",
            "  - Rapports POSitouch Memo Listing 'ADMIN' et 'HOTEL PROM'",
            "Brocher les factures POSitouch ADMIN avec le Memo Listing ADMIN.",
            "Brocher les factures POSitouch Hotel Prom avec le Memo Listing Hotel Prom.",
            "'Rapport Quotidien des factures Hôtel Promotion' (portrait) sur le dessus.",
            "'Rapport Journalier Hôtel Promotion' (paysage) face vers l'arrière en dessous.",
            "Brocher le tout au milieu dans le côté gauche."
        ],
        "tips_fr": "Portrait sur le dessus, paysage face vers l'arrière en dessous. Brocher au milieu à gauche.",
        "system_used": "Manuel",
        "estimated_minutes": 5
    },
    {
        "order": 25,
        "title_fr": "Balancer le Quasimodo",
        "category": "end_shift",
        "role": "back",
        "description_fr": "Créer et remplir le fichier Quasimodo pour la réconciliation des cartes de crédit.",
        "steps": [
            "Aller dans le dossier 'Quasimodo' sur le bureau → année en cours → mois en cours.",
            "Copier un fichier Excel existant et le renommer selon la date avant audit.",
            "Changer la date dans la cellule jaune (et le mois dans le titre au changement de mois).",
            "Remplir les données À PARTIR DU TRANSELECT : reporter les totaux par type de carte.",
            "Remplir les données À PARTIR DU RJ : reporter les montants correspondants.",
            "Vérifier que chaque type de carte balance : Terminal = Banque.",
            "Visa, MC, Amex, Debit doivent tous avoir variance 0.00$.",
            "Si variance > 0.01$ : vérifier le batch Moneris ou contacter Roula/Mandy.",
            "Ou utiliser le bouton 'Quasimodo' de l'application web pour générer automatiquement."
        ],
        "tips_fr": "Le Quasimodo peut être généré automatiquement par l'application web. La réconciliation doit être parfaite.",
        "system_used": "Excel / App Web",
        "estimated_minutes": 15
    },
    {
        "order": 26,
        "title_fr": "Assembler l'enveloppe blanche et le dossier bleu",
        "category": "end_shift",
        "role": "back",
        "description_fr": "Assembler tous les documents dans l'enveloppe blanche (comptabilité) et le dossier bleu daté.",
        "steps": [
            "SUR le dossier bleu daté (ordre du dessus vers le bas) :",
            "  - Pile factures POSitouch avec coupon vert",
            "  - Pile factures POSitouch par carte (Débit/Visa/MC/Amex)",
            "  - Pile factures POSitouch chambres/compte maître + readings serveurs",
            "  - Memo Listing Bon d'Achat + factures (si applicable)",
            "  - Memo Listing Certificat Cadeau + factures (si applicable)",
            "  - Memo Listing Forfait + factures (si applicable)",
            "  - Daily Sales Report 9 pages (rapport Établissement broché dessus)",
            "  - Daily Cash Out Report (All Cashier broché dessus)",
            "  - Guest Ledger Summary, Detail Ticket, Room Post Audit, Availability Rebuild Exception",
            "  - Sales Journal Payment Totals",
            "  - Memo Listing Chambre + panne lien + Cashier Detail 4-28 brochés",
            "DANS le dossier bleu (ordre spécifique) :",
            "  - RJ copie Vérification, Daily Revenue, Advance Deposit, Sales Journal Entire House",
            "  - Pile cartes de crédit combinée",
            "  - HP/Admin pack, Complimentary Report, Room Type Production",
            "  - Cashier Details brochés, RECAP, SD, caisses réceptionnistes",
            "  - Group Delegates et Wholesalers",
            "Mettre l'enveloppe blanche dans le pigeonnier de la comptabilité."
        ],
        "tips_fr": "Rien ne doit rester sur le bureau. Tout va dans l'enveloppe ou le dossier bleu. Vérifier deux fois avant de fermer.",
        "system_used": "Manuel",
        "estimated_minutes": 15
    },
    {
        "order": 27,
        "title_fr": "Compléter le DBRS",
        "category": "end_shift",
        "role": "back",
        "description_fr": "Remplir le DBRS formule et master avec les données de Market Segment, Daily Revenue et OTB.",
        "steps": [
            "Ouvrir les fichiers Excel 'DBRS formule' et 'DBRS master'.",
            "Compléter l'onglet 'Market Segment' dans DBRS formule (colonne 'rooms' du Market Segment).",
            "Compléter l'onglet 'Daily Rev' dans DBRS formule (colonne 'Today' du Daily Revenue Report).",
            "Vérifier les ADR dans l'onglet 'DBRS'.",
            "Cliquer 'Sélectionner et copier' dans l'onglet 'DBRS insertion'.",
            "Dans 'DBRS master' : aller au mois en cours, coller (Collage spécial : Valeurs, Largeur colonnes).",
            "Utiliser le rapport 'House Count' pour les sections après le collage.",
            "Dans l'onglet 'Set up' : changer la date pour celle avant audit.",
            "Dans l'onglet 'DBRS cover' :",
            "  - Compléter le montant NoShow dans le tableau du haut",
            "  - Cliquer 'Unhide OTB' → remplir 'Group OTB' avec la colonne RESV du rapport Allotment Overview",
            "  - Compléter les autres lignes jaunes avec Departure/Arrival/Stayover",
            "Point de vérification : le ADR doit être vraisemblable.",
            "Sauvegarder et fermer.",
            "Mettre la pile DBRS sur le bureau des superviseurs avec trombone."
        ],
        "tips_fr": "Le ADR est le point de vérification principal. Si le ADR semble anormal, revérifier la saisie Market Segment et Daily Rev.",
        "system_used": "Excel DBRS",
        "estimated_minutes": 20
    },
    {
        "order": 28,
        "title_fr": "Finaliser, ranger et distribuer",
        "category": "end_shift",
        "role": "back",
        "description_fr": "Dernières vérifications, porter l'enveloppe, remonter le papier et nettoyer.",
        "steps": [
            "Porter l'enveloppe blanche et le pigeonnier mobile à la comptabilité.",
            "Remonter des paquets de feuilles blanches s'il en reste moins de 2 paquets.",
            "Le TravelClick retourne sous l'écran de l'ordinateur auditeur.",
            "Faire un dernier tour du bureau pour s'assurer que tout est rangé.",
            "Vérifier que le fichier RJ final est sauvegardé.",
            "S'assurer que toutes les impressions sont distribuées aux bons endroits."
        ],
        "tips_fr": "Vérifier le niveau de papier dans l'imprimante. Rien ne doit rester sur le bureau de l'auditeur.",
        "system_used": "Manuel",
        "estimated_minutes": 5
    }
]

from scripts.seed_tasks_front import TASKS_DETAILED as TASKS_FRONT_DATA

def _upsert_task(task_data, role):
    """Update existing task or create new one. Matches by (order, role) to preserve IDs."""
    existing = Task.query.filter_by(order=task_data["order"], role=role).first()

    fields = {
        'title_fr': task_data["title_fr"],
        'category': task_data["category"],
        'is_active': True,
        'description_fr': task_data.get("description_fr"),
        'steps_json': json.dumps(task_data.get("steps", []), ensure_ascii=False) if task_data.get("steps") else None,
        'screenshots_json': json.dumps(task_data.get("screenshots", []), ensure_ascii=False),
        'tips_fr': task_data.get("tips_fr"),
        'system_used': task_data.get("system_used"),
        'estimated_minutes': task_data.get("estimated_minutes"),
    }

    if existing:
        for key, value in fields.items():
            setattr(existing, key, value)
        return 'updated'
    else:
        task = Task(order=task_data["order"], role=role, **fields)
        db.session.add(task)
        return 'created'


def seed_tasks():
    app = create_app()
    with app.app_context():
        created = 0
        updated = 0

        # Upsert Front Tasks (preserves task IDs → completions stay valid)
        for task_data in TASKS_FRONT_DATA:
            result = _upsert_task(task_data, 'front')
            if result == 'created':
                created += 1
            else:
                updated += 1

        # Upsert Back Tasks
        for task_data in TASKS_BACK:
            result = _upsert_task(task_data, 'back')
            if result == 'created':
                created += 1
            else:
                updated += 1

        # Deactivate tasks that are no longer in the seed data
        front_orders = {t["order"] for t in TASKS_FRONT_DATA}
        back_orders = {t["order"] for t in TASKS_BACK}

        orphan_front = Task.query.filter(Task.role == 'front', ~Task.order.in_(front_orders)).all()
        orphan_back = Task.query.filter(Task.role == 'back', ~Task.order.in_(back_orders)).all()
        deactivated = 0
        for t in orphan_front + orphan_back:
            t.is_active = False
            deactivated += 1

        db.session.commit()

        total_front = len(TASKS_FRONT_DATA)
        total_back = len(TASKS_BACK)
        print(f"✅ Seed terminé: {total_front} FRONT + {total_back} BACK tâches")
        print(f"   → {created} créées, {updated} mises à jour, {deactivated} désactivées")
        print(f"   ✓ Les complétions existantes sont préservées (IDs stables)")


if __name__ == '__main__':
    seed_tasks()
