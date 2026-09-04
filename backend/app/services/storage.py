import asyncio

import boto3

from app.config import Settings


class StorageConfigurationError(RuntimeError):
    pass


def _client(settings: Settings):
    if not all(
        (
            settings.r2_endpoint_url,
            settings.r2_access_key_id,
            settings.r2_secret_access_key,
            settings.r2_bucket_name,
        )
    ):
        raise StorageConfigurationError("Cloudflare R2 storage is not configured")
    return boto3.client(
        "s3",
        endpoint_url=settings.r2_endpoint_url,
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
    )


async def put_file(key: str, content: bytes, content_type: str, settings: Settings) -> None:
    client = _client(settings)
    await asyncio.to_thread(
        client.put_object,
        Bucket=settings.r2_bucket_name,
        Key=key,
        Body=content,
        ContentType=content_type,
    )


async def create_download_url(key: str, settings: Settings) -> str:
    client = _client(settings)
    return await asyncio.to_thread(
        client.generate_presigned_url,
        "get_object",
        Params={"Bucket": settings.r2_bucket_name, "Key": key},
        ExpiresIn=settings.r2_presigned_expiry_seconds,
    )
