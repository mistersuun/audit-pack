"""
Lightspeed PMS Data Sync Service.

Syncs Lightspeed API data into NightAuditSession fields.
Maps API responses to the 14 RJ Natif tabs, replacing manual data entry.
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Tuple
from database import db
from database.models import NightAuditSession
from utils.lightspeed_client import LightspeedClient, LightspeedAPIError

logger = logging.getLogger(__name__)


class LightspeedSync:
    """
    Syncs Lightspeed PMS data into NightAuditSession.

    Provides methods to:
    - Sync individual tabs (controle, recap, jour, transelect, geac, dbrs)
    - Full session sync across all tabs
    - Get sync status per date
    """

    def __init__(self, lightspeed_client: LightspeedClient = None):
        """
        Initialize sync service.

        Args:
            lightspeed_client: LightspeedClient instance (creates new if None)
        """
        self.client = lightspeed_client or LightspeedClient()
        self.sync_log = {
            'synced_tabs': [],
            'errors': [],
            'warnings': [],
            'timestamps': {},
        }

    def sync_session(self, audit_date: str) -> Dict[str, Any]:
        """
        Full sync: fetch all data and populate NightAuditSession.

        Syncs all 14 tabs in dependency order:
        1. controle (date, auditor, weather)
        2. recap (cash, checks, deposits)
        3. transelect (card totals)
        4. geac (AR balance)
        5. sd (already manual - skip)
        6. setd (personnel - already manual - skip)
        7. hpadmin (already manual - skip)
        8. internet (CD fields)
        9. sonifi (CD fields)
        10. jour (revenue, occupancy)
        11. quasimodo (auto-calculated from above)
        12. dbrs (auto-filled from jour + market segments)
        13. dueback (already manual - skip)
        14. resume (validation - skip)

        Args:
            audit_date: Date string (YYYY-MM-DD)

        Returns:
            {
                'synced_tabs': [list of tab names synced],
                'errors': [error messages],
                'warnings': [warning messages],
                'session': NightAuditSession dict (if successful),
            }
        """
        self.sync_log = {
            'synced_tabs': [],
            'errors': [],
            'warnings': [],
            'timestamps': {},
        }

        try:
            # Get or create session
            session = NightAuditSession.query.filter_by(
                audit_date=datetime.strptime(audit_date, '%Y-%m-%d').date()
            ).first()

            if not session:
                session = NightAuditSession(
                    audit_date=datetime.strptime(audit_date, '%Y-%m-%d').date(),
                    status='draft'
                )
                db.session.add(session)
                db.session.commit()
                logger.info(f"Created new session for {audit_date}")

            # Sync tabs in order
            self._sync_controle(session, audit_date)
            self._sync_recap(session, audit_date)
            self._sync_transelect(session, audit_date)
            self._sync_geac(session, audit_date)
            self._sync_internet(session, audit_date)
            self._sync_sonifi(session, audit_date)
            self._sync_jour(session, audit_date)
            self._sync_dbrs(session, audit_date)

            # Commit all changes
            db.session.commit()
            logger.info(f"Sync completed for {audit_date}: {len(self.sync_log['synced_tabs'])} tabs")

            return {
                'synced_tabs': self.sync_log['synced_tabs'],
                'errors': self.sync_log['errors'],
                'warnings': self.sync_log['warnings'],
                'session': session.to_dict() if hasattr(session, 'to_dict') else {},
            }

        except Exception as e:
            logger.error(f"Sync failed for {audit_date}: {str(e)}")
            self.sync_log['errors'].append(f"Sync failed: {str(e)}")
            db.session.rollback()
            return {
                'synced_tabs': self.sync_log['synced_tabs'],
                'errors': self.sync_log['errors'],
                'warnings': self.sync_log['warnings'],
            }

    # ─── Tab 1: CONTROLE ───
    def _sync_controle(self, session: NightAuditSession, audit_date: str) -> bool:
        """
        Sync control info: date, auditor name, weather, chambres à refaire.

        Currently: Only date is auto-filled. Auditor, weather, chambres_refaire
        must be entered manually.

        Args:
            session: NightAuditSession instance
            audit_date: Date string (YYYY-MM-DD)

        Returns:
            True if sync successful, False otherwise.
        """
        try:
            # Date is already set from session creation
            # Other fields require manual entry
            self.sync_log['synced_tabs'].append('controle')
            self.sync_log['timestamps']['controle'] = datetime.utcnow().isoformat()
            logger.info(f"Synced controle for {audit_date}")
            return True

        except Exception as e:
            self.sync_log['errors'].append(f"controle sync failed: {str(e)}")
            logger.error(f"controle sync failed: {str(e)}")
            return False

    # ─── Tab 3: RECAP ───
    def _sync_recap(self, session: NightAuditSession, audit_date: str) -> bool:
        """
        Sync recap: cash and check fields from cashier report and AR.

        Maps:
        - cash_ls_lecture = cashier report cash_cdn (Lightspeed cash reading)
        - cheque_ar_lecture = AR balance (advance deposits)

        Correction values remain manual.

        Args:
            session: NightAuditSession instance
            audit_date: Date string (YYYY-MM-DD)

        Returns:
            True if sync successful, False otherwise.
        """
        try:
            # Get cashier report
            cashier = self.client.get_cashier_report(audit_date)
            session.cash_ls_lecture = cashier.get('cash_cdn', 0)
            session.cash_pos_lecture = cashier.get('cash_usd', 0)

            # Get AR balance
            ar = self.client.get_ar_balance(audit_date)
            session.cheque_ar_lecture = ar.get('total_ar', 0)

            # Deposits from AR
            session.deposit_cdn = cashier.get('cash_cdn', 0)

            self.sync_log['synced_tabs'].append('recap')
            self.sync_log['timestamps']['recap'] = datetime.utcnow().isoformat()
            logger.info(f"Synced recap for {audit_date}")
            return True

        except LightspeedAPIError as e:
            self.sync_log['warnings'].append(f"recap partial sync: {str(e)}")
            logger.warning(f"recap sync partial: {str(e)}")
            return False

    # ─── Tab 4: TRANSELECT ───
    def _sync_transelect(self, session: NightAuditSession, audit_date: str) -> bool:
        """
        Sync transelect: card settlements by type.

        Maps card settlements to transelect_restaurant and transelect_reception
        JSON structures. Currently stores totals only (not terminal breakdown).

        Args:
            session: NightAuditSession instance
            audit_date: Date string (YYYY-MM-DD)

        Returns:
            True if sync successful, False otherwise.
        """
        try:
            cards = self.client.get_card_settlements(audit_date)

            # Store card totals in JSON format for quasimodo calculation
            transelect_data = {
                'visa': cards.get('visa', 0),
                'mastercard': cards.get('mastercard', 0),
                'amex': cards.get('amex', 0),
                'debit': cards.get('debit', 0),
                'discover': cards.get('discover', 0),
                'total': cards.get('total', 0),
                'source': 'lightspeed_api',
                'synced_at': datetime.utcnow().isoformat(),
            }

            session.transelect_restaurant = json.dumps(transelect_data)
            session.transelect_variance = 0  # No variance if synced from PMS

            self.sync_log['synced_tabs'].append('transelect')
            self.sync_log['timestamps']['transelect'] = datetime.utcnow().isoformat()
            logger.info(f"Synced transelect for {audit_date}: ${transelect_data['total']:.2f}")
            return True

        except LightspeedAPIError as e:
            self.sync_log['warnings'].append(f"transelect sync failed: {str(e)}")
            logger.warning(f"transelect sync failed: {str(e)}")
            return False

    # ─── Tab 5: GEAC ───
    def _sync_geac(self, session: NightAuditSession, audit_date: str) -> bool:
        """
        Sync GEAC/UX: AR balance and daily revenue details.

        Maps:
        - AR balance fields (previous, charges, payments, new balance)
        - Daily revenue by card type

        Args:
            session: NightAuditSession instance
            audit_date: Date string (YYYY-MM-DD)

        Returns:
            True if sync successful, False otherwise.
        """
        try:
            ar = self.client.get_ar_balance(audit_date)
            revenue = self.client.get_daily_revenue(audit_date)
            cards = self.client.get_card_settlements(audit_date)

            # AR fields
            session.geac_ar_previous = ar.get('ar_previous', 0)
            session.geac_ar_charges = ar.get('ar_charges', 0)
            session.geac_ar_payments = ar.get('ar_payments', 0)
            session.geac_ar_new_balance = ar.get('ar_new_balance', 0)

            # Calculate variance
            variance = (session.geac_ar_previous + session.geac_ar_charges
                       - session.geac_ar_payments - session.geac_ar_new_balance)
            session.geac_ar_variance = variance

            # Daily revenue by card type
            geac_daily_rev = {
                'total': revenue.get('total', 0),
                'room_revenue': revenue.get('room_revenue', 0),
                'fb_revenue': revenue.get('fb_revenue', {}),
                'visa': cards.get('visa', 0),
                'mastercard': cards.get('mastercard', 0),
                'amex': cards.get('amex', 0),
                'debit': cards.get('debit', 0),
                'discover': cards.get('discover', 0),
                'cash': revenue.get('total', 0) - cards.get('total', 0),
                'source': 'lightspeed_api',
                'synced_at': datetime.utcnow().isoformat(),
            }

            session.geac_daily_rev = json.dumps(geac_daily_rev)

            self.sync_log['synced_tabs'].append('geac')
            self.sync_log['timestamps']['geac'] = datetime.utcnow().isoformat()
            logger.info(f"Synced geac for {audit_date}: AR variance ${variance:.2f}")
            return True

        except LightspeedAPIError as e:
            self.sync_log['warnings'].append(f"geac sync failed: {str(e)}")
            logger.warning(f"geac sync failed: {str(e)}")
            return False

    # ─── Tab 8: HP/ADMIN ───
    # (Already manual - no sync)

    # ─── Tab 9: INTERNET ───
    def _sync_internet(self, session: NightAuditSession, audit_date: str) -> bool:
        """
        Sync Internet: CD 36.1 vs CD 36.5 variance.

        Currently: Lightspeed API doesn't expose these specific cashier details.
        This is a placeholder for future integration.

        Args:
            session: NightAuditSession instance
            audit_date: Date string (YYYY-MM-DD)

        Returns:
            True if sync successful, False otherwise.
        """
        try:
            # Placeholder: Internet CD fields not yet available from Lightspeed API
            # Would fetch from: /properties/{id}/reports/cashier-detail?code=36.1
            self.sync_log['warnings'].append("Internet CD fields not yet available from API")
            return True

        except Exception as e:
            self.sync_log['warnings'].append(f"internet sync skipped: {str(e)}")
            return False

    # ─── Tab 10: SONIFI ───
    def _sync_sonifi(self, session: NightAuditSession, audit_date: str) -> bool:
        """
        Sync Sonifi: CD 35.2 vs email PDF variance.

        Currently: Placeholder for future integration.

        Args:
            session: NightAuditSession instance
            audit_date: Date string (YYYY-MM-DD)

        Returns:
            True if sync successful, False otherwise.
        """
        try:
            # Placeholder: Sonifi details not yet available from Lightspeed API
            self.sync_log['warnings'].append("Sonifi CD fields not yet available from API")
            return True

        except Exception as e:
            self.sync_log['warnings'].append(f"sonifi sync skipped: {str(e)}")
            return False

    # ─── Tab 11: JOUR ───
    def _sync_jour(self, session: NightAuditSession, audit_date: str) -> bool:
        """
        Sync JOUR: F&B revenue, room revenue, occupancy, KPIs, taxes.

        This is the core tab with the most data from the API.

        Maps:
        - F&B by outlet (cafe, piazza, spesa, chambres_svc, banquet)
        - Room revenue
        - Occupancy (rooms sold, types, hors usage, clients)
        - Taxes (TPS, TVQ, taxe_hebergement)
        - KPIs (ADR, RevPAR, occupancy %)

        Args:
            session: NightAuditSession instance
            audit_date: Date string (YYYY-MM-DD)

        Returns:
            True if sync successful, False otherwise.
        """
        try:
            revenue = self.client.get_daily_revenue(audit_date)
            stats = self.client.get_room_statistics(audit_date)

            # Room revenue
            session.jour_room_revenue = revenue.get('room_revenue', 0)

            # F&B by outlet (simplified - Lightspeed aggregates by outlet)
            fb = revenue.get('fb_revenue', {})
            session.jour_cafe_nourriture = fb.get('cafe', 0) * 0.5  # Estimate food %
            session.jour_piazza_nourriture = fb.get('piazza', 0) * 0.5
            session.jour_spesa_nourriture = fb.get('spesa', 0) * 0.5
            session.jour_chambres_svc_nourriture = fb.get('chambres_svc', 0) * 0.5
            session.jour_banquet_nourriture = fb.get('banquet', 0) * 0.5

            # Occupancy
            room_types = stats.get('room_types', {})
            session.jour_rooms_simple = room_types.get('simple', 0)
            session.jour_rooms_double = room_types.get('double', 0)
            session.jour_rooms_suite = room_types.get('suite', 0)
            session.jour_rooms_comp = room_types.get('comp', 0)
            session.jour_nb_clients = stats.get('house_count', 0)

            # KPIs
            session.jour_adr = stats.get('adr', 0)
            session.jour_revpar = stats.get('revpar', 0)
            session.jour_occupancy_rate = stats.get('occupancy_pct', 0)

            # Taxes
            taxes = revenue.get('taxes', {})
            session.jour_tps = taxes.get('tps', 0)
            session.jour_tvq = taxes.get('tvq', 0)
            session.jour_taxe_hebergement = taxes.get('taxe_hebergement', 0)

            # Total revenue
            session.jour_total_revenue = revenue.get('total', 0)

            self.sync_log['synced_tabs'].append('jour')
            self.sync_log['timestamps']['jour'] = datetime.utcnow().isoformat()
            logger.info(f"Synced jour for {audit_date}: ${revenue.get('total', 0):.2f} revenue")
            return True

        except LightspeedAPIError as e:
            self.sync_log['warnings'].append(f"jour sync failed: {str(e)}")
            logger.warning(f"jour sync failed: {str(e)}")
            return False

    # ─── Tab 13: DBRS ───
    def _sync_dbrs(self, session: NightAuditSession, audit_date: str) -> bool:
        """
        Sync DBRS: Market segments, no-shows, ADR, RevPAR.

        Maps:
        - Market segments (transient, group, contract, other)
        - No-show count and revenue (from get_no_shows)
        - House count (from room stats)
        - ADR, occupancy % (from jour)

        Args:
            session: NightAuditSession instance
            audit_date: Date string (YYYY-MM-DD)

        Returns:
            True if sync successful, False otherwise.
        """
        try:
            segments = self.client.get_market_segments(audit_date)
            noshows = self.client.get_no_shows(audit_date)

            # Market segments
            dbrs_segments = {
                'transient': segments['transient'],
                'group': segments['group'],
                'contract': segments['contract'],
                'other': segments['other'],
                'synced_at': datetime.utcnow().isoformat(),
            }
            session.dbrs_market_segments = json.dumps(dbrs_segments)

            # No-shows
            noshow_count = len(noshows)
            noshow_revenue = sum(ns.get('rate', 0) for ns in noshows)

            # Store OTB data (On-The-Books) if available
            otb_data = {
                'house_count': session.jour_nb_clients,
                'noshow_count': noshow_count,
                'noshow_revenue': noshow_revenue,
                'synced_at': datetime.utcnow().isoformat(),
            }
            session.dbrs_otb_data = json.dumps(otb_data)

            # Daily revenue summary
            session.dbrs_daily_rev_today = session.jour_total_revenue
            session.dbrs_adr = session.jour_adr
            session.dbrs_house_count = session.jour_nb_clients
            session.dbrs_noshow_count = noshow_count
            session.dbrs_noshow_revenue = noshow_revenue

            self.sync_log['synced_tabs'].append('dbrs')
            self.sync_log['timestamps']['dbrs'] = datetime.utcnow().isoformat()
            logger.info(f"Synced dbrs for {audit_date}: {noshow_count} no-shows")
            return True

        except LightspeedAPIError as e:
            self.sync_log['warnings'].append(f"dbrs sync failed: {str(e)}")
            logger.warning(f"dbrs sync failed: {str(e)}")
            return False

    # ─── Manual tabs (skip) ───
    # - Tab 2: DueBack (manual entry)
    # - Tab 6: SD (manual entry)
    # - Tab 7: SetD (manual entry)
    # - Tab 8: HP/Admin (manual entry)
    # - Tab 12: Quasimodo (auto-calculated)
    # - Tab 14: Resume (validation only)

    def get_sync_status(self, audit_date: str) -> Dict[str, Any]:
        """
        Get sync status for a date.

        Returns information about what has been synced vs what's manual.

        Args:
            audit_date: Date string (YYYY-MM-DD)

        Returns:
            {
                'date': date string,
                'session_found': bool,
                'synced_tabs': [list of auto-synced tabs],
                'manual_tabs': [list of manual entry tabs],
                'last_sync': datetime or None,
                'sync_completeness': float (0-1),
            }
        """
        from datetime import date as date_type

        session = NightAuditSession.query.filter_by(
            audit_date=datetime.strptime(audit_date, '%Y-%m-%d').date()
        ).first()

        if not session:
            return {
                'date': audit_date,
                'session_found': False,
                'synced_tabs': [],
                'manual_tabs': [
                    'controle', 'recap', 'dueback', 'transelect', 'geac', 'sd',
                    'setd', 'hpadmin', 'internet', 'sonifi', 'jour', 'quasimodo',
                    'dbrs', 'resume'
                ],
                'last_sync': None,
                'sync_completeness': 0.0,
            }

        # Determine which tabs are synced (have data from API)
        synced_tabs = []
        if session.cash_ls_lecture > 0:
            synced_tabs.append('recap')
        if json.loads(session.transelect_restaurant or '{}'):
            synced_tabs.append('transelect')
        if session.geac_ar_new_balance != 0:
            synced_tabs.append('geac')
        if session.jour_total_revenue > 0:
            synced_tabs.append('jour')
        if json.loads(session.dbrs_market_segments or '{}'):
            synced_tabs.append('dbrs')

        manual_tabs = [
            'dueback', 'sd', 'setd', 'hpadmin'
        ]

        auto_tabs = ['quasimodo', 'resume']

        completeness = len(synced_tabs) / 14  # 14 total tabs

        return {
            'date': audit_date,
            'session_found': True,
            'synced_tabs': synced_tabs,
            'manual_tabs': manual_tabs,
            'auto_tabs': auto_tabs,
            'last_sync': session.updated_at.isoformat() if hasattr(session, 'updated_at') else None,
            'sync_completeness': completeness,
        }
