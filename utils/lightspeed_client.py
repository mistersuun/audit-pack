"""
Lightspeed Galaxy PMS API Client.

Provides OAuth2-based integration with Lightspeed Galaxy PMS API,
replacing manual report parsing with direct API calls.

Reference: https://api-portal.lsk.lightspeed.app/

The client supports demo mode (returns sample data when not configured)
and full API mode (when credentials are provided).
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from functools import wraps
from flask import current_app

logger = logging.getLogger(__name__)


class LightspeedAPIError(Exception):
    """Base exception for Lightspeed API errors."""
    pass


class LightspeedAuthError(LightspeedAPIError):
    """Raised when authentication fails."""
    pass


class LightspeedConfigError(LightspeedAPIError):
    """Raised when configuration is missing."""
    pass


def demo_mode_fallback(func):
    """Decorator: Return demo data if API not configured, else call real API."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.is_configured():
            logger.info(f"Demo mode: {func.__name__} returning sample data")
            return self._get_demo_data(func.__name__, *args, **kwargs)
        try:
            return func(self, *args, **kwargs)
        except LightspeedAPIError:
            raise
        except Exception as e:
            logger.error(f"API call failed in {func.__name__}: {str(e)}")
            raise LightspeedAPIError(f"API call failed: {str(e)}")
    return wrapper


class LightspeedClient:
    """
    Galaxy Lightspeed PMS API client.

    Handles OAuth2 authentication and provides methods to fetch
    hotel data that currently requires manual report printing/parsing.

    All methods return structured dicts matching RJ Natif field expectations.
    When not configured (no credentials), demo mode returns sample data.
    """

    # Demo data for development/testing
    DEMO_DATA = {
        'daily_revenue': {
            'room_revenue': 15235.45,
            'fb_revenue': {
                'cafe': 1850.20,
                'piazza': 2340.50,
                'spesa': 456.75,
                'chambres_svc': 234.30,
                'banquet': 3120.00,
            },
            'other_revenue': 520.00,
            'total': 23757.20,
            'taxes': {
                'tps': 890.45,
                'tvq': 1870.35,
                'taxe_hebergement': 520.30,
            },
        },
        'room_statistics': {
            'rooms_sold': 185,
            'rooms_available': 252,
            'occupancy_pct': 73.4,
            'adr': 82.35,
            'revpar': 60.45,
            'arrivals': 45,
            'departures': 38,
            'house_count': 412,
        },
        'ar_balance': {
            'guest_ledger': 8450.35,
            'city_ledger': 12340.50,
            'advance_deposits': 5200.00,
            'total_ar': 26000.85,
        },
        'cashier_report': {
            'cash_cdn': 4520.50,
            'cash_usd': 3200.00,
            'credit_cards': {
                'visa': 8934.25,
                'mastercard': 5621.40,
                'amex': 2845.60,
                'debit': 3250.80,
            },
            'cheques': 1200.00,
        },
        'card_settlements': {
            'visa': 8934.25,
            'mastercard': 5621.40,
            'amex': 2845.60,
            'debit': 3250.80,
            'discover': 425.30,
            'total': 21077.35,
        },
        'market_segments': {
            'transient': {'rooms': 95, 'revenue': 8450.35},
            'group': {'rooms': 60, 'revenue': 5200.00},
            'contract': {'rooms': 20, 'revenue': 1340.50},
            'other': {'rooms': 10, 'revenue': 800.00},
        },
    }

    def __init__(self, config=None):
        """
        Initialize Lightspeed client.

        Args:
            config: Optional config dict with keys:
                - client_id: OAuth2 client ID
                - client_secret: OAuth2 client secret
                - property_id: Lightspeed property ID
                - base_url: API base URL (defaults to production)
                - token_cache_key: Redis/cache key for token storage

            If config is None, uses Flask config or environment variables.
        """
        self.config = config or {}
        self.client_id = self._get_config('LIGHTSPEED_CLIENT_ID')
        self.client_secret = self._get_config('LIGHTSPEED_CLIENT_SECRET')
        self.property_id = self._get_config('LIGHTSPEED_PROPERTY_ID')
        self.base_url = self._get_config('LIGHTSPEED_BASE_URL',
                                        'https://api.lsk.lightspeed.app')

        self._access_token = None
        self._token_expires_at = None
        self._property_name = None
        self._last_sync = None

    def _get_config(self, key, default=None):
        """Get config value from config dict, Flask config, or env."""
        if key in self.config:
            return self.config[key]
        try:
            return current_app.config.get(key, default)
        except RuntimeError:
            # Outside Flask context
            import os
            return os.getenv(key, default)

    def is_configured(self) -> bool:
        """Check if all required credentials are present."""
        return bool(self.client_id and self.client_secret and self.property_id)

    def is_connected(self) -> bool:
        """Check if currently authenticated and token is valid."""
        if not self.is_configured():
            return False
        if self._access_token is None:
            return False
        if self._token_expires_at is None:
            return False
        # Token valid if expires in > 1 minute
        return datetime.utcnow() < (self._token_expires_at - timedelta(minutes=1))

    def authenticate(self) -> bool:
        """
        Perform OAuth2 authentication.

        Obtains access token from Lightspeed API.

        Returns:
            True if authentication successful, False otherwise.

        Raises:
            LightspeedConfigError: If credentials not configured.
            LightspeedAuthError: If OAuth2 request fails.
        """
        if not self.is_configured():
            raise LightspeedConfigError(
                "Lightspeed credentials not configured. "
                "Set LIGHTSPEED_CLIENT_ID, LIGHTSPEED_CLIENT_SECRET, LIGHTSPEED_PROPERTY_ID."
            )

        try:
            auth_url = f"{self.base_url}/oauth/authorize"
            token_url = f"{self.base_url}/oauth/token"

            # Note: This is a simplified flow. Real implementation would need
            # to handle full OAuth2 authorization code flow with user consent.
            # For production, this should be part of the configuration flow.

            payload = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': 'api',
            }

            logger.info(f"Authenticating with Lightspeed API at {self.base_url}")
            response = requests.post(token_url, json=payload, timeout=10)
            response.raise_for_status()

            data = response.json()
            self._access_token = data.get('access_token')
            expires_in = data.get('expires_in', 3600)
            self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

            logger.info("Lightspeed authentication successful")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise LightspeedAuthError(f"OAuth2 failed: {str(e)}")

    def refresh_token(self) -> bool:
        """
        Refresh OAuth2 access token.

        Returns:
            True if refresh successful, False otherwise.
        """
        if not self.is_configured():
            return False

        try:
            token_url = f"{self.base_url}/oauth/token"
            payload = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
            }

            response = requests.post(token_url, json=payload, timeout=10)
            response.raise_for_status()

            data = response.json()
            self._access_token = data.get('access_token')
            expires_in = data.get('expires_in', 3600)
            self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

            logger.info("Token refreshed successfully")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Token refresh failed: {str(e)}")
            return False

    def _ensure_authenticated(self):
        """Ensure we have a valid token, refresh if needed."""
        if not self.is_connected():
            if not self.authenticate():
                raise LightspeedAuthError("Failed to obtain access token")

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make authenticated API request.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (relative to base_url)
            **kwargs: Additional requests parameters

        Returns:
            Response JSON dict

        Raises:
            LightspeedAPIError: If request fails
        """
        self._ensure_authenticated()

        url = f"{self.base_url}/api/v1{endpoint}"
        headers = {
            'Authorization': f'Bearer {self._access_token}',
            'Content-Type': 'application/json',
        }

        try:
            logger.debug(f"{method} {endpoint}")
            response = requests.request(
                method, url,
                headers=headers,
                timeout=30,
                **kwargs
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            raise LightspeedAPIError(f"Request timeout: {endpoint}")
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                # Token expired, try refresh
                if self.refresh_token():
                    return self._make_request(method, endpoint, **kwargs)
            raise LightspeedAPIError(f"HTTP {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            raise LightspeedAPIError(f"Request failed: {str(e)}")

    def _get_demo_data(self, method_name: str, *args, **kwargs) -> Dict[str, Any]:
        """Return demo data matching method name."""
        method_map = {
            'get_daily_revenue': 'daily_revenue',
            'get_room_statistics': 'room_statistics',
            'get_ar_balance': 'ar_balance',
            'get_cashier_report': 'cashier_report',
            'get_card_settlements': 'card_settlements',
            'get_market_segments': 'market_segments',
        }
        key = method_map.get(method_name, 'daily_revenue')
        return self.DEMO_DATA.get(key, {}).copy()

    # ─── DAILY REVENUE REPORT (replaces daily_revenue_parser) ───
    @demo_mode_fallback
    def get_daily_revenue(self, date: str) -> Dict[str, Any]:
        """
        Fetch daily revenue report.

        Maps to RJ Natif "jour" tab revenue sections.

        Args:
            date: Date string (YYYY-MM-DD)

        Returns:
            {
                'room_revenue': float,
                'fb_revenue': dict{cafe, piazza, spesa, chambres_svc, banquet},
                'other_revenue': float,
                'total': float,
                'taxes': dict{tps, tvq, taxe_hebergement},
                'sync_date': datetime ISO string,
            }
        """
        endpoint = f"/properties/{self.property_id}/reports/daily-revenue"
        params = {'date': date}
        data = self._make_request('GET', endpoint, params=params)

        result = {
            'room_revenue': self._safe_float(data.get('roomRevenue')),
            'fb_revenue': {
                'cafe': self._safe_float(data.get('cafeRevenue')),
                'piazza': self._safe_float(data.get('piazzaRevenue')),
                'spesa': self._safe_float(data.get('spesaRevenue')),
                'chambres_svc': self._safe_float(data.get('roomServiceRevenue')),
                'banquet': self._safe_float(data.get('banquetRevenue')),
            },
            'other_revenue': self._safe_float(data.get('otherRevenue')),
            'total': self._safe_float(data.get('totalRevenue')),
            'taxes': {
                'tps': self._safe_float(data.get('tpsAmount')),
                'tvq': self._safe_float(data.get('tvqAmount')),
                'taxe_hebergement': self._safe_float(data.get('accommodationTaxAmount')),
            },
            'sync_date': datetime.utcnow().isoformat(),
        }

        logger.info(f"Synced daily revenue for {date}: ${result['total']:.2f}")
        return result

    # ─── ROOM STATISTICS (replaces manual occupancy data) ───
    @demo_mode_fallback
    def get_room_statistics(self, date: str) -> Dict[str, Any]:
        """
        Fetch room statistics and occupancy data.

        Maps to RJ Natif "jour" tab occupation section and KPIs.

        Args:
            date: Date string (YYYY-MM-DD)

        Returns:
            {
                'rooms_sold': int,
                'rooms_available': int,
                'occupancy_pct': float (0-100),
                'adr': float (average daily rate),
                'revpar': float (revenue per available room),
                'arrivals': int,
                'departures': int,
                'house_count': int,
                'room_types': {simple, double, suite, comp},
                'sync_date': datetime ISO string,
            }
        """
        endpoint = f"/properties/{self.property_id}/reports/room-statistics"
        params = {'date': date}
        data = self._make_request('GET', endpoint, params=params)

        result = {
            'rooms_sold': int(data.get('roomsSold', 0)),
            'rooms_available': int(data.get('roomsAvailable', 252)),
            'occupancy_pct': self._safe_float(data.get('occupancyPercentage')),
            'adr': self._safe_float(data.get('averageDailyRate')),
            'revpar': self._safe_float(data.get('revenuePerAvailableRoom')),
            'arrivals': int(data.get('arrivals', 0)),
            'departures': int(data.get('departures', 0)),
            'house_count': int(data.get('houseguests', 0)),
            'room_types': {
                'simple': int(data.get('simpleRoomsOccupied', 0)),
                'double': int(data.get('doubleRoomsOccupied', 0)),
                'suite': int(data.get('suiteRoomsOccupied', 0)),
                'comp': int(data.get('complimentaryRooms', 0)),
            },
            'sync_date': datetime.utcnow().isoformat(),
        }

        logger.info(f"Synced room stats for {date}: {result['occupancy_pct']:.1f}% occupancy")
        return result

    # ─── AR BALANCE (replaces ar_summary_parser) ───
    @demo_mode_fallback
    def get_ar_balance(self, date: str) -> Dict[str, Any]:
        """
        Fetch accounts receivable balance.

        Maps to RJ Natif "recap" tab (deposit fields) and "geac" tab (AR).

        Args:
            date: Date string (YYYY-MM-DD)

        Returns:
            {
                'guest_ledger': float,
                'city_ledger': float,
                'advance_deposits': float,
                'total_ar': float,
                'ar_previous': float,
                'ar_charges': float,
                'ar_payments': float,
                'ar_new_balance': float,
                'sync_date': datetime ISO string,
            }
        """
        endpoint = f"/properties/{self.property_id}/reports/ar-balance"
        params = {'date': date}
        data = self._make_request('GET', endpoint, params=params)

        result = {
            'guest_ledger': self._safe_float(data.get('guestLedger')),
            'city_ledger': self._safe_float(data.get('cityLedger')),
            'advance_deposits': self._safe_float(data.get('advanceDeposits')),
            'total_ar': self._safe_float(data.get('totalAR')),
            'ar_previous': self._safe_float(data.get('previousBalance')),
            'ar_charges': self._safe_float(data.get('todaysCharges')),
            'ar_payments': self._safe_float(data.get('todaysPayments')),
            'ar_new_balance': self._safe_float(data.get('newBalance')),
            'sync_date': datetime.utcnow().isoformat(),
        }

        logger.info(f"Synced AR balance for {date}: ${result['total_ar']:.2f} total")
        return result

    # ─── CASH RECONCILIATION ───
    @demo_mode_fallback
    def get_cashier_report(self, date: str) -> Dict[str, Any]:
        """
        Fetch cashier report with cash and card totals.

        Maps to RJ Natif "recap" tab (cash/check fields).

        Args:
            date: Date string (YYYY-MM-DD)

        Returns:
            {
                'cash_cdn': float,
                'cash_usd': float,
                'credit_cards': {visa, mastercard, amex, debit},
                'cheques': float,
                'total': float,
                'sync_date': datetime ISO string,
            }
        """
        endpoint = f"/properties/{self.property_id}/reports/cashier"
        params = {'date': date}
        data = self._make_request('GET', endpoint, params=params)

        cards = data.get('creditCards', {})
        result = {
            'cash_cdn': self._safe_float(data.get('cashCDN')),
            'cash_usd': self._safe_float(data.get('cashUSD')),
            'credit_cards': {
                'visa': self._safe_float(cards.get('visa')),
                'mastercard': self._safe_float(cards.get('mastercard')),
                'amex': self._safe_float(cards.get('amex')),
                'debit': self._safe_float(cards.get('debit')),
            },
            'cheques': self._safe_float(data.get('checks')),
            'total': self._safe_float(data.get('total')),
            'sync_date': datetime.utcnow().isoformat(),
        }

        logger.info(f"Synced cashier report for {date}: ${result['total']:.2f}")
        return result

    # ─── CARD SETTLEMENTS (replaces freedompay_parser) ───
    @demo_mode_fallback
    def get_card_settlements(self, date: str) -> Dict[str, Any]:
        """
        Fetch card settlement totals.

        Maps to RJ Natif "transelect" and "geac" tabs.

        Args:
            date: Date string (YYYY-MM-DD)

        Returns:
            {
                'visa': float,
                'mastercard': float,
                'amex': float,
                'debit': float,
                'discover': float,
                'total': float,
                'sync_date': datetime ISO string,
            }
        """
        endpoint = f"/properties/{self.property_id}/reports/card-settlements"
        params = {'date': date}
        data = self._make_request('GET', endpoint, params=params)

        result = {
            'visa': self._safe_float(data.get('visa')),
            'mastercard': self._safe_float(data.get('mastercard')),
            'amex': self._safe_float(data.get('amex')),
            'debit': self._safe_float(data.get('debit')),
            'discover': self._safe_float(data.get('discover')),
            'total': self._safe_float(data.get('total')),
            'sync_date': datetime.utcnow().isoformat(),
        }

        logger.info(f"Synced card settlements for {date}: ${result['total']:.2f}")
        return result

    # ─── HOUSE GUESTS / NO-SHOWS ───
    @demo_mode_fallback
    def get_house_guests(self, date: str) -> List[Dict[str, Any]]:
        """
        Fetch guest list for a date.

        For future use in occupancy verification.

        Args:
            date: Date string (YYYY-MM-DD)

        Returns:
            List of {
                'name': str,
                'room': int,
                'rate': float,
                'arrival_date': date string,
                'departure_date': date string,
                'market_segment': str (transient|group|contract|comp),
            }
        """
        endpoint = f"/properties/{self.property_id}/reports/house-guests"
        params = {'date': date}
        data = self._make_request('GET', endpoint, params=params)

        guests = data.get('guests', [])
        result = [
            {
                'name': guest.get('name'),
                'room': int(guest.get('roomNumber', 0)),
                'rate': self._safe_float(guest.get('dailyRate')),
                'arrival_date': guest.get('arrivalDate'),
                'departure_date': guest.get('departureDate'),
                'market_segment': guest.get('marketSegment', 'transient'),
            }
            for guest in guests
        ]

        logger.info(f"Fetched {len(result)} house guests for {date}")
        return result

    # ─── NO-SHOW REPORT ───
    @demo_mode_fallback
    def get_no_shows(self, date: str) -> List[Dict[str, Any]]:
        """
        Fetch no-show list for a date.

        Maps to RJ Natif "dbrs" tab (no-show count and revenue).

        Args:
            date: Date string (YYYY-MM-DD)

        Returns:
            List of {
                'name': str,
                'confirmation': str,
                'rate': float,
                'market_segment': str,
            }
        """
        endpoint = f"/properties/{self.property_id}/reports/no-shows"
        params = {'date': date}
        data = self._make_request('GET', endpoint, params=params)

        noshows = data.get('noShows', [])
        result = [
            {
                'name': ns.get('name'),
                'confirmation': ns.get('confirmationNumber'),
                'rate': self._safe_float(ns.get('rate')),
                'market_segment': ns.get('marketSegment', 'transient'),
            }
            for ns in noshows
        ]

        logger.info(f"Fetched {len(result)} no-shows for {date}")
        return result

    # ─── MARKET SEGMENTS (for DBRS) ───
    @demo_mode_fallback
    def get_market_segments(self, date: str) -> Dict[str, Any]:
        """
        Fetch market segment breakdown.

        Maps to RJ Natif "dbrs" tab (market segments section).

        Args:
            date: Date string (YYYY-MM-DD)

        Returns:
            {
                'transient': {rooms: int, revenue: float},
                'group': {rooms: int, revenue: float},
                'contract': {rooms: int, revenue: float},
                'other': {rooms: int, revenue: float},
                'total_rooms': int,
                'total_revenue': float,
                'sync_date': datetime ISO string,
            }
        """
        endpoint = f"/properties/{self.property_id}/reports/market-segments"
        params = {'date': date}
        data = self._make_request('GET', endpoint, params=params)

        segments = data.get('segments', {})
        result = {
            'transient': {
                'rooms': int(segments.get('transient', {}).get('rooms', 0)),
                'revenue': self._safe_float(segments.get('transient', {}).get('revenue')),
            },
            'group': {
                'rooms': int(segments.get('group', {}).get('rooms', 0)),
                'revenue': self._safe_float(segments.get('group', {}).get('revenue')),
            },
            'contract': {
                'rooms': int(segments.get('contract', {}).get('rooms', 0)),
                'revenue': self._safe_float(segments.get('contract', {}).get('revenue')),
            },
            'other': {
                'rooms': int(segments.get('other', {}).get('rooms', 0)),
                'revenue': self._safe_float(segments.get('other', {}).get('revenue')),
            },
            'sync_date': datetime.utcnow().isoformat(),
        }

        # Calculate totals
        result['total_rooms'] = sum(s['rooms'] for s in result.values() if s != 'sync_date')
        result['total_revenue'] = sum(s['revenue'] for s in result.values() if s != 'sync_date')

        logger.info(f"Synced market segments for {date}")
        return result

    # ─── UTILITY METHODS ───
    @staticmethod
    def _safe_float(value, default=0.0) -> float:
        """Safely convert value to float."""
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def get_connection_status(self) -> Dict[str, Any]:
        """Get connection status for dashboard display."""
        return {
            'configured': self.is_configured(),
            'connected': self.is_connected(),
            'property_id': self.property_id,
            'property_name': self._property_name,
            'last_sync': self._last_sync.isoformat() if self._last_sync else None,
            'token_expires_at': self._token_expires_at.isoformat() if self._token_expires_at else None,
        }

    def test_connection(self) -> bool:
        """
        Test API connection with a simple call.

        Returns:
            True if connection successful, False otherwise.
        """
        if not self.is_configured():
            return False

        try:
            self.authenticate()
            logger.info("Connection test successful")
            return True
        except LightspeedAPIError as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False

    def disconnect(self):
        """Clear stored authentication state."""
        self._access_token = None
        self._token_expires_at = None
        logger.info("Disconnected from Lightspeed API")
