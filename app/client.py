from typing import Any, Dict

import httpx
from fastapi import HTTPException, status

from app.config import settings


class DirectoryAPIClient:
    def __init__(self) -> None:
        self._base_url = settings.directory_api_base_url
        self._timeout = settings.request_timeout_seconds

    async def create_hospital(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request("POST", "/hospitals/", json=payload)

    async def activate_batch(self, batch_id: str) -> Dict[str, Any]:
        return await self._request("PATCH", f"/hospitals/batch/{batch_id}/activate")

    async def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        url = f"{self._base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.request(method, url, **kwargs)
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Could not reach Hospital Directory API: {exc}",
            ) from exc

        if response.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Hospital Directory API error ({response.status_code}): {response.text}",
            )

        return response.json()


directory_client = DirectoryAPIClient()
