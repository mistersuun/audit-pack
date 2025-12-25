"""
Seed script to load Front and Back office tasks into the database.
Run this once after setting up the database: python seed_tasks.py
"""

import json
from main import create_app
from database import db, Task

# ================= FRONT OFFICE TASKS =================
TASKS_FRONT = [
    # ... (Keep existing Front tasks here, I will just reference them for brevity in this thought process, 
    # but in the actual file write I must include them all or read them)
    # Actually, to be safe and clean, I will re-declare the full list of 47 Front tasks 
    # plus the new Back tasks.
]

# I will assume the previous content of TASKS_DETAILED is what I should use for TASKS_FRONT.
# I will copy the previous content and add role='front' to the dicts in the loop.

# ================= BACK OFFICE TASKS =================
TASKS_BACK = [
    {
        "order": 1,
        "title_fr": "Setup poste & Reset RJ",
        "category": "pre_audit",
        "role": "back",
        "description_fr": "Préparation de l'environnement et création du fichier RJ du jour.",
        "steps": [
            "Ouvrir LightSpeed, Empower, VNC",
            "Ouvrir RJ d'hier et 'Enregistrer sous' date d'aujourd'hui",
            "Mettre à jour l'onglet Contrôle",
            "Effacer les onglets RECAP, TRANSELECT, GEAC/UX (Utiliser bouton Reset dans le guide)"
        ],
        "tips_fr": "Assurez-vous de ne pas écraser le fichier d'hier!",
        "system_used": "Excel RJ",
        "estimated_minutes": 15
    },
    {
        "order": 2,
        "title_fr": "Triage des factures",
        "category": "pre_audit",
        "role": "back",
        "description_fr": "Organiser tous les documents F&B et Réception.",
        "steps": [
            "Séparer Réception vs F&B",
            "Classer F&B par mode de paiement (Débit, Visa, MC, Amex)",
            "Vérifier la présence de tous les bordereaux de dépôt"
        ],
        "tips_fr": "Un bon triage maintenant sauve du temps pour le Transelect.",
        "system_used": "Papier",
        "estimated_minutes": 20
    },
    {
        "order": 3,
        "title_fr": "Cashier Details & DueBack",
        "category": "part1",
        "role": "back",
        "description_fr": "Vérifier les caisses réception et calculer les DueBacks.",
        "steps": [
            "Imprimer Cashier Details (Dept 2, 90.x)",
            "Noter tous les ajustements (codes 50+)",
            "Extraire paiements Interac et Chèques",
            "Compléter l'onglet DueBack dans le RJ",
            "Fermer folio Dépôt Restaurant (40.52)"
        ],
        "tips_fr": "Utilisez le bouton 'Sync DueBack' pour transférer vers SetD.",
        "system_used": "LightSpeed / RJ",
        "estimated_minutes": 30
    },
    {
        "order": 4,
        "title_fr": "Fermeture Moneris",
        "category": "part1",
        "role": "back",
        "description_fr": "Fermer les 4 terminaux de paiement.",
        "steps": [
            "Fermer terminal Réception",
            "Fermer terminal Bar",
            "Fermer terminal Room Service",
            "Fermer terminal Banquet",
            "Récupérer et encercler les rapports de batch"
        ],
        "tips_fr": "À faire impérativement avant 03h00.",
        "system_used": "Moneris",
        "estimated_minutes": 15
    },
    {
        "order": 5,
        "title_fr": "Rapports VNC (Pré-Part)",
        "category": "part1",
        "role": "back",
        "description_fr": "Imprimer les rapports POSitouch via VNC.",
        "steps": [
            "Vérifier CloseBATCH",
            "Imprimer Établissement & Spesa",
            "Imprimer Daily Sales Report (9 pages + page 1)",
            "Imprimer Acheteur.bat et Audit.bat"
        ],
        "tips_fr": "Gardez le DSR page 5-6 proche pour le RECAP.",
        "system_used": "VNC / POSitouch",
        "estimated_minutes": 45
    },
    {
        "order": 6,
        "title_fr": "Saisie HP / Admin",
        "category": "part1",
        "role": "back",
        "description_fr": "Saisir les factures internes dans le fichier HP-ADMIN.",
        "steps": [
            "Ouvrir HP-ADMIN.xlsx",
            "Filtrer pour les dates vides",
            "Saisir chaque facture (Nourriture, Boisson, etc.)",
            "Rafraîchir l'onglet Journalier et imprimer"
        ],
        "tips_fr": "Attention à bien sélectionner Administration ou Promotion.",
        "system_used": "Excel HP-ADMIN",
        "estimated_minutes": 20
    },
    {
        "order": 7,
        "title_fr": "Sommaire Dépôts (SD)",
        "category": "part1",
        "role": "back",
        "description_fr": "Compter le cash et balancer avec POSitouch.",
        "steps": [
            "Ouvrir SD-[DATE].xls",
            "Compter chaque enveloppe du coffre",
            "Comparer avec montants DSR page 5",
            "Calculer et expliquer les variances",
            "Signer et faire signer si nécessaire"
        ],
        "tips_fr": "Variance > 5$ demande signature superviseur.",
        "system_used": "Excel SD",
        "estimated_minutes": 30
    },
    {
        "order": 8,
        "title_fr": "Balancer RECAP (Comptant)",
        "category": "part1",
        "role": "back",
        "description_fr": "Balancer le comptant total de l'hôtel.",
        "steps": [
            "Dans RJ onglet RECAP",
            "Entrer comptant LightSpeed et POSitouch",
            "Vérifier que la variance est 0.00$",
            "Utiliser le formulaire automatique ci-dessous"
        ],
        "tips_fr": "Si ça ne balance pas, revérifiez le SD et le DueBack.",
        "system_used": "RJ Recap",
        "estimated_minutes": 20
    },
    {
        "order": 9,
        "title_fr": "Mise à jour Dépôt RJ",
        "category": "part2",
        "role": "back",
        "description_fr": "Transférer le montant vérifié du SD vers le RJ.",
        "steps": [
            "Prendre le total 'Montant Vérifié' du SD",
            "L'inscrire dans l'onglet Dépôt du RJ",
            "Utiliser le bouton automatique ci-dessous"
        ],
        "tips_fr": "C'est ce montant qui va à la banque.",
        "system_used": "RJ Dépôt",
        "estimated_minutes": 5
    },
    {
        "order": 10,
        "title_fr": "Transelect (Cartes de crédit)",
        "category": "part2",
        "role": "back",
        "description_fr": "Balancer toutes les transactions cartes de crédit.",
        "steps": [
            "Entrer montants POSitouch (Bar/Spesa)",
            "Entrer montants Moneris (Réception)",
            "Entrer montants FreedomPay (Fuseboxe)",
            "Vérifier que chaque colonne balance",
            "Utiliser la grille de saisie ci-dessous"
        ],
        "tips_fr": "Variance acceptable: 0.01$.",
        "system_used": "RJ Transelect",
        "estimated_minutes": 40
    },
    {
        "order": 11,
        "title_fr": "Rapports POSitouch Détails",
        "category": "part2",
        "role": "back",
        "description_fr": "Vérifier les charges chambres restaurant.",
        "steps": [
            "Imprimer Memo Listings (Chambre, Panne Lien)",
            "Comparer avec Cashier Detail 4-28",
            "Faire ajustements si nécessaire"
        ],
        "tips_fr": None,
        "system_used": "POSitouch / LS",
        "estimated_minutes": 30
    },
    {
        "order": 12,
        "title_fr": "Téléphone, Sonifi & Internet",
        "category": "part2",
        "role": "back",
        "description_fr": "Vérifier les revenus divers.",
        "steps": [
            "Imprimer Cashier Details 30.x, 35.x, 36.x",
            "Comparer avec rapports systèmes (Sonifi email)",
            "Compléter onglets RJ correspondants"
        ],
        "tips_fr": "Attention aux ajustements Marriott pour internet.",
        "system_used": "LS / RJ",
        "estimated_minutes": 20
    },
    {
        "order": 13,
        "title_fr": "GEAC/UX & Pile CC",
        "category": "part2",
        "role": "back",
        "description_fr": "Finaliser la balance des cartes de crédit.",
        "steps": [
            "Compléter onglet GEAC/UX avec Daily Cash Out",
            "Vérifier balance à 0.00$",
            "Assembler la pile de cartes de crédit finale"
        ],
        "tips_fr": "Utilisez le formulaire GEAC ci-dessous.",
        "system_used": "RJ GEAC",
        "estimated_minutes": 20
    },
    {
        "order": 14,
        "title_fr": "Onglet Jour & Transfert",
        "category": "part2",
        "role": "back",
        "description_fr": "Finaliser le RJ et transférer les données.",
        "steps": [
            "Entrer statistiques chambres (CK, CN...)",
            "Entrer revenus F&B",
            "Vérifier 'Diff Caisse' = 0",
            "Cliquer sur le bouton TRANSFERT dans l'onglet Contrôle"
        ],
        "tips_fr": "C'est la dernière étape du RJ avant impression.",
        "system_used": "RJ Jour",
        "estimated_minutes": 30
    },
    {
        "order": 15,
        "title_fr": "Quasimodo & DBRS",
        "category": "end_shift",
        "role": "back",
        "description_fr": "Rapports finaux de management.",
        "steps": [
            "Compléter fichier Quasimodo",
            "Compléter fichier DBRS (Market segment, Rev, ADR)",
            "Imprimer et distribuer"
        ],
        "tips_fr": "Le DBRS doit être sur le bureau du superviseur.",
        "system_used": "Excel",
        "estimated_minutes": 35
    },
    {
        "order": 16,
        "title_fr": "Assemblage Final",
        "category": "end_shift",
        "role": "back",
        "description_fr": "Préparer l'enveloppe blanche et les pigeonniers.",
        "steps": [
            "Mettre tous les documents dans l'enveloppe blanche",
            "Distribuer les copies aux managers",
            "Envoyer courriels de fin de quart"
        ],
        "tips_fr": "Rien ne doit rester sur le bureau.",
        "system_used": "Papier",
        "estimated_minutes": 30
    }
]

from seed_tasks_front import TASKS_DETAILED as TASKS_FRONT_DATA

def seed_tasks():
    app = create_app()
    with app.app_context():
        # Clear existing tasks
        Task.query.delete()

        # Seed Front Tasks
        for task_data in TASKS_FRONT_DATA:
            task = Task(
                order=task_data["order"],
                title_fr=task_data["title_fr"],
                category=task_data["category"],
                role="front",
                is_active=True,
                description_fr=task_data.get("description_fr"),
                steps_json=json.dumps(task_data.get("steps", []), ensure_ascii=False) if task_data.get("steps") else None,
                screenshots_json=json.dumps(task_data.get("screenshots", []), ensure_ascii=False) if task_data.get("screenshots") else None,
                tips_fr=task_data.get("tips_fr"),
                system_used=task_data.get("system_used"),
                estimated_minutes=task_data.get("estimated_minutes")
            )
            db.session.add(task)
            
        # Seed Back Tasks
        for task_data in TASKS_BACK:
            task = Task(
                order=task_data["order"],
                title_fr=task_data["title_fr"],
                category=task_data["category"],
                role="back",
                is_active=True,
                description_fr=task_data.get("description_fr"),
                steps_json=json.dumps(task_data.get("steps", []), ensure_ascii=False) if task_data.get("steps") else None,
                screenshots_json=json.dumps(task_data.get("screenshots", []), ensure_ascii=False) if task_data.get("screenshots") else None,
                tips_fr=task_data.get("tips_fr"),
                system_used=task_data.get("system_used"),
                estimated_minutes=task_data.get("estimated_minutes")
            )
            db.session.add(task)

        db.session.commit()
        print(f"✅ Seeded {len(TASKS_FRONT_DATA)} FRONT tasks and {len(TASKS_BACK)} BACK tasks!")

if __name__ == '__main__':
    seed_tasks()