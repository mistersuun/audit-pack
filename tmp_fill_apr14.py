import sys
sys.stdout.reconfigure(encoding='utf-8')

# April 14, 2026 - Full Jour row computation

SJ = {
    'Piazza_Nour': 3585.00, 'Piazza_Alcool': 1550.00, 'Piazza_Biere': 539.50,
    'Piazza_Min': 156.50, 'Piazza_Vin': 539.00,
    'SCh_Nour': 226.00, 'SCh_Biere': 11.00, 'SCh_Min': 4.25, 'SCh_Vin': 28.00, 'SCh_FREtage': 18.00,
    'Bqt_Nour': 8410.00, 'Bqt_PourbAPayer': 1986.48, 'Bqt_EqDivers': 80.00,
    'Bqt_LocSalle': 9300.00, 'Bqt_Internet': 460.00, 'Bqt_PauseSpesa': 2626.00,
    'Spesa_Nour': 1223.89, 'Spesa_Tabagie': 1021.03,
    'TPS': 1528.09, 'TVQ': 3047.97, 'Comptant': 941.90,
    'Visa_dbt': 2836.40, 'MC_dbt': 1616.48, 'AMEX_dbt': 484.20, 'Interac_dbt': 1415.99,
    'Chambre_dbt': 29580.22, 'Admin_dbt': 343.49, 'HotelPromo_dbt': 830.79,
    'Forfait_dbt': 170.16, 'PanneLienHotel_dbt': 4.88,
    'PourbCharge': 1307.86,
}

DR = {
    'Chambres_Total': 50695.88, 'Nettoyeur': 257.80, 'Internet': 0,
    'AutreGL': -157384.06, 'ARMisc': 7061.00,
    'TVH': 1775.29, 'TPS_Ch': 2623.45, 'TVQ_Ch': 5231.01,
    'TPS_Piazza': 102.97, 'TVQ_Piazza': 205.38,
    'TPS_Bqt': 1143.13, 'TVQ_Bqt': 2280.56,
    'TPS_Spesa': 13.05, 'TVQ_Spesa': 26.01,
    'TPS_Autres': 12.90, 'TVQ_Autres': 25.71,
    'TPS_Internet': 0, 'TVQ_Internet': 0,
    'RembServeur': 1021.02,
    'set_AMEX': -5613.06, 'set_Visa': -15185.17, 'set_MC': -17789.51,
    'set_Comptant': -78.18, 'set_Debit': 0, 'set_FD': -2384.64,
    'dep_AX': 0, 'dep_Visa': 3127.87, 'dep_MC': 5953.94,
    'AdvDep_Applied': -5901.44, 'AdvDep_DNA': -260.61,
    'InterHotel_In': 0, 'BalPrevDay': -1378635.51, 'BalToday': -98253.73,
    'NewBalance': -1476889.24,
}

AR = {'GuestFolios': 2384.64}

HP = {
    'Piazza_Nour': 612, 'Piazza_Boisson': 47, 'Piazza_Biere': 0,
    'Piazza_Min': 65.5, 'Piazza_Vin': 84,
    'Tabagie_Nour': 7, 'Tabagie_Tab': 245.44,
    'AdminPourb': 36.99, 'PromoPourb': 76.35,
}

RECAP = {
    'ArgentRecu': 2354.63, 'RembServeur': -1021.02, 'PourbCharge': -1307.86,
    'DueBackRecept': -946.03, 'SurplusDeficit': 56.56,
}

ADJ = {'Piazza_Nour': 2.96, 'Spesa_Nour': 4.05, 'G4': 40}

TRX_REST = {'Visa': 2542.45, 'MC': 1449.76, 'AMEX': 484.20, 'Debit': 1191.00, 'Discover': 0}

bal_ouv = -1830988.79

# Compute
AK = DR['Chambres_Total'] - ADJ['G4']
BF_ffait = -(SJ['Forfait_dbt'] - ADJ['G4'])
J = SJ['Piazza_Nour'] - HP['Piazza_Nour'] - ADJ['Piazza_Nour']
K = SJ['Piazza_Alcool'] - HP['Piazza_Boisson']
L = SJ['Piazza_Biere'] - HP['Piazza_Biere']
M = SJ['Piazza_Min'] - HP['Piazza_Min']
N = SJ['Piazza_Vin'] - HP['Piazza_Vin']
T = SJ['SCh_Nour']; U = 0; V = SJ['SCh_Biere']; W = SJ['SCh_Min']; X = SJ['SCh_Vin']
Y = SJ['Bqt_Nour']; Z = 0; AA = 0; AB = 0; AC = 0
AD = SJ['Bqt_PourbAPayer']
AE = 0; AF = SJ['Bqt_EqDivers']; AG = SJ['Bqt_LocSalle']; AH = 0
O_col = SJ['Spesa_Nour'] - HP['Tabagie_Nour'] - ADJ['Spesa_Nour']
AJ = SJ['Spesa_Tabagie'] - HP['Tabagie_Tab']
E = SJ['Bqt_PauseSpesa']
BB = 0
AO = DR['Nettoyeur']
AS = DR['AutreGL']
AU = SJ['SCh_FREtage'] + DR['InterHotel_In']
AW = DR['Internet'] + SJ['Bqt_Internet']
AX = DR['TVQ_Ch'] + SJ['TVQ'] + DR['TVQ_Piazza'] + DR['TVQ_Bqt'] + DR['TVQ_Spesa'] + DR['TVQ_Autres'] + DR['TVQ_Internet']
AY = DR['TPS_Ch'] + SJ['TPS'] + DR['TPS_Piazza'] + DR['TPS_Bqt'] + DR['TPS_Spesa'] + DR['TPS_Autres'] + DR['TPS_Internet']
AZ = DR['TVH']
AP = -(abs(DR['set_FD']) - AR['GuestFolios'])
CF = abs(DR['set_FD'])
col60 = abs(DR['set_AMEX'])
col61 = 0
col62 = abs(DR['set_MC']) + TRX_REST['MC']
col63 = abs(DR['set_Visa']) + TRX_REST['Visa']
col64 = abs(DR['set_Debit']) + TRX_REST['Debit']
col65 = TRX_REST['AMEX']
BQ = HP['AdminPourb']
BR = HP['PromoPourb']
BU = RECAP['ArgentRecu']
BV = RECAP['RembServeur']
BW = RECAP['PourbCharge']
BY = RECAP['DueBackRecept']
CA = RECAP['SurplusDeficit']

credits = {
    'J Piazza Nour': J, 'K Piazza Alcool': K, 'L Piazza Bieres': L, 'M Piazza Min': M, 'N Piazza Vin': N,
    'O Spesa Nour': O_col, 'AJ Tabagie': AJ, 'E Pause Spesa': E,
    'T SCh Nour': T, 'V SCh Biere': V, 'W SCh Min': W, 'X SCh Vin': X,
    'Y Bqt Nour': Y, 'AD Pourb': AD, 'AF Divers Bqt': AF, 'AG LocSalle': AG,
    'AK Chambres': AK, 'AO Nettoyeur': AO, 'AP GEAC comp': AP,
    'AS Autres GL': AS, 'AU Autre Rev': AU,
    'AW Internet': AW, 'AX TVQ': AX, 'AY TPS': AY, 'AZ TVH': AZ,
    'BF Diff Forfait': BF_ffait,
}

debits = {
    'BI Amex Elavon (60)': col60, 'BJ Discover (61)': col61,
    'BK MasterCard (62)': col62, 'BL Visa (63)': col63,
    'BM Debit (64)': col64, 'BN Amex Global (65)': col65,
    'BQ HP Admin Pourb': BQ, 'BR HP Promo Pourb': BR,
    'BU Argent Recu': BU, 'BV Remb Serveur': BV,
    'BW Pourb Charge': BW, 'BY Due Back Recept': BY,
    'CA Surplus/Deficit': CA, 'CF Transfer AR': CF,
}

sum_credits = sum(credits.values())
sum_debits = sum(debits.values())

print('=== CREDITS ===')
for k, v in credits.items():
    print(f'  {k:25s}: {v:>14,.2f}')
print(f'  {"TOTAL":25s}: {sum_credits:>14,.2f}')

print('\n=== DEBITS ===')
for k, v in debits.items():
    print(f'  {k:25s}: {v:>14,.2f}')
print(f'  {"TOTAL":25s}: {sum_debits:>14,.2f}')

bal_ferm_if_balanced = bal_ouv + sum_credits - sum_debits
implied_advdep = -bal_ferm_if_balanced - abs(DR['NewBalance'])

print('\n=== BALANCE ===')
print(f'  Bal_Ouv (Day 13 close): {bal_ouv:>14,.2f}')
print(f'  Bal_Ferm if DC=0:       {bal_ferm_if_balanced:>14,.2f}')
print(f'  |New Balance| (DR p.7): {abs(DR["NewBalance"]):>14,.2f}')
print(f'  Implied Adv Dep Today:  {implied_advdep:>14,.2f}')
print('\n  If Adv Dep on Hand Today matches ^ then DC = 0 cleanly.')
print('  If actual Adv Dep differs by $X, DC = -$X (residual to investigate).')
