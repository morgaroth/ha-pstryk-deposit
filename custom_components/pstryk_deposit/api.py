"""JWT session client for Pstryk private API."""
import asyncio
import logging
from typing import Any, Optional

import aiohttp

from .const import API_BASE_URL, API_AUTH_TOKEN, API_AUTH_TOKEN_REFRESH, API_PROSUMER_DEPOSIT

_LOGGER = logging.getLogger(__name__)
_TIMEOUT = aiohttp.ClientTimeout(total=20)


class PstrykAuthError(Exception):
    pass


class PstrykApiError(Exception):
    pass


class PstrykJwtClient:
    """Manages JWT session for Pstryk private endpoints."""

    def __init__(self, email: str, password: str, session: aiohttp.ClientSession) -> None:
        self._email = email
        self._password = password
        self._session = session
        self._access: Optional[str] = None
        self._refresh: Optional[str] = None

    async def _login(self) -> None:
        url = f"{API_BASE_URL}{API_AUTH_TOKEN}"
        _LOGGER.debug("Attempting login to %s with email: %s", url, self._email)
        try:
            async with self._session.post(
                url,
                json={"email": self._email, "password": self._password},
                headers={"Content-Type": "application/json"},
                timeout=_TIMEOUT,
            ) as resp:
                _LOGGER.debug("Login response status: %d", resp.status)
                _LOGGER.debug("Login response headers: %s", dict(resp.headers))
                if resp.status in (400, 401, 403):
                    text = await resp.text()
                    _LOGGER.error("Login failed (%d): %s", resp.status, text[:500])
                    raise PstrykAuthError(f"Login failed ({resp.status}): {text[:200]}")
                resp.raise_for_status()
                data = await resp.json()
                _LOGGER.debug("Login successful, received tokens (access=%s, refresh=%s)",
                              "yes" if data.get("access") else "no",
                              "yes" if data.get("refresh") else "no")
                self._access = data["access"]
                self._refresh = data.get("refresh")
        except aiohttp.ClientError as err:
            _LOGGER.error("Network error during login: %s", err)
            raise PstrykApiError(f"Network error during login: {err}") from err

    async def _do_refresh(self) -> bool:
        if not self._refresh:
            return False
        url = f"{API_BASE_URL}{API_AUTH_TOKEN_REFRESH}"
        try:
            async with self._session.post(
                url,
                json={"refresh": self._refresh},
                headers={"Content-Type": "application/json"},
                timeout=_TIMEOUT,
            ) as resp:
                if resp.status in (400, 401, 403):
                    return False
                resp.raise_for_status()
                data = await resp.json()
                self._access = data["access"]
                if "refresh" in data:
                    self._refresh = data["refresh"]
                return True
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return False

    async def _ensure_token(self) -> str:
        if not self._access:
            await self._login()
        return self._access

    async def _request(self, method: str, path: str) -> Any:
        token = await self._ensure_token()
        url = f"{API_BASE_URL}{path}"
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

        async with self._session.request(method, url, headers=headers, timeout=_TIMEOUT) as resp:
            if resp.status == 401:
                # try refresh then retry
                if not await self._do_refresh():
                    await self._login()
                token = self._access
                headers["Authorization"] = f"Bearer {token}"
                async with self._session.request(method, url, headers=headers, timeout=_TIMEOUT) as retry:
                    if retry.status in (401, 403):
                        raise PstrykAuthError(f"Request failed after re-auth ({retry.status})")
                    retry.raise_for_status()
                    return await retry.json()
            resp.raise_for_status()
            return await resp.json()

    async def test_auth(self) -> bool:
        """Test login credentials. Returns True on success."""
        try:
            await self._login()
            _LOGGER.debug("test_auth: login succeeded")
            return True
        except PstrykAuthError as err:
            _LOGGER.error("test_auth failed (auth): %s", err)
            return False
        except PstrykApiError as err:
            _LOGGER.error("test_auth failed (api/network): %s", err)
            return False
        except Exception as err:
            _LOGGER.exception("test_auth failed (unexpected): %s", err)
            return False

    async def get_prosumer_deposit(self) -> dict:
        """Fetch prosumer deposit balance and transactions."""
        return await self._request("GET", API_PROSUMER_DEPOSIT)
