from __future__ import annotations

import json
import os
import uuid
import mimetypes
from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import AppException


def _client() -> httpx.Client:
    return httpx.Client(timeout=settings.HTTP_CLIENT_TIMEOUT_SEC)


def _s3_enabled() -> bool:
    return bool(
        (settings.AWS_S3_BUCKET or "").strip()
        and (settings.AWS_PUBLIC_BASE_URL or "").strip()
        and (settings.AWS_REGION or "").strip()
        and (settings.AWS_ACCESS_KEY_ID or "").strip()
        and (settings.AWS_SECRET_ACCESS_KEY or "").strip()
    )


def _s3_public_url_for_key(key: str) -> str:
    base = (settings.AWS_PUBLIC_BASE_URL or "").strip().rstrip("/")
    k = key.lstrip("/")
    return f"{base}/{k}"


def _s3_put_bytes(*, key: str, data: bytes, filename: str, content_type: str | None) -> str:
    # Local import so the service still boots when boto3 isn't installed.
    import boto3  # type: ignore

    guessed, _ = mimetypes.guess_type(filename)
    ct = content_type or guessed or "application/octet-stream"
    s3 = boto3.client(
        "s3",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    s3.put_object(
        Bucket=settings.AWS_S3_BUCKET,
        Key=key,
        Body=data,
        ContentType=ct,
    )
    return _s3_public_url_for_key(key)


def validate_user_exists(user_id: str) -> None:
    base = settings.USER_MS_BASE_URL.strip()
    if not base:
        return
    path = settings.USER_MS_VALIDATE_PATH
    url = f"{base.rstrip('/')}{path}"
    headers: dict[str, str] = {}
    key = settings.USER_MS_INTERNAL_API_KEY.strip()
    if key:
        headers["X-Internal-Api-Key"] = key
    try:
        with _client() as c:
            r = c.post(url, json={"user_id": user_id}, headers=headers)
    except httpx.RequestError as e:
        raise AppException("User service unavailable", status_code=503) from e
    if r.status_code == 401:
        raise AppException("User service unauthorized", status_code=503)
    if r.status_code >= 400:
        raise AppException("User not found", status_code=404)
    try:
        data = r.json()
    except json.JSONDecodeError as e:
        raise AppException("User not found", status_code=404) from e
    if not data.get("valid"):
        raise AppException("User not found", status_code=404)


def upload_via_media_ms(file_bytes: bytes, filename: str, content_type: str | None) -> str:
    base = settings.MEDIA_MS_BASE_URL.strip()
    if not base:
        raise AppException("Media service is not configured", status_code=500)
    url = f"{base.rstrip('/')}{settings.MEDIA_MS_UPLOAD_PATH}"
    files = {"file": (filename, file_bytes, content_type or "application/octet-stream")}
    try:
        with _client() as c:
            r = c.post(url, files=files)
    except httpx.RequestError as e:
        raise AppException("Upload failed", status_code=400) from e
    if r.status_code >= 400:
        raise AppException("Upload failed", status_code=400)
    try:
        data = r.json()
    except json.JSONDecodeError as e:
        raise AppException("Upload failed", status_code=400) from e
    url_out = data.get("url") or data.get("image_url")
    if not url_out:
        raise AppException("Upload failed", status_code=400)
    return str(url_out)


def save_upload_locally(subdir: str, file_bytes: bytes, filename: str) -> str:
    root = os.path.abspath(settings.LOCAL_UPLOAD_DIR)
    safe_name = f"{uuid.uuid4().hex}_{os.path.basename(filename) or 'file'}"
    dest_dir = os.path.join(root, subdir)
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, safe_name)
    with open(dest_path, "wb") as f:
        f.write(file_bytes)
    rel = f"/uploads/{subdir}/{safe_name}".replace("\\", "/")
    return f"{settings.PUBLIC_APP_URL.rstrip('/')}{rel}"


def resolve_upload_url(file_bytes: bytes, filename: str, content_type: str | None) -> str:
    if _s3_enabled():
        prefix = (settings.AWS_UPLOAD_PREFIX or "").strip()
        if prefix and not prefix.endswith("/"):
            prefix += "/"
        safe = f"{uuid.uuid4().hex}_{os.path.basename(filename) or 'file'}"
        key = f"{prefix}media/{safe}"
        try:
            return _s3_put_bytes(key=key, data=file_bytes, filename=filename, content_type=content_type)
        except ModuleNotFoundError as e:
            raise AppException("Upload failed (missing boto3)", status_code=500) from e

    if settings.MEDIA_MS_BASE_URL.strip():
        return upload_via_media_ms(file_bytes, filename, content_type)
    return save_upload_locally("media", file_bytes, filename)


def fetch_vehicle_tracking(vehicle_id: str) -> dict[str, Any]:
    base = settings.TRACKING_MS_BASE_URL.strip()
    if not base:
        raise AppException("Unavailable", status_code=500)
    path = settings.TRACKING_MS_VEHICLE_PATH.format(vehicle_id=vehicle_id)
    url = f"{base.rstrip('/')}{path}"
    try:
        with _client() as c:
            r = c.get(url)
    except httpx.RequestError as e:
        raise AppException("Unavailable", status_code=500) from e
    if r.status_code >= 400:
        raise AppException("Unavailable", status_code=500)
    try:
        return dict(r.json())
    except json.JSONDecodeError as e:
        raise AppException("Unavailable", status_code=500) from e


def ticket_create(vehicle_id: str) -> dict[str, Any]:
    base = settings.TICKET_MS_BASE_URL.strip()
    if not base:
        raise AppException("Failed", status_code=400)
    url = f"{base.rstrip('/')}{settings.TICKET_MS_CREATE_PATH}"
    try:
        with _client() as c:
            r = c.post(url, json={"vehicle_id": vehicle_id})
    except httpx.RequestError as e:
        raise AppException("Failed", status_code=400) from e
    if r.status_code >= 400:
        raise AppException("Failed", status_code=400)
    try:
        return dict(r.json())
    except json.JSONDecodeError as e:
        raise AppException("Failed", status_code=400) from e


def ticket_approve(ticket_id: str, status: str) -> None:
    base = settings.TICKET_MS_BASE_URL.strip()
    if not base:
        raise AppException("Invalid", status_code=400)
    url = f"{base.rstrip('/')}{settings.TICKET_MS_APPROVE_PATH}"
    try:
        with _client() as c:
            r = c.post(url, json={"ticket_id": ticket_id, "status": status})
    except httpx.RequestError as e:
        raise AppException("Invalid", status_code=400) from e
    if r.status_code >= 400:
        raise AppException("Invalid", status_code=400)


def analytics_vehicle_summary(vehicle_id: str) -> dict[str, Any]:
    base = settings.ANALYTICS_MS_BASE_URL.strip()
    if not base:
        raise AppException("Failed", status_code=500)
    path = settings.ANALYTICS_MS_VEHICLE_SUMMARY_PATH
    url = f"{base.rstrip('/')}{path}"
    try:
        with _client() as c:
            r = c.get(url, params={"vehicle_id": vehicle_id})
    except httpx.RequestError as e:
        raise AppException("Failed", status_code=500) from e
    if r.status_code >= 400:
        raise AppException("Failed", status_code=500)
    try:
        return dict(r.json())
    except json.JSONDecodeError as e:
        raise AppException("Failed", status_code=500) from e


def proxy_media_upload(file_bytes: bytes, filename: str, content_type: str | None) -> str:
    """Generic media upload: Media MS if configured, else local storage."""
    return resolve_upload_url(file_bytes, filename, content_type)
