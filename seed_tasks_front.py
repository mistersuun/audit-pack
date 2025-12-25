"""
Data file for Front Office tasks (detailed, chronological).
Basé sur les instructions détaillées pour l'auditeur de nuit (Front) au Sheraton Laval.
"""

TASKS_DETAILED = [
    # 0. ÉCHANGE D'INFORMATIONS AVEC LE QUART DU SOIR
    {
        "order": 1,
        "title_fr": "Échange d'informations avec le quart du soir",
        "category": "pre_audit",
        "role": "front",
        "description_fr": "Faire le transfert d'information avec l'équipe du soir avant de commencer le travail.",
        "steps": [
            "Échanger les informations avec le quart du soir (arrivées restantes, situations clients, groupes, etc.).",
            "Noter les points importants à suivre pendant la nuit.",
            "S'assurer d'avoir toutes les informations nécessaires avant de commencer."
        ],
        "system_used": "Communication",
        "estimated_minutes": 5
    },

    # 1. SETUP INITIAL - Accès et logistique
    {
        "order": 2,
        "title_fr": "Setup initial - Accès et logistique",
        "category": "pre_audit",
        "role": "front",
        "description_fr": "Installer le poste, vérifier le panneau incendie, accéder aux systèmes et préparer les wake-up calls.",
        "steps": [
            "Panneau d'incendie : se trouve à la gauche de la réception, vérifier le statut (normal).",
            "Connexions aux systèmes : se fait sur l'île (n'importe quel ordinateur de la réception).",
            "Papiers : se trouvent en bas dans les bureaux de l'admin près de leur imprimante. Code de la porte : 3514#.",
            "Ordinateur de gauche à la réception : changer d'utilisateur → Username: Auditeur, Mot de passe: Green176. Accès direct à l'Audit Pack qui contient les documents nécessaires.",
            "Wake-up calls : généralement pas nécessaire de vérifier Espresso. Le cahier de la réception ou les employés de la réception nous font signe s'il y en a à ajouter. Sinon, sur le téléphone le plus à droite à la réception, il y a un bouton Réveil → entrer le numéro de la chambre suivi du # → mettre l'heure au format 630 pour 6h30 → demandera AM ou PM → ce sera fait."
        ],
        "system_used": "Windows / Téléphone",
        "estimated_minutes": 10
    },

    # 2. DOCUMENTS - Séparateur date, feuille entretien, feuille tournée
    {
        "order": 3,
        "title_fr": "Préparation des documents (séparateur, entretien, tournée)",
        "category": "pre_audit",
        "role": "front",
        "description_fr": "Préparer le séparateur daté, la feuille d'entretien avec météo, et la feuille de tournée.",
        "steps": [
            "Séparateur date : clic droit sur Word → sélectionner 'Séparateur date' → changer juste le jour et la date → imprimer → plier en deux → mettre à gauche de l'écran de l'ordi où on fait l'impression (pour tous les documents à donner à la comptabilité).",
            "Feuille entretien : clic droit sur Word → sélectionner 'Feuille d'entretien' → changer le jour et la date (toujours du lendemain) jusqu'au jour +4 pour avoir la météo pour les prochains jours.",
            "Météo : aller sur MétéoMédia Laval 7 jours → utiliser Snipping Tool → copier → aller sur Word → cliquer les anciennes photos → Change Picture → Paste (pour juste changer l'image mais pas le placement). Snip toujours deux jours à la fois pour en avoir 4.",
            "IMPORTANT : imprimer la feuille entretien en RECTO-VERSO.",
            "Feuille de tournée : clic droit sur Excel → sélectionner 'Feuille de tournée' → changer la date → imprimer → SIGNER.",
            "Déposer : prendre la feuille d'entretien et la feuille de tournée → les mettre à droite des comptoirs de réception (vers la tabagie SPESA) pour l'équipe d'entretien le matin qui vont la ramasser."
        ],
        "tips_fr": "Utilise Change Picture pour garder la mise en page; recto-verso obligatoire pour la météo. Le séparateur date plié en deux servira pour tous les documents comptables.",
        "system_used": "Word / Excel / MétéoMédia / Snipping Tool",
        "estimated_minutes": 15
    },

    # 3. UPS
    {
        "order": 4,
        "title_fr": "Feuille UPS",
        "category": "pre_audit",
        "role": "front",
        "description_fr": "Imprimer la feuille de sign-in UPS pour le lendemain.",
        "steps": [
            "Ouvrir Chrome sur l'ordinateur de gauche.",
            "Sélectionner le favori 'UPS Plugin'.",
            "Cliquer 'Go to Home'.",
            "Username et password sont pré-remplis → cliquer sur 'Login'.",
            "Sélectionner l'onglet 'Sign in sheet' à gauche.",
            "Cliquer 'View and Print' → redirection sur une autre page.",
            "Sélectionner UPS et laisser la date du lendemain → 'View'.",
            "Une fois fait, imprimer → plier la feuille en 3 → mettre dans le bac des réceptionnistes entre le poste de droite et le poste central."
        ],
        "system_used": "Chrome / UPS Plugin",
        "estimated_minutes": 5
    },

    # 4. FEDEX
    {
        "order": 5,
        "title_fr": "Feuille FedEx",
        "category": "pre_audit",
        "role": "front",
        "description_fr": "Remplir et imprimer la feuille FedEx avec les chambres des pilotes.",
        "steps": [
            "Récupérer le cahier de la réception (ils ont noté et assigné les chambres des pilotes déjà).",
            "Clic droit sur Excel → chercher 'FEDEX room records'.",
            "Effacer les infos dessus.",
            "Mettre à jour la date d'arrivée.",
            "Pour FEDEX : ne noter que les chambres (nous n'avons pas les noms des pilotes encore).",
            "Save → imprimer → plier en 3 → mettre avec UPS."
        ],
        "tips_fr": "FedEx : seulement les numéros de chambres, pas les noms.",
        "system_used": "Excel / Cahier réception",
        "estimated_minutes": 5
    },

    # 5. CARGOJET
    {
        "order": 6,
        "title_fr": "Feuille Cargojet",
        "category": "pre_audit",
        "role": "front",
        "description_fr": "Remplir la feuille Cargojet avec les chambres ET les noms complets des pilotes.",
        "steps": [
            "Clic droit sur Excel → chercher 'CARGO JET'.",
            "Effacer les infos dessus.",
            "Mettre à jour la date d'arrivée.",
            "Pour Cargojet : nous avons les noms donc il faut les marquer en vérifiant sur Lightspeed en même temps.",
            "Pour chaque pilote : rentrer le numéro de chambre → valider le nom complet sur Lightspeed → le mettre sur la feuille Excel.",
            "Save → imprimer → mettre avec les deux autres documents de pilotes (UPS et FedEx)."
        ],
        "tips_fr": "Cargojet : vérifier les noms complets sur Lightspeed pour chaque chambre.",
        "system_used": "Excel / Lightspeed / Cahier réception",
        "estimated_minutes": 8
    },

    # 6. PRÉ-AUDIT - Vérifier arrivals et lancer
    {
        "order": 7,
        "title_fr": "Pré-audit : vérifier arrivals et lancer",
        "category": "part1",
        "role": "front",
        "description_fr": "Vérifier les arrivées restantes et lancer le pre-audit Lightspeed.",
        "steps": [
            "Se connecter à Lightspeed.",
            "Regarder les Arrivals → s'il en reste, vérifier qu'ils sont gérables.",
            "Cliquer sur l'icône de la lune (onglet Night Audit).",
            "Cliquer sur 'Run Pre-Audit'.",
            "Les documents vont s'imprimer en arrière dans le bureau.",
            "Partir chercher les documents."
        ],
        "system_used": "Lightspeed",
        "estimated_minutes": 6
    },

    # 8. PRÉ-AUDIT - Trier les documents
    {
        "order": 8,
        "title_fr": "Pré-audit : trier les documents",
        "category": "part1",
        "role": "front",
        "description_fr": "Trier les rapports imprimés et préparer pour le traitement.",
        "steps": [
            "Chercher le 'Actual Departure Report' → le mettre de côté.",
            "Chercher le 'Complimentary Rooms Report' → mettre cette fois-ci de côté à droite de ton écran à côté du téléphone pour reprendre plus tard quand tu auras fini le Part 2.",
            "Noter le CO: s'il y a des complimentary rooms.",
            "Mettre SD: mais ne rien mettre car tu n'as pas encore le chiffre."
        ],
        "system_used": "Lightspeed Reports",
        "estimated_minutes": 3
    },

    # 9. ACTUAL DEPARTURES - Ajustements ±1$
    {
        "order": 9,
        "title_fr": "Actual Departures : ajuster les montants entre 1$ et -1$",
        "category": "part1",
        "role": "front",
        "description_fr": "Corriger manuellement les folios avec des montants résiduels entre 1$ et -1$ pour les mettre à 0.",
        "steps": [
            "Prendre Actual Departures et les agrafer ensemble.",
            "Regarder la colonne 'Gst' seulement pour voir s'il y a des montants entre 1$ et -1$.",
            "Si oui, on doit les ajuster manuellement pour les mettre à 0.",
            "Pour chaque chambre à corriger :",
            "  - Trouver le montant à corriger (exemple: 0.68 qui est un montant positif).",
            "  - Aller sur Lightspeed → mettre le numéro de chambre → cliquer sur l'utilisateur → s'assurer du bon nom.",
            "  - Faire 'Modify'.",
            "  - En haut, cliquer sur 'Cashiering'.",
            "  - Cliquer sur 'Post' dans le département.",
            "  - On choisit 40 et subdepartment on sélectionne 60 si c'est un montant positif (montant en noir en bas) ou 10 lorsque c'est un montant négatif (rouge en bas).",
            "  - Dans 'Ref' on met CLOSE.",
            "  - Dans 'Note' on met le chiffre 1.",
            "  - Ensuite 'Add to List' et 'Post'.",
            "  - Le montant devrait alors devenir 0 pour le folio.",
            "Une fois fait, on peut l'enregistrer et fermer.",
            "S'assurer de faire ça pour toutes les chambres qui ont un montant entre 1$ et -1$.",
            "Mettre le document dans le séparateur date à gauche de l'écran qu'on avait plié en deux tout à l'heure."
        ],
        "tips_fr": "Dept 40 / Sub 60 = positif (noir), Dept 40 / Sub 10 = négatif (rouge). Ref CLOSE, Note 1.",
        "system_used": "Lightspeed",
        "estimated_minutes": 15
    },

    # 10. GROUPES - Group Delegate
    {
        "order": 10,
        "title_fr": "Groupes : Group Delegate Guests",
        "category": "part1",
        "role": "front",
        "description_fr": "Imprimer la liste des Group Delegate Guests.",
        "steps": [
            "Ouvrir l'onglet Reports encore.",
            "Cliquer 'In-House List'.",
            "Sélectionner dans 'Report Option' : 'Group Delegate Guests'.",
            "Sélectionner les options suivantes :",
            "  - Page break ON group",
            "  - Include room rates YES",
            "  - Sort order : by Group Code, Room Number.",
            "Submit et Print.",
            "Agrafer ensemble."
        ],
        "system_used": "Lightspeed Reports",
        "estimated_minutes": 5
    },

    # 11. GROUPES - Wholesaler Delegates
    {
        "order": 11,
        "title_fr": "Groupes : Wholesaler Delegates",
        "category": "part1",
        "role": "front",
        "description_fr": "Imprimer la liste des Wholesaler Delegates.",
        "steps": [
            "Toujours dans In-House List.",
            "Sélectionner 'Wholesaler Delegates'.",
            "Include Tour Code : ALL",
            "Sort order : by Room Number.",
            "Submit → imprimer → agrafer.",
            "Aller en arrière dans le dernier tiroir de l'étagère → prendre une chemise bleue.",
            "Mettre les documents dedans avec la date d'aujourd'hui."
        ],
        "system_used": "Lightspeed Reports",
        "estimated_minutes": 5
    },

    # 12. ROOM STATUS DETAILS
    {
        "order": 12,
        "title_fr": "Room Status Details",
        "category": "part1",
        "role": "front",
        "description_fr": "Imprimer le Room Status Details et faire les copies du logbook.",
        "steps": [
            "Ouvrir l'onglet Rapport sur Lightspeed.",
            "Cliquer sur 'Room Status Details'.",
            "Options :",
            "  - Include ALL rooms",
            "  - Include all status",
            "  - Sort order : by Room",
            "Submit → imprimer.",
            "Mettre en arrière sur l'étagère sur les caisses pour la gouvernante le matin.",
            "Prendre le cahier de la réception/logbook.",
            "Faire des copies des 3 pages.",
            "Les mettre sur le Room Status Details."
        ],
        "system_used": "Lightspeed Reports / Photocopieur",
        "estimated_minutes": 8
    },

    # 13. FOLIO AMERISPA
    {
        "order": 13,
        "title_fr": "Vérifier et clore le folio Amerispa",
        "category": "part1",
        "role": "front",
        "description_fr": "Vérifier le folio Amerispa, le clore si nécessaire et assembler avec les reçus.",
        "steps": [
            "Retourner sur Lightspeed.",
            "Cliquer sur 'Cashiering'.",
            "Entrer le nom 'Amerispa' → on devrait le voir en bleu foncé.",
            "Regarder la balance : si elle est à 0, on peut quitter (il n'y a pas de transactions à settle).",
            "Sinon, cliquer pour ouvrir → cliquer 'Settle'.",
            "Une page s'ouvrira → faire 'Apply'.",
            "Le montant devrait maintenant montrer 0.",
            "On doit maintenant fermer cette page et imprimer le folio.",
            "Aller voir le back pour demander le reçu ou les reçus.",
            "En faire des copies.",
            "Les agrafer avec le folio imprimé.",
            "Mettre dans le séparateur date."
        ],
        "system_used": "Lightspeed / Photocopieur",
        "estimated_minutes": 10
    },

    # 14. FACTURES GROUPES ET RL
    {
        "order": 14,
        "title_fr": "Factures des groupes et RL",
        "category": "part1",
        "role": "front",
        "description_fr": "Photocopier les factures des groupes/RL, imprimer les folios et assembler.",
        "steps": [
            "Prendre les factures des groupes et RL.",
            "Faire des photocopies.",
            "Retourner dans Cashiering.",
            "Écrire le nom du groupe ou RL.",
            "Imprimer le folio.",
            "Agrafer avec les copies de reçu derrière.",
            "Faire ça pour tous les groupes ou RL.",
            "Mettre dans le séparateur date."
        ],
        "system_used": "Lightspeed / Photocopieur",
        "estimated_minutes": 12
    },

    # 15. INTERNET - Rapport 36.1
    {
        "order": 15,
        "title_fr": "Internet : Rapport 36.1 (vérification et corrections)",
        "category": "part1",
        "role": "front",
        "description_fr": "Générer le rapport 36.1, vérifier et corriger les montants pour les membres, VIP et pilotes.",
        "steps": [
            "Ouvrir Reports.",
            "Cashier Detail :",
            "  - Mettre 36 comme département",
            "  - 36.1 comme sous-département",
            "  - Include all users",
            "  - Include posting notation",
            "  - Include deposit ledger detail",
            "  - By user id, hotel code, room number",
            "Submit mais NE PAS IMPRIMER ENCORE.",
            "Chercher les noms et les chambres.",
            "Partir sur le menu de Lightspeed → chercher la chambre → cliquer 'Modify'.",
            "Si le client est membre : la charge devrait être 4.95.",
            "  - Faire Cashiering → Posting Summary → Details.",
            "  - Il y a un crayon à côté de la charge et des taxes.",
            "  - Cliquer dessus pour les trois montants qui sont 9.95, 1.02 et 0.5.",
            "  - Les modifier pour 4.95, 0.52 et 0.25 respectivement.",
            "Par contre, si la personne est membre Gold, Platinum, Titanium ou Ambassadeur : on doit transférer.",
            "  - Faire Cashiering → Transfer.",
            "  - Cliquer 'House List' en bas.",
            "  - Écrire 'Marriott Internet'.",
            "  - On sélectionne lui en bleu foncé.",
            "  - Maintenir la touche Contrôle du clavier.",
            "  - Sélectionner les trois charges.",
            "  - Avec la souris, cliquer et les déplacer vers le bas qui est le folio Marriott Internet pour leur enlever la charge.",
            "On peut les enlever pour les pilotes aussi car ils n'ont généralement pas de carte de crédit au dossier et c'est le compte maître qui paye.",
            "Par contre, si la personne n'est pas membre : on ne touche à rien et la personne sera chargée le montant complet.",
            "Une fois tout modifié et transféré, on peut maintenant régénérer le 36.1 et cette fois-ci l'imprimer."
        ],
        "tips_fr": "Membres standard = 4.95/0.52/0.25. VIP/Pilotes = transférer vers Marriott Internet. Non-membres = ne rien changer.",
        "system_used": "Lightspeed",
        "estimated_minutes": 25
    },

    # 16. INTERNET - Settle Marriott Internet et 36.5
    {
        "order": 16,
        "title_fr": "Internet : Settle Marriott Internet et rapport 36.5",
        "category": "part1",
        "role": "front",
        "description_fr": "Clore le compte Marriott Internet et imprimer le rapport 36.5.",
        "steps": [
            "Aller dans Cashiering.",
            "Écrire 'Marriott Internet' en bleu foncé.",
            "L'ouvrir → faire 'Settle' → 'Apply'.",
            "Ensuite imprimer le folio.",
            "Retourner dans Rapport.",
            "Au lieu de faire 36.1, on fait 36.5.",
            "Submit → imprimer.",
            "Partir ramasser les trois impressions (36.1, folio Marriott Internet, 36.5).",
            "Les agrafer ensemble.",
            "Les remettre à l'auditeur du back."
        ],
        "system_used": "Lightspeed",
        "estimated_minutes": 8
    },

    # 17. CLÉS BANQUETS (après Internet, avant vérifier arrivals)
    {
        "order": 17,
        "title_fr": "Clés banquets pour le lendemain",
        "category": "part1",
        "role": "front",
        "description_fr": "Préparer la liste des clés banquets pour les événements du lendemain.",
        "steps": [
            "Pour les clés banquet pour le lendemain : aller sous l'ordinateur de droite → il y a un gros cartable → le prendre.",
            "Ouvrir à la date du lendemain.",
            "Ouvrir le fichier 'Copie clef banquet' qui est dans Audit Pack (ou en faisant clic droit sur Word et trouver le document).",
            "Prendre le nom d'affichage et le mettre.",
            "Vis-à-vis la salle qu'ils ont louée : mettre l'heure de départ la plus tôt et l'heure de quitter la plus tard (même si c'est séparé en blocs distincts).",
            "Mettre le nom du client qui est aussi la personne ressource.",
            "Une fois fait et vérifié → imprimer le document.",
            "Mettre avec les feuilles de pilotes entre l'ordi de droite et l'ordi central."
        ],
        "system_used": "Word / Cartable banquets",
        "estimated_minutes": 8
    },

    # 18. VÉRIFIER ARRIVALS AVANT AUDIT
    {
        "order": 18,
        "title_fr": "Vérifier les arrivals avant de run l'audit",
        "category": "part2",
        "role": "front",
        "description_fr": "Vérifier une dernière fois les arrivals et charger les advance deposits si nécessaire.",
        "steps": [
            "Une fois que le back est prêt, on peut aller sur Lightspeed.",
            "Avant de run l'audit, revérifier les Arrivals.",
            "Car s'il y en a, il faut les charger l'advance deposit ou canceller la réservation si la carte ne passe pas.",
            "On fait 'Modify' sur l'arrival qui n'est pas là.",
            "Au bas de l'écran à droite, à côté du paiement, on voit un crayon → cliquer dessus.",
            "Ensuite cliquer sur 'Add Deposit'.",
            "On choisit la calculatrice et on met le montant sans taxe multiplié par 1.19 pour les taxes.",
            "On essaye de passer la transaction.",
            "Si elle ne passe pas, on peut annuler.",
            "Une fois fait, on peut run l'audit et fermer la journée."
        ],
        "system_used": "Lightspeed",
        "estimated_minutes": 10
    },

    # 19. RUN AUDIT - Post Room and Tax
    {
        "order": 19,
        "title_fr": "Run Audit : Post Room and Tax",
        "category": "part2",
        "role": "front",
        "description_fr": "Lancer Post Room and Tax qui va fermer la journée.",
        "steps": [
            "Aller sélectionner l'onglet Night Audit.",
            "Cliquer 'Post Room and Tax'.",
            "Le système va prendre du temps et déconnecter tout le monde.",
            "Une fois qu'il redémarre, on se reconnecte."
        ],
        "system_used": "Lightspeed",
        "estimated_minutes": 10
    },

    # 20. RUN AUDIT - Run Audit
    {
        "order": 20,
        "title_fr": "Run Audit : Run Audit",
        "category": "part2",
        "role": "front",
        "description_fr": "Lancer l'audit complet qui va générer tous les rapports.",
        "steps": [
            "Retourner sur Night Audits.",
            "Cliquer 'Run Audit'.",
            "Pendant ce temps, aller demander à l'auditeur du back les informations pour les pourboires."
        ],
        "system_used": "Lightspeed",
        "estimated_minutes": 15
    },

    # 21. POURBOIRES (POD)
    {
        "order": 21,
        "title_fr": "Pourboires (POD) pendant l'audit",
        "category": "part2",
        "role": "front",
        "description_fr": "Remplir le fichier POD avec les ventes et pourboires par serveur et vérifier le balancement.",
        "steps": [
            "Prendre les feuilles individuelles de pourboires.",
            "Ouvrir le fichier POD pour les deux semaines courantes.",
            "Le remplir en mettant le montant des ventes par noms et le montant de pourboires reçu.",
            "Ensuite ça va nous mettre un total.",
            "Prendre la feuille que le back nous a donnée.",
            "Prendre la deuxième colonne et surligner les serveurs qu'on a mis sur le fichier pour les exclure.",
            "Prendre le total vendu et soustraire les montants non surlignés pour voir si le montant qui reste est égal au montant entré pour chacun des serveurs individuel pour savoir qu'on n'a pas fait d'erreurs.",
            "Une fois fini et balancé, enregistrer.",
            "Prendre les feuillets de déclaration et les agrafer au dos de la feuille des totaux remis par l'auditeur du back.",
            "Mettre le tout dans le séparateur date."
        ],
        "tips_fr": "Vérification : Total vendu - (non-serveurs) = Total ventes POD par serveur.",
        "system_used": "Excel POD",
        "estimated_minutes": 20
    },

    # 22. IMPRESSIONS POST-AUDIT
    {
        "order": 22,
        "title_fr": "Impressions post-audit (rapports obligatoires)",
        "category": "part2",
        "role": "front",
        "description_fr": "Imprimer tous les rapports obligatoires dans l'ordre spécifique.",
        "steps": [
            "Le Audit Report devrait avoir été imprimé pendant ce temps.",
            "Juste avant de commencer, on peut imprimer dans Reports :",
            "",
            "No Posting Allowed :",
            "  - Options : All guests, In-house only, by room number",
            "  - Imprimer → mettre dans la pile Restaurant.",
            "",
            "Guest List - Charge All :",
            "  - Options : Registered guest → No comments → Special Service CA → By room number",
            "  - Imprimer → mettre dans la pile Restaurant.",
            "",
            "Allotment Overview :",
            "  - Imprimer (49 jours) pour le DBRS.",
            "  - Start date → Today",
            "  - End Date → Today+49",
            "  - Imprimer → pile DBRS.",
            "",
            "In-House List (Spécial G4) :",
            "  - x3 copies (DBRS, Auditeur, Restaurant).",
            "  - Options : Registered guest → No comments → Include room rate → Special Service G4 → By room number",
            "  - Imprimer 3 fois → distribuer.",
            "",
            "In-House List (Spécial G4+CL) :",
            "  - x2 copies (Superviseur, Restaurant).",
            "  - Options : Registered guest → No comments → Include room rate → Special Service G4,CL → By room number",
            "  - Imprimer 2 fois → distribuer.",
            "",
            "Une fois tout imprimé, mettre les feuilles pour le restaurant à l'arrière près de la pile pour gouvernante.",
            "Ensuite faire la séparation pour les autres départements.",
            "Arriver aux feuilles de High Balance → les mettre de côté pour plus tard.",
            "Et un des feuillets No Show aussi → continuer la séparation.",
            "Une fois fini, aller faire 2 copies supplémentaires de la pile DBRS.",
            "Agrafer les copies individuelles.",
            "Mettre une pour l'auditeur, une pour la réception et une dans le pigeonnier de Nathalia à l'arrière.",
            "Donner à l'auditeur du back sa pile aussi."
        ],
        "system_used": "Lightspeed Reports",
        "estimated_minutes": 25
    },

    # 23. HIGH BALANCE
    {
        "order": 23,
        "title_fr": "High Balance : tester les cartes",
        "category": "part2",
        "role": "front",
        "description_fr": "Tester les cartes de crédit en balance élevée pour valider qu'elles sont actives.",
        "steps": [
            "Prendre les High Balance.",
            "Sur Lightspeed, mettre le numéro de chambre.",
            "Faire Cashiering → Settle → Apply.",
            "Ensuite, si la transaction passe, faire le X rouge pour annuler (on a validé que la carte est active et valide).",
            "Passer au suivant jusqu'à les avoir testés.",
            "Mettre un OK si la carte est valide.",
            "Mettre une note pour si elle ne passe pas.",
            "On peut maintenant aller voir les Did Not Arrive Open."
        ],
        "system_used": "Lightspeed",
        "estimated_minutes": 12
    },

    # 24. NO-SHOWS (Did Not Arrive Open)
    {
        "order": 24,
        "title_fr": "No-Shows : Did Not Arrive Open",
        "category": "part2",
        "role": "front",
        "description_fr": "Poster les no-shows de la veille où on a pris l'advance deposit.",
        "steps": [
            "Ce sont les no-shows de la veille où on a pris l'advance deposit.",
            "Il faut maintenant ouvrir leurs dossiers avec 'Modify' sur Lightspeed.",
            "Cashiering → Post → Département 1, Sub Department 28 pour No Show.",
            "Mettre le montant sans taxes.",
            "Ref : NO SHOW.",
            "Ensuite mettre le nom dans Notes.",
            "Post.",
            "Ensuite imprimer le folio actif.",
            "Sur Excel, ouvrir la feuille d'ajustement.",
            "Mettre le numéro de folio, le nom, le montant, ensuite les taxes.",
            "Imprimer.",
            "Agrafer le folio avec la feuille d'ajustement (qui sera en avant).",
            "Aller les mettre sur le bureau de la réception à l'arrière avec les autres rapports imprimés pour elle.",
            "",
            "Si c'est un client normal : on charge juste une nuit donc le montant sur le rapport No Show.",
            "",
            "Si c'est une RL :",
            "  - On charge tout dans Post, pas juste une nuit.",
            "  - On imprime le folio.",
            "  - Ensuite on refait un transfert comme avec internet mais en mettant le nom de la RL ou du groupe.",
            "  - On leur transfère la charge.",
            "  - Ensuite, si c'est pour plus d'une nuit, on doit dupliquer la réservation pour les jours restants si la personne se présente durant le séjour.",
            "  - En cliquant en haut à gauche → faire 'Copy All Same Guest Same Dates'.",
            "  - Choisir un rate et mettre manuellement le montant à 0 pour ne pas qu'on charge en double le groupe et le compte maître.",
            "  - Mettre comptant et enregistrer la nouvelle réservation.",
            "  - Faire la feuille d'ajustement."
        ],
        "tips_fr": "Client normal = 1 nuit. RL/Groupe = tout le séjour + transfert + duplication si multi-nuits.",
        "system_used": "Lightspeed / Excel ajustement",
        "estimated_minutes": 15
    },

    # 25. FEUILLE DE RÉCEPTION - Checkouts
    {
        "order": 25,
        "title_fr": "Feuille de réception : checkouts après Part 2",
        "category": "part2",
        "role": "front",
        "description_fr": "Reprendre la feuille de réception et faire les checkouts des départs après Part 2.",
        "steps": [
            "Reprendre la feuille de réception.",
            "Regarder la colonne départ après Part 2.",
            "Checkout les guest en vérifiant qu'il n'y a pas de charge restantes.",
            "Charger la carte avant checkout le cas échéant."
        ],
        "system_used": "Lightspeed / Feuille réception",
        "estimated_minutes": 10
    },

    # 26. PLUG-INS PILOTES
    {
        "order": 26,
        "title_fr": "Plug-ins : pilotes in-house ou en départ",
        "category": "end_shift",
        "role": "front",
        "description_fr": "Préparer les courriels pour les pilotes qui sont in-house ou en départ plus tard dans la journée.",
        "steps": [
            "Sur Lightspeed, ouvrir l'onglet Quick Modify.",
            "Le crayon et sélectionner 'Registered Guest' et 'Wholesaler Code'.",
            "Search.",
            "On va voir les listes avec le code CA***, FE***, UP*** pour chaque groupe de pilote.",
            "Mettre les numéros de chambres dans le courriel sur Outlook.",
            "On peut revérifier sur Lightspeed en mettant le numéro de chambre et regarder les notes.",
            "Ajouter des détails au courriel comme l'heure de départ prévu des pilotes."
        ],
        "system_used": "Lightspeed / Outlook",
        "estimated_minutes": 10
    },

    # 27. MACHINE À VIN
    {
        "order": 27,
        "title_fr": "Machine à vin (Lounge)",
        "category": "end_shift",
        "role": "front",
        "description_fr": "Facturer les vins ouverts de la machine à vin du lounge.",
        "steps": [
            "Partir sur Enoclient sur l'ordinateur.",
            "Username : Reception",
            "Mot de passe : 1234",
            "Ensuite faire Statistics → Reports Management → Yesterday and Today's Tastings → Load.",
            "Ensuite cliquer le carré rouge en haut à gauche → Print.",
            "Prendre la feuille.",
            "Aller à la Piazza sur POSitouch.",
            "Mettre ton code.",
            "Mettre numéro de client 800 → Entrer.",
            "Ensuite mettre 1 → Entrer.",
            "Ensuite cliquer Menu Divers → Vins Ouvert.",
            "Mettre le montant du vin.",
            "Puis le nom du vin.",
            "Ajouter tout ceux pour la même chambre.",
            "Quand tu es prêt → Faire Paiement → Chambres.",
            "Mettre le numéro et valider.",
            "Ça va faire 3 impressions → les mettre ensemble en ordre crescendo.",
            "Agrafer sur la feuille.",
            "Une fois tous entrés dans le système, le mettre dans le back dans le panier des factures pour la nuit suivante."
        ],
        "system_used": "Enoclient / POSitouch",
        "estimated_minutes": 15
    },

    # 28. COURRIEL EXPECTED ARRIVALS
    {
        "order": 28,
        "title_fr": "Courriel Expected Arrivals",
        "category": "end_shift",
        "role": "front",
        "description_fr": "Envoyer le courriel des expected arrivals du jour.",
        "steps": [
            "Pour le courriel de Expected Arrivals, il faut ouvrir Lightspeed.",
            "Aller dans Reports.",
            "Cliquer sur 'Expected Arrivals' avec les options suivantes :",
            "  - Start date : Today",
            "  - End date : Today",
            "Submit → Save.",
            "Envoyer par courriel avec le template de la veille."
        ],
        "system_used": "Lightspeed / Outlook",
        "estimated_minutes": 5
    },

    # 29. COURRIEL INCIDENTS
    {
        "order": 29,
        "title_fr": "Courriel incidents de la nuit",
        "category": "end_shift",
        "role": "front",
        "description_fr": "Envoyer le courriel des incidents de la nuit si nécessaire.",
        "steps": [
            "Envoyer le courriel à partir du template de la veille par rapport aux incidents de la nuit."
        ],
        "system_used": "Outlook",
        "estimated_minutes": 5
    },

    # 30. RESOB
    {
        "order": 30,
        "title_fr": "RESOB (365 jours)",
        "category": "end_shift",
        "role": "front",
        "description_fr": "Imprimer le rapport RESOB pour 365 jours et distribuer dans les pigeonniers.",
        "steps": [
            "Imprimer RESOB avec :",
            "  - Start date : Today",
            "  - End date : Today+365",
            "Imprimer 9 fois.",
            "Mettre dans les pigeonniers."
        ],
        "system_used": "Lightspeed Reports",
        "estimated_minutes": 8
    },

    # 31. JOURNAUX
    {
        "order": 31,
        "title_fr": "Journaux : remplacer et trier",
        "category": "end_shift",
        "role": "front",
        "description_fr": "Remplacer les journaux reçus et trier ceux à garder vs recycler.",
        "steps": [
            "Aller à l'entrée et prendre les journaux reçus (sauf le dimanche où on ne reçoit rien).",
            "Aller les remplacer.",
            "Garder uniquement les pages couvertures des anciens Journal de Montréal.",
            "Garder les journaux complets de la Gazette (car on nous paye lorsqu'on les rend à la fin du mois).",
            "Les mettre en arrière sous le bureau du superviseur.",
            "Sinon jeter le reste et remplacer avec les nouveaux."
        ],
        "system_used": "Manuel",
        "estimated_minutes": 8
    }
]
