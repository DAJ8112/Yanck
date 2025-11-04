"""Cloud storage abstraction layer."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import BinaryIO

import boto3
from botocore.client import BaseClient

from app.core.config import settings


class S3StorageService:
    """Thin wrapper around boto3 S3 client for asynchronous usage."""

    def __init__(
        self,
        bucket_name: str,
        *,
        endpoint_url: str | None = None,
        region_name: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
    ) -> None:
        self.bucket_name = bucket_name
        self._client: BaseClient = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=region_name,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

    async def upload_fileobj(
        self,
        fileobj: BinaryIO,
        key: str,
        *,
        content_type: str | None = None,
        extra_args: dict | None = None,
    ) -> str:
        params = extra_args.copy() if extra_args else {}
        if content_type:
            params.setdefault("ContentType", content_type)

        await asyncio.to_thread(
            self._client.upload_fileobj,
            fileobj,
            self.bucket_name,
            key,
            ExtraArgs=params or None,
        )
        return key

    async def delete_object(self, key: str) -> None:
        await asyncio.to_thread(self._client.delete_object, Bucket=self.bucket_name, Key=key)

    async def download_file(self, key: str, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(
            self._client.download_file, self.bucket_name, key, str(destination)
        )
        return destination

    def generate_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": key},
            ExpiresIn=expires_in,
        )


def get_storage_service() -> S3StorageService:
    return S3StorageService(
        bucket_name=settings.s3_bucket_name,
        endpoint_url=settings.s3_endpoint_url,
        region_name=settings.s3_region,
        access_key=settings.s3_access_key,
        secret_key=settings.s3_secret_key,
    )


