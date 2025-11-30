"""
Seed script to load the 46 front desk night audit tasks into the database.
Run this once after setting up the database: python seed_tasks.py

Tasks include detailed step-by-step instructions where available.
"""

import json
from main import create_app
from database import db, Task

# Detailed task definitions with instructions
# Format: (order, title_fr, category, description_fr, steps, tips_fr, system_used, estimated_minutes, screenshots)

TASKS_DETAILED = [
    # ============= PRE-AUDIT (1-9) =============
    {
        "order": 1,
        "title_fr": "Échange d'informations avec le quart du soir (arrivées restantes, situations clients, groupes, etc.).",
        "category": "pre_audit",
        "description_fr": "Cette étape est cruciale pour assurer une transition fluide entre les quarts. Vous devez être au courant de toutes les situations en cours.",
        "steps": [
            "Rencontrer l'agent du quart du soir à la réception",
            "Demander combien d'arrivées sont encore attendues ce soir",
            "Vérifier s'il y a des groupes en maison ou attendus",
            "Noter toute situation client particulière (plaintes, demandes spéciales, VIP)",
            "Vérifier s'il y a des chambres hors service ou en maintenance",
            "Demander s'il y a des messages ou suivis importants à faire"
        ],
        "tips_fr": "Prenez des notes! Les informations importantes peuvent être oubliées pendant une nuit chargée.",
        "system_used": None,
        "estimated_minutes": 5,
        "screenshots": []
    },
    {
        "order": 2,
        "title_fr": "Vérifier le panneau incendie et vous mettre en alarme pour retirer les dérivations au besoin.",
        "category": "pre_audit",
        "description_fr": "Vérification de sécurité obligatoire. Le panneau incendie doit être en état normal avant de commencer le quart.",
        "steps": [
            "Se rendre au panneau incendie (situé dans le bureau de sécurité)",
            "Vérifier que l'écran affiche 'NORMAL' ou 'SYSTEM OK'",
            "Si des dérivations (bypass) sont actives, noter les zones concernées",
            "Contacter la maintenance si des anomalies sont présentes",
            "Se mettre en alarme sur le système si requis"
        ],
        "tips_fr": "IMPORTANT: Ne jamais ignorer une alarme incendie. En cas de doute, suivre la procédure d'urgence.",
        "system_used": "Panneau incendie",
        "estimated_minutes": 3,
        "screenshots": []
    },
    {
        "order": 3,
        "title_fr": "Se connecter sur Lightspeed (Galaxy), Empower/GXP et Control Panel pour clés mobiles.",
        "category": "pre_audit",
        "description_fr": "Connexion aux systèmes principaux utilisés pendant le quart de nuit.",
        "steps": [
            "Ouvrir Galaxy Lightspeed sur l'ordinateur principal",
            "Entrer vos identifiants de connexion",
            "Ouvrir Empower/GXP dans un autre onglet ou fenêtre",
            "Se connecter avec vos identifiants GXP",
            "Ouvrir le Control Panel pour les clés mobiles",
            "Vérifier que tous les systèmes répondent correctement"
        ],
        "tips_fr": "Gardez vos mots de passe en sécurité. Ne les partagez jamais avec d'autres employés.",
        "system_used": "Lightspeed, GXP, Mobile Key Control Panel",
        "estimated_minutes": 3,
        "screenshots": ["lightspeed_login.png", "gxp_login.png"]
    },
    {
        "order": 4,
        "title_fr": "Faire vos questions du jour sur DLZ.",
        "category": "pre_audit",
        "description_fr": "Compléter les questions quotidiennes sur la plateforme DLZ de Marriott.",
        "steps": [
            "Ouvrir le navigateur et accéder à DLZ",
            "Se connecter avec vos identifiants Marriott",
            "Aller dans la section 'Daily Questions' ou 'Questions du jour'",
            "Répondre à toutes les questions disponibles",
            "Soumettre vos réponses"
        ],
        "tips_fr": "Les questions DLZ comptent pour votre formation continue. Prenez le temps de bien lire les questions.",
        "system_used": "DLZ",
        "estimated_minutes": 10,
        "screenshots": []
    },
    {
        "order": 5,
        "title_fr": "Remplir les imprimantes de papiers, vérifier que l'encre est adéquate pour l'impression.",
        "category": "pre_audit",
        "description_fr": "S'assurer que les imprimantes sont prêtes pour la nuit. Beaucoup de rapports seront imprimés.",
        "steps": [
            "Vérifier le niveau de papier dans l'imprimante principale",
            "Ajouter du papier si le bac est moins qu'à moitié plein",
            "Vérifier l'imprimante de reçus",
            "Faire un test d'impression si nécessaire",
            "Vérifier les niveaux d'encre/toner sur l'écran de l'imprimante"
        ],
        "tips_fr": "Le papier est rangé dans l'armoire du bureau arrière. Prévoir suffisamment pour toute la nuit.",
        "system_used": None,
        "estimated_minutes": 5,
        "screenshots": []
    },
    {
        "order": 6,
        "title_fr": "Vérifier les wake up calls (Cahier de réception vs Espresso). Faire les ajouts au besoin.",
        "category": "pre_audit",
        "description_fr": "S'assurer que tous les appels de réveil demandés par les clients sont programmés correctement.",
        "steps": [
            "Ouvrir le cahier de réception et trouver la section 'Wake Up Calls'",
            "Ouvrir le système Espresso sur l'ordinateur",
            "Comparer les demandes dans le cahier avec celles dans Espresso",
            "Ajouter dans Espresso les appels manquants",
            "Vérifier les heures et numéros de chambre"
        ],
        "tips_fr": "Un appel de réveil manqué peut causer un client à manquer son vol. Double-vérifiez toujours!",
        "system_used": "Espresso",
        "estimated_minutes": 5,
        "screenshots": ["espresso_wakeup.png"]
    },
    {
        "order": 7,
        "title_fr": "Imprimer le séparateur daté.",
        "category": "pre_audit",
        "description_fr": "Le séparateur daté permet d'organiser les documents de la nuit.",
        "steps": [
            "Dans Lightspeed, aller au menu des rapports",
            "Sélectionner 'Séparateur daté' ou créer manuellement",
            "Imprimer le séparateur avec la date du jour",
            "Placer dans la pile de documents de la nuit"
        ],
        "tips_fr": None,
        "system_used": "Lightspeed",
        "estimated_minutes": 2,
        "screenshots": []
    },
    {
        "order": 8,
        "title_fr": "Imprimer la feuille de tournée des étages.",
        "category": "pre_audit",
        "description_fr": "Cette feuille sera utilisée lors de la tournée de sécurité des étages.",
        "steps": [
            "Accéder au modèle de feuille de tournée",
            "Imprimer une copie",
            "Garder à portée de main pour la tournée plus tard dans la nuit"
        ],
        "tips_fr": None,
        "system_used": None,
        "estimated_minutes": 2,
        "screenshots": []
    },
    {
        "order": 9,
        "title_fr": "Imprimer la feuille de déneigement avec screenshot de météo du jour à venir.",
        "category": "pre_audit",
        "description_fr": "Information importante pour l'équipe de maintenance concernant les conditions météo.",
        "steps": [
            "Ouvrir un site météo fiable (MétéoMédia, Environnement Canada)",
            "Faire une capture d'écran des prévisions pour demain",
            "Imprimer la capture d'écran",
            "Remplir la feuille de déneigement si de la neige est prévue",
            "Placer dans la pile pour la maintenance"
        ],
        "tips_fr": "En hiver, cette information est critique pour planifier le déneigement du stationnement.",
        "system_used": None,
        "estimated_minutes": 5,
        "screenshots": []
    },

    # ============= PART 1 (10-22) =============
    {
        "order": 10,
        "title_fr": "Run PART 1 – Pre Audit Reports.",
        "category": "part1",
        "description_fr": "Lancement de la première partie de l'audit de nuit dans Lightspeed. Cette étape génère les rapports préliminaires.",
        "steps": [
            "Dans Lightspeed, aller au menu 'Night Audit'",
            "Sélectionner 'PART 1 - Pre Audit Reports'",
            "Cliquer sur 'Run' ou 'Exécuter'",
            "Attendre que tous les rapports soient générés",
            "Vérifier qu'il n'y a pas d'erreurs affichées",
            "Imprimer les rapports générés"
        ],
        "tips_fr": "Ne jamais interrompre le processus une fois lancé. Cela peut corrompre les données.",
        "system_used": "Lightspeed",
        "estimated_minutes": 15,
        "screenshots": ["lightspeed_part1.png"]
    },
    {
        "order": 11,
        "title_fr": "Ajouter folios à zéro (Actual Departure Report), au besoin seulement.",
        "category": "part1",
        "description_fr": "Vérifier les départs du jour et s'assurer que les folios sont à zéro avant le check-out.",
        "steps": [
            "Consulter le 'Actual Departure Report' généré au PART 1",
            "Identifier les chambres avec un solde non-zéro",
            "Pour chaque folio avec solde, vérifier la méthode de paiement",
            "Ajuster ou collecter le paiement au besoin",
            "Mettre le folio à zéro"
        ],
        "tips_fr": "Cette étape n'est requise que si des folios ont un solde. Si tous sont à zéro, passer à la prochaine tâche.",
        "system_used": "Lightspeed",
        "estimated_minutes": 10,
        "screenshots": []
    },
    {
        "order": 12,
        "title_fr": "Imprimer Guest List Delegates pour les groupes, mettre dans la filière bleue du jour.",
        "category": "part1",
        "description_fr": "Liste des délégués de groupes pour le suivi.",
        "steps": [
            "Dans Lightspeed, aller à Reports > Guest Lists",
            "Sélectionner 'Delegates' et filtrer par groupes",
            "Imprimer le rapport",
            "Placer dans la filière bleue du jour concerné"
        ],
        "tips_fr": None,
        "system_used": "Lightspeed",
        "estimated_minutes": 3,
        "screenshots": []
    },
    {
        "order": 13,
        "title_fr": "Imprimer Guest List Delegates pour Wholesalers, mettre dans la filière bleue du jour.",
        "category": "part1",
        "description_fr": "Liste des clients venant par wholesalers (agences de voyage en gros).",
        "steps": [
            "Dans Lightspeed, aller à Reports > Guest Lists",
            "Sélectionner 'Delegates' et filtrer par Wholesalers",
            "Imprimer le rapport",
            "Placer dans la filière bleue du jour concerné"
        ],
        "tips_fr": None,
        "system_used": "Lightspeed",
        "estimated_minutes": 3,
        "screenshots": []
    },
    {
        "order": 14,
        "title_fr": "Faire et imprimer feuille de contrôle pour Fedex, Cargojet et UPS (si non reçu par courriel).",
        "category": "part1",
        "description_fr": "Préparation des documents pour les livraisons de colis.",
        "steps": [
            "Vérifier si la feuille de contrôle a été reçue par courriel",
            "Si non reçue, créer la feuille manuellement",
            "Lister tous les colis attendus ou à envoyer",
            "Imprimer et garder à la réception"
        ],
        "tips_fr": "Si la feuille arrive par courriel, cette étape peut être sautée.",
        "system_used": None,
        "estimated_minutes": 5,
        "screenshots": []
    },
    {
        "order": 15,
        "title_fr": "Imprimer le rapport Room Status Details. (Pile pour Gouvernante).",
        "category": "part1",
        "description_fr": "Rapport sur l'état de toutes les chambres pour l'équipe d'entretien ménager.",
        "steps": [
            "Dans Lightspeed, aller à Reports > Housekeeping",
            "Sélectionner 'Room Status Details'",
            "Imprimer le rapport",
            "Placer dans la pile désignée pour la Gouvernante"
        ],
        "tips_fr": None,
        "system_used": "Lightspeed",
        "estimated_minutes": 3,
        "screenshots": []
    },
    {
        "order": 16,
        "title_fr": "Faire copie des changements de chambre et faire copie de la feuille des travaux. (Pile Gouvernante).",
        "category": "part1",
        "description_fr": "Documents importants pour l'équipe d'entretien.",
        "steps": [
            "Récupérer la liste des changements de chambre du jour",
            "Faire une photocopie",
            "Récupérer la feuille des travaux de maintenance",
            "Faire une photocopie",
            "Placer les copies dans la pile pour la Gouvernante"
        ],
        "tips_fr": None,
        "system_used": None,
        "estimated_minutes": 5,
        "screenshots": []
    },
    {
        "order": 17,
        "title_fr": "Vérifier Folio Amex/Visa : s'il y a une charge dans le folio, nous devons prendre le paiement en Facture Directe.",
        "category": "part1",
        "description_fr": "Vérification des folios corporatifs Amex/Visa pour facturation directe.",
        "steps": [
            "Dans Lightspeed, rechercher les folios Amex et Visa corporatifs",
            "Vérifier si des charges sont présentes",
            "Si oui, traiter le paiement en Facture Directe",
            "Générer la facture et envoyer au département concerné"
        ],
        "tips_fr": "Les folios corporatifs doivent être traités différemment des folios individuels.",
        "system_used": "Lightspeed",
        "estimated_minutes": 10,
        "screenshots": []
    },
    {
        "order": 18,
        "title_fr": "Compléter les contrats Banquets (1 copie du folio + 1 copie des factures originales).",
        "category": "part1",
        "description_fr": "Finalisation des documents de banquets pour la comptabilité.",
        "steps": [
            "Récupérer les contrats de banquets du jour",
            "Imprimer une copie du folio pour chaque événement",
            "Imprimer une copie des factures originales",
            "Assembler les documents ensemble",
            "Placer dans la pile pour la comptabilité"
        ],
        "tips_fr": None,
        "system_used": "Lightspeed",
        "estimated_minutes": 10,
        "screenshots": []
    },
    {
        "order": 19,
        "title_fr": "Préparer la liste et les clés banquets pour les événements de demain.",
        "category": "part1",
        "description_fr": "Préparation pour les événements du lendemain.",
        "steps": [
            "Consulter le calendrier des événements de demain",
            "Imprimer la liste des événements",
            "Préparer les clés des salles de banquet nécessaires",
            "Placer le tout dans l'endroit désigné pour les banquets"
        ],
        "tips_fr": None,
        "system_used": "Lightspeed",
        "estimated_minutes": 10,
        "screenshots": []
    },
    {
        "order": 20,
        "title_fr": "Faire la distribution des pourboires journaliers.",
        "category": "part1",
        "description_fr": "Distribution des pourboires collectés aux employés concernés.",
        "steps": [
            "Récupérer les pourboires collectés pendant la journée",
            "Consulter la liste de distribution",
            "Répartir selon les pourcentages établis",
            "Placer dans les enveloppes individuelles",
            "Ranger dans les casiers des employés ou l'endroit désigné"
        ],
        "tips_fr": "Suivre strictement la politique de distribution de l'hôtel.",
        "system_used": None,
        "estimated_minutes": 10,
        "screenshots": []
    },
    {
        "order": 21,
        "title_fr": "Toujours connecter sur GXP; vérifier Cases/Chats.",
        "category": "part1",
        "description_fr": "Vérification des demandes clients via le système GXP.",
        "steps": [
            "S'assurer d'être connecté sur Empower/GXP",
            "Vérifier la section 'Cases' pour les demandes en attente",
            "Vérifier les 'Chats' pour les messages clients",
            "Traiter les demandes urgentes immédiatement",
            "Marquer les cases résolues comme complétées"
        ],
        "tips_fr": "GXP doit être vérifié régulièrement tout au long de la nuit, pas seulement une fois.",
        "system_used": "GXP",
        "estimated_minutes": 5,
        "screenshots": []
    },
    {
        "order": 22,
        "title_fr": "Vérifier si l'auditeur du BACK a besoin d'aide.",
        "category": "part1",
        "description_fr": "Coordination avec l'auditeur back-office.",
        "steps": [
            "Aller voir l'auditeur du BACK",
            "Demander s'il a besoin d'assistance",
            "Offrir de l'aide pour les tâches qu'il peut déléguer"
        ],
        "tips_fr": "Le travail d'équipe est essentiel pour une nuit efficace.",
        "system_used": None,
        "estimated_minutes": 2,
        "screenshots": []
    },

    # ============= PART 2 & 3 (23-35) =============
    {
        "order": 23,
        "title_fr": "Fermer sa caisse et remettre à l'auditeur du BACK.",
        "category": "part2",
        "description_fr": "Clôture de la caisse du front desk.",
        "steps": [
            "Compter tout l'argent dans votre tiroir-caisse",
            "Remplir la feuille de fermeture de caisse",
            "Vérifier que le total correspond au système",
            "Placer l'argent et le rapport dans l'enveloppe de dépôt",
            "Remettre à l'auditeur du BACK"
        ],
        "tips_fr": "Compter l'argent deux fois pour éviter les erreurs.",
        "system_used": "Lightspeed",
        "estimated_minutes": 15,
        "screenshots": []
    },
    {
        "order": 24,
        "title_fr": "Ajuster le Folio Internet + vérifier les folios avec des charges (ajuster tarif @4,95 $ par jour au besoin).",
        "category": "part2",
        "description_fr": "Ajustement des frais Internet sur les folios.",
        "steps": [
            "Rechercher les folios avec des charges Internet",
            "Vérifier le tarif appliqué",
            "Si différent de 4,95$/jour, faire l'ajustement",
            "Documenter les ajustements effectués"
        ],
        "tips_fr": "Le tarif standard Internet est de 4,95$ par jour.",
        "system_used": "Lightspeed",
        "estimated_minutes": 10,
        "screenshots": []
    },
    {
        "order": 25,
        "title_fr": "Faire la tournée des étages. (Prendre un RELAY).",
        "category": "part2",
        "description_fr": "Tournée de sécurité de tous les étages de l'hôtel.",
        "steps": [
            "Prendre un appareil RELAY (radio)",
            "Prendre la feuille de tournée imprimée plus tôt",
            "Commencer par le dernier étage et descendre",
            "Vérifier les corridors, escaliers et issues de secours",
            "Noter toute anomalie sur la feuille",
            "Vérifier les aires communes (piscine, gym, etc.)",
            "Retourner à la réception et remettre la feuille complétée"
        ],
        "tips_fr": "Garder le RELAY allumé et à portée en tout temps. Signaler immédiatement toute situation suspecte.",
        "system_used": "RELAY",
        "estimated_minutes": 30,
        "screenshots": []
    },
    {
        "order": 26,
        "title_fr": "Débuter le PART 2 (Post Room and Tax) à la demande de l'auditeur du BACK.",
        "category": "part2",
        "description_fr": "Lancement de la deuxième partie de l'audit. ATTENDRE l'instruction de l'auditeur du BACK.",
        "steps": [
            "ATTENDRE que l'auditeur du BACK vous donne le feu vert",
            "Dans Lightspeed, aller au menu 'Night Audit'",
            "Sélectionner 'PART 2 - Post Room and Tax'",
            "Cliquer sur 'Run' ou 'Exécuter'",
            "Attendre la fin du processus"
        ],
        "tips_fr": "NE JAMAIS lancer PART 2 sans l'autorisation de l'auditeur du BACK. Cela peut causer des erreurs graves.",
        "system_used": "Lightspeed",
        "estimated_minutes": 20,
        "screenshots": ["lightspeed_part2.png"]
    },
    {
        "order": 27,
        "title_fr": "Poursuivre le PART 3 lorsque Lightspeed s'éteint.",
        "category": "part2",
        "description_fr": "Le système s'éteint automatiquement entre les parties. Relancer PART 3.",
        "steps": [
            "Attendre que Lightspeed se ferme automatiquement après PART 2",
            "Se reconnecter à Lightspeed",
            "Aller au menu 'Night Audit'",
            "Sélectionner 'PART 3'",
            "Exécuter et attendre la fin du processus"
        ],
        "tips_fr": "C'est normal que le système s'éteigne. Ne pas s'inquiéter.",
        "system_used": "Lightspeed",
        "estimated_minutes": 15,
        "screenshots": []
    },
    {
        "order": 28,
        "title_fr": "Séparer les rapports et les distribuer aux départements concernés.",
        "category": "part2",
        "description_fr": "Organisation et distribution des rapports générés par l'audit.",
        "steps": [
            "Récupérer tous les rapports imprimés",
            "Trier par département (Restaurant, DBRS, Réception, etc.)",
            "Placer chaque pile dans l'endroit désigné",
            "Vérifier que rien n'est oublié"
        ],
        "tips_fr": None,
        "system_used": None,
        "estimated_minutes": 10,
        "screenshots": []
    },
    {
        "order": 29,
        "title_fr": "Imprimer No Post Report (pile du Restaurant).",
        "category": "part2",
        "description_fr": "Rapport des chambres sans permission de poster des charges.",
        "steps": [
            "Dans Lightspeed, aller à Reports",
            "Sélectionner 'No Post Report'",
            "Imprimer",
            "Placer dans la pile du Restaurant"
        ],
        "tips_fr": None,
        "system_used": "Lightspeed",
        "estimated_minutes": 2,
        "screenshots": []
    },
    {
        "order": 30,
        "title_fr": "Imprimer Guest List – Charge All (pile du Restaurant).",
        "category": "part2",
        "description_fr": "Liste des clients pouvant charger à leur chambre.",
        "steps": [
            "Dans Lightspeed, aller à Reports > Guest Lists",
            "Sélectionner 'Charge All'",
            "Imprimer",
            "Placer dans la pile du Restaurant"
        ],
        "tips_fr": None,
        "system_used": "Lightspeed",
        "estimated_minutes": 2,
        "screenshots": []
    },
    {
        "order": 31,
        "title_fr": "Imprimer Rapport Allotment (pile du DBRS).",
        "category": "part2",
        "description_fr": "Rapport des allotements de chambres.",
        "steps": [
            "Dans Lightspeed, aller à Reports",
            "Sélectionner 'Allotment Report'",
            "Imprimer",
            "Placer dans la pile du DBRS"
        ],
        "tips_fr": None,
        "system_used": "Lightspeed",
        "estimated_minutes": 2,
        "screenshots": []
    },
    {
        "order": 32,
        "title_fr": "Imprimer Rapport Inhouse avec spécial service G4 (3× pour piles DBRS, Auditeurs et Restaurant).",
        "category": "part2",
        "description_fr": "Rapport des clients en maison avec service spécial G4.",
        "steps": [
            "Dans Lightspeed, aller à Reports > Inhouse",
            "Filtrer par 'Special Service G4'",
            "Imprimer 3 copies",
            "Distribuer: 1 au DBRS, 1 aux Auditeurs, 1 au Restaurant"
        ],
        "tips_fr": None,
        "system_used": "Lightspeed",
        "estimated_minutes": 3,
        "screenshots": []
    },
    {
        "order": 33,
        "title_fr": "Imprimer Rapport Inhouse avec spécial service G4 + CL (2× pour piles Superviseur Réception & Restaurant).",
        "category": "part2",
        "description_fr": "Rapport des clients avec service G4 et CL.",
        "steps": [
            "Dans Lightspeed, aller à Reports > Inhouse",
            "Filtrer par 'Special Service G4 + CL'",
            "Imprimer 2 copies",
            "Distribuer: 1 au Superviseur Réception, 1 au Restaurant"
        ],
        "tips_fr": None,
        "system_used": "Lightspeed",
        "estimated_minutes": 3,
        "screenshots": []
    },
    {
        "order": 34,
        "title_fr": "Prendre les 5 copies du High Balance et faire les vérifications / inscrire les notes sur chaque feuille (pigeonnier de M. Pazi, M. Meunier, Roula, séparateur daté, & pile Superviseur Réception).",
        "category": "part2",
        "description_fr": "Rapport des clients avec solde élevé. Requiert vérification et notes.",
        "steps": [
            "Prendre le rapport High Balance (5 copies)",
            "Pour chaque client listé, vérifier le folio",
            "Noter sur chaque copie les informations pertinentes",
            "Distribuer aux 5 destinataires: M. Pazi, M. Meunier, Roula, séparateur daté, Superviseur Réception"
        ],
        "tips_fr": "Les clients à solde élevé doivent être suivis de près pour éviter les départs sans paiement.",
        "system_used": "Lightspeed",
        "estimated_minutes": 15,
        "screenshots": []
    },
    {
        "order": 35,
        "title_fr": "Faire les check-outs des départs après Part 2.",
        "category": "part2",
        "description_fr": "Traitement des départs tôt le matin.",
        "steps": [
            "Vérifier les départs prévus pour tôt le matin",
            "Quand un client se présente, vérifier son folio",
            "S'assurer que le solde est à zéro ou collecter le paiement",
            "Procéder au check-out dans Lightspeed",
            "Remettre la facture au client"
        ],
        "tips_fr": None,
        "system_used": "Lightspeed",
        "estimated_minutes": 30,
        "screenshots": []
    },

    # ============= END OF SHIFT (36-46) =============
    {
        "order": 36,
        "title_fr": "Envoyer les Plug in par courriel avant 5h30 à la Gouvernante, Maintenance, SAC et Directrice de Réception.",
        "category": "end_shift",
        "description_fr": "Envoi des rapports Plug in aux départements concernés.",
        "steps": [
            "Préparer le rapport Plug in",
            "Ouvrir votre client courriel",
            "Créer un nouveau message",
            "Ajouter les destinataires: Gouvernante, Maintenance, SAC, Directrice de Réception",
            "Joindre le rapport",
            "Envoyer AVANT 5h30"
        ],
        "tips_fr": "IMPORTANT: Cet envoi doit être fait AVANT 5h30 pour que les équipes du matin aient l'information.",
        "system_used": "Courriel",
        "estimated_minutes": 5,
        "screenshots": []
    },
    {
        "order": 37,
        "title_fr": "Faire la fermeture/facturation de la machine de vin (lounge) après 5h30.",
        "category": "end_shift",
        "description_fr": "Clôture de la machine à vin du lounge.",
        "steps": [
            "ATTENDRE après 5h30",
            "Se rendre au lounge",
            "Accéder au menu de fermeture de la machine à vin",
            "Imprimer le rapport de fermeture",
            "Remettre le rapport à la comptabilité"
        ],
        "tips_fr": "Ne pas faire cette tâche avant 5h30.",
        "system_used": "Machine à vin",
        "estimated_minutes": 10,
        "screenshots": []
    },
    {
        "order": 38,
        "title_fr": "Faire la facturation + prendre paiements de no show. Faire les feuilles d'ajustements. Remettre au bureau SAC.",
        "category": "end_shift",
        "description_fr": "Traitement des no-shows et ajustements.",
        "steps": [
            "Identifier les réservations no-show de la nuit",
            "Facturer selon la politique (généralement 1 nuit)",
            "Tenter de prendre le paiement sur la carte en dossier",
            "Si échec, documenter sur la feuille d'ajustements",
            "Remettre tous les documents au bureau SAC"
        ],
        "tips_fr": "Suivre strictement la politique de no-show de l'hôtel.",
        "system_used": "Lightspeed",
        "estimated_minutes": 20,
        "screenshots": []
    },
    {
        "order": 39,
        "title_fr": "Imprimer RESDO jusqu'au 27 FEV 2027 × copies (pigeonnier M. Pazi, M. Dacosta, M. Meunier, Mélanie, Jérome, Cuisine, Ventes, & pile Superviseur Réception, pile Restaurant).",
        "category": "end_shift",
        "description_fr": "Impression et distribution du rapport RESDO.",
        "steps": [
            "Dans Lightspeed, générer le rapport RESDO",
            "Paramétrer la date jusqu'au 27 FEV 2027",
            "Imprimer le nombre de copies nécessaire",
            "Distribuer aux destinataires: M. Pazi, M. Dacosta, M. Meunier, Mélanie, Jérome, Cuisine, Ventes, Superviseur Réception, Restaurant"
        ],
        "tips_fr": None,
        "system_used": "Lightspeed",
        "estimated_minutes": 10,
        "screenshots": []
    },
    {
        "order": 40,
        "title_fr": "Vérifier les réservations de groupe « No-show » et « Reinstate » qui font partie d'une RL.",
        "category": "end_shift",
        "description_fr": "Gestion des réservations de groupe non honorées.",
        "steps": [
            "Consulter la liste des groupes avec réservations liées (RL)",
            "Identifier les chambres no-show",
            "Vérifier si elles doivent être réinstallées (reinstate)",
            "Traiter selon les instructions du contrat de groupe"
        ],
        "tips_fr": "Les groupes ont souvent des politiques de no-show différentes des réservations individuelles.",
        "system_used": "Lightspeed",
        "estimated_minutes": 10,
        "screenshots": []
    },
    {
        "order": 41,
        "title_fr": "Placer les journaux à la SPESA et au Lounge. Retirer les anciens et conserver la 1re page du Journal de MTL.",
        "category": "end_shift",
        "description_fr": "Distribution des journaux du matin.",
        "steps": [
            "Récupérer les journaux livrés",
            "Retirer les journaux de la veille de la SPESA et du Lounge",
            "Conserver la première page du Journal de Montréal (archives)",
            "Placer les nouveaux journaux",
            "Jeter ou recycler les anciens journaux"
        ],
        "tips_fr": None,
        "system_used": None,
        "estimated_minutes": 5,
        "screenshots": []
    },
    {
        "order": 42,
        "title_fr": "À 6h00, ouvrir les lumières de la réception et ajuster le volume de la musique.",
        "category": "end_shift",
        "description_fr": "Préparation de la réception pour le quart du matin.",
        "steps": [
            "À 6h00 précises, allumer les lumières principales de la réception",
            "Ajuster le volume de la musique d'ambiance",
            "Vérifier que l'éclairage est adéquat pour accueillir les clients"
        ],
        "tips_fr": "Cette tâche marque le début de la transition vers le quart du matin.",
        "system_used": None,
        "estimated_minutes": 2,
        "screenshots": []
    },
    {
        "order": 43,
        "title_fr": "Envoyer le courriel des expected arrivals à Stéphanie Lefebvre.",
        "category": "end_shift",
        "description_fr": "Rapport des arrivées prévues pour le jour.",
        "steps": [
            "Générer le rapport des arrivées prévues pour aujourd'hui",
            "Ouvrir votre client courriel",
            "Créer un nouveau message à Stéphanie Lefebvre",
            "Joindre le rapport",
            "Envoyer"
        ],
        "tips_fr": None,
        "system_used": "Lightspeed, Courriel",
        "estimated_minutes": 5,
        "screenshots": []
    },
    {
        "order": 44,
        "title_fr": "Envoyer le courriel de fin de quart (complet avec caisse, informations importantes, etc.).",
        "category": "end_shift",
        "description_fr": "Résumé complet de la nuit envoyé à la direction.",
        "steps": [
            "Compiler toutes les informations importantes de la nuit",
            "Inclure le résumé de la caisse",
            "Noter tous les incidents ou situations particulières",
            "Lister les suivis nécessaires pour le quart du matin",
            "Envoyer le courriel aux destinataires habituels"
        ],
        "tips_fr": "Ce courriel est très important. Prenez le temps de bien le rédiger.",
        "system_used": "Courriel",
        "estimated_minutes": 10,
        "screenshots": []
    },
    {
        "order": 45,
        "title_fr": "Aller porter les papiers aux bureaux de l'administration. S.V.P. demander du papier pour la réception si nécessaire.",
        "category": "end_shift",
        "description_fr": "Distribution finale des documents et réapprovisionnement.",
        "steps": [
            "Rassembler tous les documents à remettre à l'administration",
            "Se rendre aux bureaux de l'administration",
            "Déposer les documents aux endroits appropriés",
            "Si le stock de papier est bas, en demander"
        ],
        "tips_fr": None,
        "system_used": None,
        "estimated_minutes": 5,
        "screenshots": []
    },
    {
        "order": 46,
        "title_fr": "Nettoyer votre espace de travail, faire les messages nécessaires au quart du matin.",
        "category": "end_shift",
        "description_fr": "Clôture du quart et passation au matin.",
        "steps": [
            "Ranger tous les documents et fournitures",
            "Nettoyer le comptoir et votre espace de travail",
            "Écrire les messages importants pour le quart du matin",
            "Vérifier que tout est prêt pour la passation"
        ],
        "tips_fr": "Laissez l'espace de travail propre et organisé pour vos collègues du matin.",
        "system_used": None,
        "estimated_minutes": 5,
        "screenshots": []
    },
]


def seed_tasks():
    app = create_app()
    with app.app_context():
        # Clear existing tasks
        Task.query.delete()

        # Add all tasks with detailed instructions
        for task_data in TASKS_DETAILED:
            task = Task(
                order=task_data["order"],
                title_fr=task_data["title_fr"],
                category=task_data["category"],
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
        print(f"Seeded {len(TASKS_DETAILED)} tasks with detailed instructions!")


if __name__ == '__main__':
    seed_tasks()
