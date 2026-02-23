"""
Front Desk Night Audit Tasks - Detailed Task List
Sheraton Laval - Night Audit WebApp

This module defines the complete task list for front desk night audit employees.
Each task contains French instructions, estimated time, and system requirements.

Generated from:
- sheraton_laval_night_audit_checklist.md
- manual_audit_nuit_front.md
"""

TASKS_DETAILED = [
    # ================== MISE EN PLACE (Setup) ==================
    {
        "order": 1,
        "title_fr": "Échange d'informations avec le quart du soir",
        "category": "mise_en_place",
        "description_fr": "Discuter avec l'équipe du soir des arrivées restantes, situations clients, groupes spéciaux et toute information importante pour la nuit.",
        "steps": [
            "Arriver 15 minutes avant l'heure de début du quart",
            "Vérifier le livre de réception pour les notes du quart du soir",
            "Discuter avec le chef de réception ou superviseur du soir des clients VIP ou situations spéciales",
            "Vérifier les arrivées prévues pour le reste de la nuit",
            "Prendre note des groupes en house et de leurs horaires d'événements"
        ],
        "screenshots": [],
        "tips_fr": "C'est la source d'information la plus fiable. Posez des questions si quelque chose n'est pas clair.",
        "system_used": "Manuel",
        "estimated_minutes": 15
    },
    {
        "order": 2,
        "title_fr": "Vérifier le panneau incendie et se mettre en alarme",
        "category": "mise_en_place",
        "description_fr": "Vérifier l'état du panneau incendie à gauche de la réception et se mettre en alarme pour retirer les dérivations au besoin.",
        "steps": [
            "Localiser le panneau incendie à gauche de la réception",
            "Vérifier l'écran du panneau pour voir l'état de tous les capteurs",
            "Se mettre en alarme si nécessaire",
            "Retirer les dérivations de test si présentes",
            "Vérifier que tous les capteurs sont actifs"
        ],
        "screenshots": [],
        "tips_fr": "Les dérivations peuvent être laissées par le quart du jour lors de travaux d'entretien.",
        "system_used": "Manuel",
        "estimated_minutes": 5
    },
    {
        "order": 3,
        "title_fr": "Se connecter aux systèmes (Lightspeed, Empower/GXP, Control Panel)",
        "category": "mise_en_place",
        "description_fr": "Se connecter sur Galaxy Lightspeed (PMS), Empower/GXP et Control Panel pour clés mobiles.",
        "steps": [
            "Ouvrir Lightspeed (Galaxy) sur le PC de la réception",
            "Entrer les identifiants d'auditeur de nuit",
            "Ouvrir Empower/GXP (système de communication)",
            "Vérifier la connexion au Control Panel pour les clés mobiles",
            "S'assurer que tous les systèmes sont pleinement opérationnels"
        ],
        "screenshots": ["image1.jpeg"],
        "tips_fr": "Vérifier que les connexions sont stables avant de continuer.",
        "system_used": "Lightspeed, Empower/GXP, Mobile Key Control Panel",
        "estimated_minutes": 10
    },
    {
        "order": 4,
        "title_fr": "Faire les questions du jour sur DLZ",
        "category": "mise_en_place",
        "description_fr": "Consulter et répondre aux questions du jour sur le système DLZ (Daily Live Zone).",
        "steps": [
            "Ouvrir le système DLZ",
            "Vérifier les questions pendantes du jour",
            "Répondre à toutes les questions appropriées",
            "Marquer les questions comme complétées",
            "Mettre à jour les informations requises"
        ],
        "screenshots": [],
        "tips_fr": "Les questions DLZ doivent être traitées tôt dans la nuit.",
        "system_used": "DLZ",
        "estimated_minutes": 10
    },
    {
        "order": 5,
        "title_fr": "Remplir les imprimantes de papier et vérifier l'encre",
        "category": "mise_en_place",
        "description_fr": "Remplir les imprimantes de papier et vérifier que l'encre est adéquate pour toutes les impressions de la nuit.",
        "steps": [
            "Vérifier les niveaux de papier dans les imprimantes",
            "Ajouter du papier si nécessaire (réserve au bureau Administration)",
            "Vérifier le niveau d'encre/toner",
            "Remplacer les cartouches si nécessaire",
            "Faire un test d'impression pour vérifier la qualité"
        ],
        "screenshots": [],
        "tips_fr": "La réserve de papier et d'encre se trouve au bureau Administration en bas.",
        "system_used": "Manuel",
        "estimated_minutes": 10
    },
    {
        "order": 6,
        "title_fr": "Vérifier les wake-up calls",
        "category": "mise_en_place",
        "description_fr": "Vérifier les wake-up calls (Cahier de réception vs Espresso) et faire les ajouts au besoin.",
        "steps": [
            "Consulter le cahier de réception pour les wake-up calls demandés",
            "Vérifier la correspondance avec le système Espresso",
            "Pour chaque appel manquant, utiliser le téléphone à droite",
            "Appuyer sur la touche 'Réveil'",
            "Entrer le numéro de chambre + # + heure (ex. 630 pour 6h30) + AM/PM",
            "Vérifier que tous les appels sont enregistrés"
        ],
        "screenshots": ["image1.jpeg"],
        "tips_fr": "Les clients peuvent demander des appels jusqu'à minuit. Vérifiez régulièrement.",
        "system_used": "Espresso, Manuel",
        "estimated_minutes": 15
    },

    # ================== PRE-AUDIT (Avant l'audit - Impressions et rapports) ==================
    {
        "order": 7,
        "title_fr": "Imprimer le séparateur daté",
        "category": "pre_audit",
        "description_fr": "Imprimer et préparer le séparateur daté dans Word pour recevoir les documents comptables.",
        "steps": [
            "Ouvrir Word sur le poste gauche (User: Auditeur, MDP: Green176)",
            "Localiser le fichier 'Séparateur daté'",
            "Changer la date du jour",
            "Mettre à jour le jour de la semaine",
            "Imprimer une copie",
            "Plier en 2 et poser à gauche de l'écran"
        ],
        "screenshots": [],
        "tips_fr": "Le séparateur doit être visible et accessible pour recevoir les documents au fur et à mesure.",
        "system_used": "Word",
        "estimated_minutes": 5
    },
    {
        "order": 8,
        "title_fr": "Imprimer la feuille de tournée des étages",
        "category": "pre_audit",
        "description_fr": "Imprimer la feuille de tournée (Excel) avec la date du jour et signer.",
        "steps": [
            "Ouvrir le fichier Excel 'Feuille de tournée'",
            "Changer la date au jour actuel",
            "Imprimer une copie",
            "Signer la feuille avec votre nom",
            "Déposer à l'extrême droite du comptoir pour l'équipe du matin"
        ],
        "screenshots": [],
        "tips_fr": "Cette feuille servira à la tournée des étages plus tard dans la nuit.",
        "system_used": "Excel",
        "estimated_minutes": 5
    },
    {
        "order": 9,
        "title_fr": "Imprimer la feuille de déneigement avec capture météo",
        "category": "pre_audit",
        "description_fr": "Préparer la feuille d'entretien et météo avec les prévisions pour les 4 prochains jours.",
        "steps": [
            "Ouvrir MétéoMédia pour Laval via Chrome",
            "Consulter les prévisions pour les 4 prochains jours",
            "Prendre 2 captures d'écran (2 jours par 2 jours) avec Snipping Tool",
            "Ouvrir le fichier Word 'Feuille d'entretien'",
            "Clic droit sur l'image existante, 'Change Picture' → 'From Clipboard'",
            "Imprimer en recto-verso",
            "Déposer à l'extrême droite du comptoir"
        ],
        "screenshots": ["weather_example.png"],
        "tips_fr": "L'impression en recto-verso économise le papier et rend le document plus compact.",
        "system_used": "Word, Chrome, Snipping Tool",
        "estimated_minutes": 10
    },
    {
        "order": 10,
        "title_fr": "Run PART 1 – Pre Audit Reports",
        "category": "pre_audit",
        "description_fr": "Exécuter le rapport de pré-audit (PART 1) pour générer tous les rapports préalables.",
        "steps": [
            "Vérifier qu'il n'y a plus d'arrivées en attente dans Lightspeed",
            "Cliquer sur l'icône de lune (Night Audit)",
            "Sélectionner 'Run Pre-Audit'",
            "Attendre la génération des rapports",
            "Aller chercher les impressions au bureau Administration (code 3514#)",
            "Organiser les rapports sur le bureau"
        ],
        "screenshots": ["image2.png", "image3.png"],
        "tips_fr": "Assurez-vous que toutes les arrivées sont complétées avant de lancer PART 1.",
        "system_used": "Lightspeed",
        "estimated_minutes": 15
    },
    {
        "order": 11,
        "title_fr": "Ajouter folios à zéro (petits soldes)",
        "category": "pre_audit",
        "description_fr": "Vérifier l'Actual Departure Report et ajouter folios à zéro pour les soldes ±1$.",
        "steps": [
            "Prendre le rapport 'Actual Departure Report'",
            "Identifier les chambres avec solde entre -1$ et +1$",
            "Pour chaque chambre : Lightspeed → Modify → Cashiering → Post",
            "Si positif (noir) : Dept 40 / Sub 60",
            "Si négatif (rouge) : Dept 40 / Sub 10",
            "Entrer Ref 'CLOSE', Note '1'",
            "Cliquer 'Add to List' puis 'Post' (solde = 0)",
            "Agrafer le rapport et placer dans le séparateur daté"
        ],
        "screenshots": [],
        "tips_fr": "Cela nettoie les petites erreurs d'arrondi qui peuvent causer des problèmes au back.",
        "system_used": "Lightspeed",
        "estimated_minutes": 20
    },
    {
        "order": 12,
        "title_fr": "Imprimer Guest List Delegates pour les groupes",
        "category": "pre_audit",
        "description_fr": "Générer et imprimer la liste des délégués de groupe pour les réservations groupes.",
        "steps": [
            "Ouvrir Lightspeed → Reports → In-House List",
            "Sélectionner 'Group Delegate Guests'",
            "Activer 'Page break ON' et 'Room rates YES'",
            "Trier par Group Code / Room Number",
            "Soumettre et imprimer",
            "Agrafer le rapport",
            "Placer dans la chemise bleue datée (tiroir arrière)"
        ],
        "screenshots": ["image4.png"],
        "tips_fr": "Cette liste aide à l'organisation des événements de groupe le lendemain.",
        "system_used": "Lightspeed",
        "estimated_minutes": 10
    },
    {
        "order": 13,
        "title_fr": "Imprimer Guest List Delegates pour les Wholesalers",
        "category": "pre_audit",
        "description_fr": "Générer et imprimer la liste des délégués pour les réservations wholesalers.",
        "steps": [
            "Ouvrir Lightspeed → Reports → In-House List",
            "Sélectionner 'Wholesaler Delegates'",
            "Sélectionner 'Tour Code ALL'",
            "Trier par Room Number",
            "Soumettre et imprimer",
            "Agrafer le rapport",
            "Placer dans la chemise bleue datée (tiroir arrière)"
        ],
        "screenshots": ["image5.png"],
        "tips_fr": "Les wholesalers ont des procédures spéciales de check-out.",
        "system_used": "Lightspeed",
        "estimated_minutes": 10
    },
    {
        "order": 14,
        "title_fr": "Préparer feuille de contrôle pour FedEx, Cargojet et UPS",
        "category": "pre_audit",
        "description_fr": "Préparer les 3 feuilles de contrôle pilotes (FedEx, Cargo Jet, UPS) pour le lendemain. Consulter le cahier de réception pour les chambres assignées aux équipages. Les 3 feuilles sont agrafées ensemble.",
        "steps": [
            "Consulter le cahier de réception pour relever les chambres des équipages pilotes",
            "Vérifier dans Lightspeed les noms associés aux chambres si nécessaire",
            "FedEx : utiliser le générateur ci-dessous ou ouvrir Excel 'FEDEX room records' → entrer noms, # employé, vol et chambres",
            "Cargo Jet : utiliser le générateur ci-dessous ou ouvrir Excel 'CARGO JET' → entrer noms et chambres",
            "UPS : Chrome → Favori 'UPS Plugin' → Home → Login → Sign in sheet → View and Print → Remplir la date du lendemain",
            "Imprimer les 3 feuilles",
            "Agrafer les 3 feuilles ensemble, plier en 3",
            "Placer dans le bac des réceptionnistes"
        ],
        "screenshots": ["image14.png"],
        "tips_fr": "Les pilotes viennent chercher ces feuilles le matin pour savoir quelles chambres visiter.",
        "system_used": "Excel, Chrome, UPS Plugin",
        "estimated_minutes": 20
    },
    {
        "order": 15,
        "title_fr": "Imprimer Room Status Details pour la gouvernante",
        "category": "pre_audit",
        "description_fr": "Imprimer le rapport Room Status Details pour l'équipe de gouvernante.",
        "steps": [
            "Ouvrir Lightspeed → Reports → Room Status Details",
            "Sélectionner 'All rooms', 'All status'",
            "Trier par Room Number",
            "Imprimer le rapport",
            "Photocopier les 3 pages du logbook",
            "Agrafer les copies sur le rapport Room Status",
            "Déposer à l'arrière (étagère sur les caisses) pour la gouvernante"
        ],
        "screenshots": ["image6.png"],
        "tips_fr": "La gouvernante a besoin de ce rapport pour organiser le travail de nettoyage.",
        "system_used": "Lightspeed",
        "estimated_minutes": 15
    },
    {
        "order": 16,
        "title_fr": "Photocopier changements de chambre et feuille des travaux",
        "category": "pre_audit",
        "description_fr": "Préparer les copies des changements de chambre et de la feuille des travaux pour la gouvernante.",
        "steps": [
            "Identifier les changements de chambre du jour",
            "Photocopier les formulaires de changement",
            "Localiser la feuille des travaux en cours",
            "Photocopier la feuille",
            "Agrafer les deux documents",
            "Placer dans la pile gouvernante avec le Room Status Details"
        ],
        "screenshots": [],
        "tips_fr": "Ces documents doivent être accompagnés du Room Status Details.",
        "system_used": "Manuel",
        "estimated_minutes": 10
    },

    # ================== PRE_AUDIT - Finances et folios ==================
    {
        "order": 17,
        "title_fr": "Vérifier le folio Amérispa et régler les charges",
        "category": "pre_audit",
        "description_fr": "Vérifier le folio Amérispa (AR 22866). Si des charges sont présentes, prendre le paiement en Facture Directe (DB) via Cashiering → Settle.",
        "steps": [
            "Ouvrir Lightspeed → Cashiering",
            "Rechercher le folio Amérispa (AR 22866)",
            "Vérifier si des charges sont présentes sur le folio",
            "Si charges : cliquer 'Settle' sur le folio",
            "Sélectionner le type de paiement 'DB - Facture Directe'",
            "Cliquer 'Apply' pour régler le solde",
            "Vérifier que le solde est à 0.00$",
            "Imprimer le folio et placer dans le séparateur daté"
        ],
        "screenshots": ["image7.png", "image11.png"],
        "tips_fr": "Le folio Amérispa doit être réglé en Facture Directe (DB) chaque nuit. Vérifiez que le solde est bien à 0$.",
        "system_used": "Lightspeed",
        "estimated_minutes": 15
    },
    {
        "order": 18,
        "title_fr": "Compléter contrats banquets",
        "category": "pre_audit",
        "description_fr": "Préparer les contrats des banquets en imprimant les folios et factures originales.",
        "steps": [
            "Identifier les événements banquet du jour",
            "Ouvrir Lightspeed → Cashiering → Groupe/RL",
            "Imprimer le folio de chaque groupe",
            "Aller au back et récupérer les factures originales POSitouch",
            "Photocopier les factures",
            "Agrafer 1 copie du folio + 1 copie des factures pour chaque contrat",
            "Placer dans le séparateur daté"
        ],
        "screenshots": [],
        "tips_fr": "Les contrats complétés doivent inclure le folio et les reçus.",
        "system_used": "Lightspeed, POSitouch",
        "estimated_minutes": 20
    },
    {
        "order": 19,
        "title_fr": "Préparer clés et liste banquets pour événements de demain",
        "category": "pre_audit",
        "description_fr": "Préparer les clés banquets et liste des délégués pour les événements du lendemain.",
        "steps": [
            "Ouvrir le gros cartable sous l'ordi de droite",
            "Relever les événements prévus pour demain",
            "Ouvrir Word 'Copie clef banquet'",
            "Remplir : affichage, salle, horaire (départ/fin), contact",
            "Imprimer la copie de clef",
            "Préparer les clés correspondantes",
            "Placer avec les feuilles pilotes"
        ],
        "screenshots": ["image10.png"],
        "tips_fr": "Les clés doivent être prêtes avant le début des événements.",
        "system_used": "Word, Manuel",
        "estimated_minutes": 15
    },

    # ================== TIPS (Pourboires) ==================
    {
        "order": 20,
        "title_fr": "Faire la distribution des pourboires journaliers",
        "category": "tips",
        "description_fr": "Distribuer les pourboires accumulés durant la journée selon la procédure établie. Utiliser l'outil Pourboires de l'application web pour saisir et générer les fichiers POD.",
        "steps": [
            "Récupérer les feuilles individuelles auprès du back audit",
            "Ouvrir l'outil 'Pourboires' dans l'application web (menu latéral → Pourboires)",
            "Déposer le fichier POD Excel de la période courante (ou charger le dernier fichier actif)",
            "Utiliser l'entrée rapide : entrer un montant de ventes → le pourboire (10%) se calcule automatiquement",
            "Sélectionner les serveurs qui ont le même montant pour les remplir en lot",
            "Vérifier : Total ventes back – (réception + Spesa) = total ventes POD",
            "Télécharger le fichier POD mis à jour",
            "Distribuer à chaque serveur selon les feuilles",
            "Agrafer la feuille POD derrière la feuille du back",
            "Placer dans le séparateur daté",
            "Pour générer un nouveau fichier pour la prochaine période : cliquer 'Nouvelle période' dans l'outil"
        ],
        "screenshots": [],
        "tips_fr": "L'outil web calcule automatiquement 10% de pourboire. L'entrée rapide permet d'appliquer le même montant à plusieurs serveurs d'un coup. Vérifiez deux fois avant distribution.",
        "system_used": "App Web / Excel",
        "estimated_minutes": 25
    },

    # ================== COORDINATION (milieu de nuit) ==================
    {
        "order": 21,
        "title_fr": "Se connecter sur GXP et vérifier les cases/chats",
        "category": "coordination",
        "description_fr": "Toujours se connecter sur GXP pour vérifier les cases et chats du soir.",
        "steps": [
            "Ouvrir Empower/GXP",
            "Se connecter avec les identifiants d'auditeur",
            "Consulter toutes les cases et messages",
            "Lire les chats importants du jour",
            "Répondre aux messages nécessaires",
            "Rester connecté pendant toute la nuit"
        ],
        "screenshots": [],
        "tips_fr": "GXP est le système de communication principal. Restez alerte pour les messages importants.",
        "system_used": "Empower/GXP",
        "estimated_minutes": 10
    },
    {
        "order": 22,
        "title_fr": "Vérifier si l'auditeur du back a besoin d'aide",
        "category": "coordination",
        "description_fr": "Vérifier périodiquement auprès de l'auditeur du back s'il a besoin d'aide.",
        "steps": [
            "Aller consulter l'auditeur du back régulièrement",
            "Demander s'il a besoin d'assistance pour des tâches",
            "Aider à récupérer les rapports",
            "Aider à préparer les piles de documents",
            "Rester disponible pour les besoins urgents"
        ],
        "screenshots": [],
        "tips_fr": "L'équipe du back est souvent surchargée. Un coup de main rapide peut accélérer tout le audit.",
        "system_used": "Manuel",
        "estimated_minutes": 10
    },
    {
        "order": 23,
        "title_fr": "Fermer sa caisse et remettre au back audit",
        "category": "coordination",
        "description_fr": "Fermer votre caisse de réception et remettre tous les documents au back audit.",
        "steps": [
            "Arrêter les transactions",
            "Compter le contenu de la caisse",
            "Préparer un résumé du tirage-caisse",
            "Créer un bilan de clôture",
            "Remettre tous les documents et l'argent au back audit",
            "Obtenir une confirmation de réception"
        ],
        "screenshots": [],
        "tips_fr": "La caisse doit être fermée correctement avant les rapports finaux.",
        "system_used": "Lightspeed",
        "estimated_minutes": 20
    },

    # ================== POST-AUDIT (Après l'audit) ==================
    {
        "order": 24,
        "title_fr": "Ajuster le folio Internet et vérifier les folios avec charges",
        "category": "post_audit",
        "description_fr": "Ajuster les tarifs Internet et vérifier tous les folios avec des charges.",
        "steps": [
            "Ouvrir Lightspeed → Cashier Detail → Dept 36, Sub 36.1",
            "Pour chaque chambre : vérifier le tarif Internet",
            "Standard : corriger à 4.95 / 0.52 / 0.25",
            "Elite/Pilote : gratuit (0$) → Transfer vers 'Marriott Internet'",
            "Sélectionner les 3 lignes et glisser vers Marriott Internet",
            "Non-membre : laisser sans changement",
            "Imprimer le rapport 36.1 final",
            "Imprimer le folio Marriott Internet et Settle à 0$",
            "Imprimer le rapport 36.5",
            "Agrafer les 3 rapports et donner au back"
        ],
        "screenshots": ["image8.png", "image9.png"],
        "tips_fr": "Les tarifs Internet doivent correspondre aux types de membres Marriott.",
        "system_used": "Lightspeed",
        "estimated_minutes": 30
    },
    {
        "order": 25,
        "title_fr": "Faire la tournée des étages",
        "category": "post_audit",
        "description_fr": "Faire la tournée complète des étages pour vérifier l'état des chambres et prendre un RELAY.",
        "steps": [
            "Prendre la feuille de tournée imprimée plus tôt",
            "Prendre un téléphone RELAY (portable de réception)",
            "Commencer par le 1er étage",
            "Vérifier l'état général des chambres",
            "Noter tout problème ou situation anormale",
            "Communiquer avec la gouvernante si besoin",
            "Revenir à la réception et mettre à jour les informations"
        ],
        "screenshots": [],
        "tips_fr": "La tournée permet de vérifier que tout est en ordre et d'identifier les problèmes rapidement.",
        "system_used": "Manuel, Téléphone RELAY",
        "estimated_minutes": 45
    },
    {
        "order": 26,
        "title_fr": "Débuter PART 2 à la demande du back audit",
        "category": "post_audit",
        "description_fr": "Lancer PART 2 (Post Room and Tax) quand demandé par l'auditeur du back.",
        "steps": [
            "Attendre la confirmation de l'auditeur du back",
            "Vérifier qu'il n'y a plus d'arrivées en attente",
            "Vérifier les no-shows avec dépôt : Modify > Paiement > Add Deposit",
            "Pour dépôt : montant HT × 1.19. Si refus : Cancel",
            "Ouvrir Lightspeed → Night Audit → Post Room and Tax",
            "Attendre la déconnexion (tous les systèmes se fermeront)",
            "Attendre la reconnexion automatique"
        ],
        "screenshots": ["image12.png"],
        "tips_fr": "PART 2 est critique. Assurez-vous que tout est prêt avant de lancer.",
        "system_used": "Lightspeed",
        "estimated_minutes": 15
    },
    {
        "order": 27,
        "title_fr": "Poursuivre PART 3 quand Lightspeed s'éteint",
        "category": "post_audit",
        "description_fr": "Lancer PART 3 (Run Audit) après reconnexion de Lightspeed.",
        "steps": [
            "Attendre la reconnexion de Lightspeed après PART 2",
            "Vérifier que tous les systèmes sont en ligne",
            "Ouvrir Lightspeed → Night Audit → Run Audit",
            "Attendre la fin du traitement (Lightspeed s'éteindra)",
            "Rester disponible en cas d'erreurs"
        ],
        "screenshots": ["image13.png"],
        "tips_fr": "PART 3 est le processus final d'audit. Ne pas interrompre une fois lancé.",
        "system_used": "Lightspeed",
        "estimated_minutes": 30
    },
    {
        "order": 28,
        "title_fr": "Séparer les rapports et distribuer aux départements",
        "category": "post_audit",
        "description_fr": "Séparer tous les rapports post-audit et les distribuer aux départements concernés.",
        "steps": [
            "Récupérer tous les rapports générés par PART 3",
            "Organiser les piles selon la distribution établie",
            "Pile Restaurant : à l'arrière du comptoir",
            "Pile DBRS : 2 copies (une pour auditeur, une pour pigeonnier)",
            "Pile Gouvernante : sur l'étagère à l'arrière",
            "Pile Superviseur : à la réception",
            "Vérifier que tout est bien organisé"
        ],
        "screenshots": ["image28.png"],
        "tips_fr": "Une bonne organisation des rapports accélère le travail du quart suivant.",
        "system_used": "Manuel",
        "estimated_minutes": 15
    },
    {
        "order": 29,
        "title_fr": "Imprimer No Post Report",
        "category": "post_audit",
        "description_fr": "Imprimer le rapport No Posting Allowed pour les clients avec des restrictions.",
        "steps": [
            "Ouvrir Lightspeed → Reports → No Posting Allowed",
            "Sélectionner : All guests / In-house / By room",
            "Imprimer le rapport",
            "Agrafer les pages",
            "Placer dans la pile Restaurant"
        ],
        "screenshots": [],
        "tips_fr": "Ce rapport est important pour que le restaurant sache qui ne peut pas être facturé.",
        "system_used": "Lightspeed",
        "estimated_minutes": 10
    },
    {
        "order": 30,
        "title_fr": "Imprimer Guest List – Charge All",
        "category": "post_audit",
        "description_fr": "Imprimer la liste des clients avec 'Charge All' pour le restaurant.",
        "steps": [
            "Ouvrir Lightspeed → Reports → Guest List – Charge All",
            "Sélectionner : Registered / No comments / Special Service CA / By room",
            "Imprimer le rapport",
            "Agrafer les pages",
            "Placer dans la pile Restaurant"
        ],
        "screenshots": ["image15.png"],
        "tips_fr": "Cette liste aide le restaurant à identifier les clients avec 'Charge All'.",
        "system_used": "Lightspeed",
        "estimated_minutes": 10
    },
    {
        "order": 31,
        "title_fr": "Imprimer Rapport Allotment",
        "category": "post_audit",
        "description_fr": "Imprimer le rapport Allotment Overview pour les réservations futures.",
        "steps": [
            "Ouvrir Lightspeed → Reports → Allotment Overview",
            "Sélectionner : Today → Today+49 jours",
            "Imprimer le rapport",
            "Agrafer les pages",
            "Placer dans la pile DBRS"
        ],
        "screenshots": ["image16.png"],
        "tips_fr": "Ce rapport aide à la planification des réservations futures.",
        "system_used": "Lightspeed",
        "estimated_minutes": 10
    },
    {
        "order": 32,
        "title_fr": "Imprimer In-House List G4 (3 copies)",
        "category": "post_audit",
        "description_fr": "Imprimer 3 copies du rapport In-House avec service spécial G4.",
        "steps": [
            "Ouvrir Lightspeed → Reports → In-House List",
            "Sélectionner : G4 / Sort by Room",
            "Imprimer 3 copies",
            "Agrafer chaque copie",
            "Distribuer : 1 à DBRS, 1 à Auditeur Back, 1 à Réception"
        ],
        "screenshots": ["image17.png"],
        "tips_fr": "Les 3 copies doivent être identiques et séparées pour les différents départements.",
        "system_used": "Lightspeed",
        "estimated_minutes": 10
    },
    {
        "order": 33,
        "title_fr": "Imprimer In-House List G4 + CL (2 copies)",
        "category": "post_audit",
        "description_fr": "Imprimer 2 copies du rapport In-House avec services spéciaux G4 et CL.",
        "steps": [
            "Ouvrir Lightspeed → Reports → In-House List",
            "Sélectionner : G4 + CL / Sort by Room",
            "Imprimer 2 copies",
            "Agrafer chaque copie",
            "Distribuer : 1 au Superviseur Réception, 1 au Restaurant"
        ],
        "screenshots": ["image18.png"],
        "tips_fr": "Ce rapport inclut les clients avec Concierge (CL).",
        "system_used": "Lightspeed",
        "estimated_minutes": 10
    },
    {
        "order": 34,
        "title_fr": "Traiter High Balance",
        "category": "post_audit",
        "description_fr": "Vérifier et traiter les folios avec soldes élevés (High Balance).",
        "steps": [
            "Identifier toutes les chambres avec High Balance",
            "Pour chaque chambre : Lightspeed → Cashiering → Settle",
            "Cliquer 'Apply' sur le solde",
            "Si client accepte : marquer 'OK' et imprimer folio",
            "Si client refuse : noter le folio",
            "Préparer 5 copies des High Balance pour les pigeonniers",
            "Distribuer : M. Pazi, M. Meunier, Roula, Séparateur daté, Superviseur Réception"
        ],
        "screenshots": ["image19.png"],
        "tips_fr": "Les High Balance doivent être vérifiés avant le checkout final.",
        "system_used": "Lightspeed",
        "estimated_minutes": 25
    },

    # ================== FIN DE QUART (après PART — ~05h-07h) ==================
    {
        "order": 35,
        "title_fr": "Effectuer les check-outs des départs après PART 2",
        "category": "fin_quart",
        "description_fr": "Traiter les check-outs des départs prévus après l'exécution de PART 2.",
        "steps": [
            "Obtenir la liste des départs après PART 2",
            "Pour chaque chambre : Lightspeed → Modify",
            "Mettre le solde à 0",
            "Effectuer le check-out",
            "Imprimer le folio final",
            "Vérifier que tout est complété"
        ],
        "screenshots": [],
        "tips_fr": "Les check-outs doivent être finalisés après PART 2.",
        "system_used": "Lightspeed",
        "estimated_minutes": 20
    },
    {
        "order": 36,
        "title_fr": "Envoyer les Plug-in par courriel avant 5h30",
        "category": "fin_quart",
        "description_fr": "Envoyer les informations Plug-in (pilotes) par courriel à gouvernante, maintenance, SAC et directrice de réception.",
        "steps": [
            "Identifier les pilotes (code CA*, FE*, UP*) dans les réservations",
            "Ouvrir Lightspeed → Quick Modify",
            "Sélectionner 'Registered' et chercher le Wholesaler Code",
            "Entrer le code du pilote",
            "Préparer un courriel Outlook avec :",
            "  - Nombre de chambres occupées par chaque pilote",
            "  - Heures de départ approximatives",
            "Envoyer avant 5h30 à :",
            "  - Gouvernante",
            "  - Maintenance",
            "  - SAC",
            "  - Directrice de Réception"
        ],
        "screenshots": ["image20.png"],
        "tips_fr": "Le timing est important : avant 5h30. Préparez le courriel d'avance.",
        "system_used": "Lightspeed, Outlook",
        "estimated_minutes": 15
    },
    {
        "order": 37,
        "title_fr": "Facturer la machine de vin (lounge) après 5h30",
        "category": "fin_quart",
        "description_fr": "Fermer et facturer les ventes de la machine de vin du lounge après 5h30.",
        "steps": [
            "Attendre après 5h30",
            "Ouvrir Enoclient",
            "Aller à Statistics → Reports → Yesterday & Today",
            "Cliquer 'Load'",
            "Imprimer le rapport (carré rouge)",
            "Ouvrir POSitouch (Piazza)",
            "Aller à Table 800 → Guest 1 → Divers → Vins Ouverts",
            "Entrer le montant et le nom du serveur",
            "Sélectionner 'Pay' → 'Room Charge'",
            "Agrafer les 3 tickets de caisse sur la feuille Enoclient",
            "Placer dans le panier de factures pour le back office"
        ],
        "screenshots": ["image21.png", "image22.png", "image23.png", "image24.png"],
        "tips_fr": "La machine de vin doit être facturée après 5h30, pas avant.",
        "system_used": "Enoclient, POSitouch",
        "estimated_minutes": 20
    },
    {
        "order": 38,
        "title_fr": "Facturer les no-shows et prendre les paiements",
        "category": "fin_quart",
        "description_fr": "Facturer les no-shows (Did Not Arrive), prendre les paiements et préparer les feuilles d'ajustements. Remettre au bureau SAC.",
        "steps": [
            "Identifier tous les no-shows du jour",
            "Pour chaque no-show : Lightspeed → Modify → Cashiering",
            "Poster Dept 1 / Sub 28",
            "Entrer le montant HT",
            "Ref : 'NO SHOW'",
            "Note : nom du client",
            "Imprimer le folio",
            "Créer une feuille d'ajustement (Excel)",
            "Agrafer l'ajustement devant, folio derrière",
            "Remettre au bureau SAC"
        ],
        "screenshots": ["image25.png", "image26.png"],
        "tips_fr": "Les no-shows doivent être facturés selon la politique de l'hôtel.",
        "system_used": "Lightspeed, Excel",
        "estimated_minutes": 30
    },
    {
        "order": 39,
        "title_fr": "Imprimer RESOB (7 copies pour pigeonniers)",
        "category": "fin_quart",
        "description_fr": "Imprimer les rapports RESOB (Reservations Overview Business) et distribuer aux 7 pigeonniers.",
        "steps": [
            "Ouvrir Lightspeed → Reports → RESOB",
            "Sélectionner la période : Today → date future",
            "Imprimer 7 copies",
            "Agrafer les pages de chaque copie",
            "Distribuer aux pigeonniers :",
            "  - M. Dacosta",
            "  - M. Meunier",
            "  - Jérome",
            "  - Cuisine",
            "  - Ventes",
            "  - Pile Superviseur Réception",
            "  - Pile Restaurant"
        ],
        "screenshots": ["image27.png"],
        "tips_fr": "RESOB montre les réservations futures. Pazzi et Mélanie ne travaillent plus au Sheraton.",
        "system_used": "Lightspeed",
        "estimated_minutes": 20
    },
    {
        "order": 40,
        "title_fr": "Vérifier no-shows groupe et Reinstate dans les RL",
        "category": "fin_quart",
        "description_fr": "Vérifier les réservations de groupe No-show et Reinstate qui font partie d'une Reservation List (RL). Traiter selon la politique de groupe.",
        "steps": [
            "Identifier les no-shows de groupe/RL",
            "Poster tout le séjour du groupe si nécessaire",
            "Transférer au compte maître du groupe",
            "Dupliquer la réservation pour les nuits restantes si Reinstate",
            "Mettre la rate à 0$ pour les nuits dupliquées",
            "Vérifier les 'Reinstate' et 'No-show' qui font partie d'une RL",
            "Traiter selon la politique de groupe",
            "Noter les anomalies pour le superviseur"
        ],
        "screenshots": [],
        "tips_fr": "Les groupes et RL ont des règles spéciales pour les no-shows. Consulter le superviseur si incertain.",
        "system_used": "Lightspeed",
        "estimated_minutes": 20
    },
    {
        "order": 41,
        "title_fr": "Placer les journaux à la SPESA et au Lounge",
        "category": "fin_quart",
        "description_fr": "Placer les journaux frais à la Spesa et au Lounge. Retirer les anciens et conserver la 1re page du Journal de Montréal. Ne pas oublier la Gazette de Montréal.",
        "steps": [
            "Retirer les anciens journaux de la Spesa",
            "Retirer les anciens journaux du Lounge",
            "Placer les nouveaux journaux dans les porte-journaux :",
            "  - Journal de Montréal",
            "  - La Gazette de Montréal (Montreal Gazette)",
            "Conserver la 1re page du Journal de Montréal",
            "Jeter les autres journaux périmés",
            "Ranger la 1re page du Journal de MTL sous le bureau du superviseur arrière",
            "Vérifier que les zones sont propres"
        ],
        "screenshots": [],
        "tips_fr": "Les clients apprécient des journaux frais le matin. C'est un détail important du service.",
        "system_used": "Manuel",
        "estimated_minutes": 10
    },
    {
        "order": 42,
        "title_fr": "À 6h00, ouvrir les lumières et ajuster la musique",
        "category": "fin_quart",
        "description_fr": "À 6h du matin, allumer les lumières de la réception et ajuster le volume de la musique pour l'arrivée du quart du matin.",
        "steps": [
            "Vérifier qu'il est 6h00",
            "Localiser les interrupteurs de lumière de réception",
            "Allumer toutes les lumières graduellement",
            "Localiser le système audio/musique",
            "Ajuster le volume à un niveau agréable (modéré, pas trop fort)",
            "Vérifier que l'ambiance est appropriée pour l'arrivée du quart du matin"
        ],
        "screenshots": [],
        "tips_fr": "Cela crée une bonne transition vers le quart du matin.",
        "system_used": "Manuel",
        "estimated_minutes": 5
    },
    {
        "order": 43,
        "title_fr": "Envoyer courriel Expected Arrivals",
        "category": "fin_quart",
        "description_fr": "Envoyer le courriel des arrivées attendues pour la journée à Stéphanie Lefebvre.",
        "steps": [
            "Ouvrir Outlook",
            "Créer un nouveau courriel",
            "Récipient : Stéphanie Lefebvre",
            "Sujet : 'Expected Arrivals'",
            "Contenu :",
            "  - Nombre total d'arrivées prévues",
            "  - Détails des arrivées importantes (groupes, VIP, etc.)",
            "  - Heures d'arrivée prévisionnelles",
            "Envoyer le courriel"
        ],
        "screenshots": [],
        "tips_fr": "Utilisez le template si disponible pour gagner du temps.",
        "system_used": "Outlook",
        "estimated_minutes": 10
    },
    {
        "order": 44,
        "title_fr": "Envoyer courriel de fin de quart",
        "category": "fin_quart",
        "description_fr": "Envoyer le courriel complet de fin de quart avec caisse, informations importantes et notes pour le matin.",
        "steps": [
            "Ouvrir Outlook",
            "Créer un nouveau courriel",
            "Destinataire : Superviseur Réception/Directeur",
            "Sujet : 'Fin de quart - [DATE]'",
            "Contenu :",
            "  - Résumé de la caisse (tirage)",
            "  - Incidents ou situations importantes",
            "  - Tâches complétées",
            "  - Notes pour le quart du matin",
            "  - Clients VIP en maison",
            "  - Problèmes en attente de résolution",
            "Envoyer le courriel"
        ],
        "screenshots": [],
        "tips_fr": "Soyez concis mais complet. Le superviseur a besoin des informations clés.",
        "system_used": "Outlook",
        "estimated_minutes": 15
    },
    {
        "order": 45,
        "title_fr": "Porter les papiers aux bureaux d'administration",
        "category": "fin_quart",
        "description_fr": "Apporter tous les documents finalisés aux bureaux d'administration. Demander du papier pour la réception si nécessaire.",
        "steps": [
            "Rassembler tous les rapports et documents finalisés",
            "Mettre les documents dans les piles appropriées",
            "Aller au bureau d'administration en bas",
            "Demander du papier si nécessaire",
            "Remettre les documents aux personnes responsables",
            "Obtenir une confirmation de réception"
        ],
        "screenshots": [],
        "tips_fr": "Apportez aussi une demande de papier si les stocks sont bas.",
        "system_used": "Manuel",
        "estimated_minutes": 15
    },
    {
        "order": 46,
        "title_fr": "Nettoyer l'espace de travail et messages au quart du matin",
        "category": "fin_quart",
        "description_fr": "Nettoyer votre espace de travail et laisser les messages nécessaires au quart du matin.",
        "steps": [
            "Ranger tous les papiers et documents personnels",
            "Nettoyer le bureau et l'écran",
            "Vérifier qu'il n'y a rien d'oublié",
            "Laisser un message au quart du matin si nécessaire",
            "Écrire dans le cahier de réception les informations importantes",
            "Vérifier que tout est prêt pour le prochain quart",
            "Partir en bon état"
        ],
        "screenshots": [],
        "tips_fr": "Un espace propre et une bonne documentation font une différence pour le quart suivant.",
        "system_used": "Manuel",
        "estimated_minutes": 15
    }
]
