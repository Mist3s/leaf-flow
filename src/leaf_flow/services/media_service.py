from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


async def save_image(upload: UploadFile, *, upload_dir: Path, public_prefix: str) -> str:
    suffix = Path(upload.filename or "").suffix.lower()
    if suffix not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError("UNSUPPORTED_IMAGE_TYPE")

    upload_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid4().hex}{suffix}"
    destination = upload_dir / filename
    content = await upload.read()
    destination.write_bytes(content)

    public_prefix = public_prefix.rstrip("/") or "/"
    if public_prefix != "/":
        return f"{public_prefix}/{filename}"
    return f"/{filename}"
