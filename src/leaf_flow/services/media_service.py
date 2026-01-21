import base64
import binascii
import imghdr
import re
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
_BASE64_IMAGE_PATTERN = re.compile(r"^data:(image/(png|jpg|jpeg|webp));base64,", re.IGNORECASE)
_MIME_TO_EXTENSION = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/webp": ".webp",
}
_DETECTED_EXTENSION = {"jpeg": ".jpg", "png": ".png", "webp": ".webp"}


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


async def save_base64_image(image_base64: str, *, upload_dir: Path, public_prefix: str) -> str:
    normalized_data = image_base64.strip()
    match = _BASE64_IMAGE_PATTERN.match(normalized_data)

    try:
        encoded_content = normalized_data.split(",", 1)[1] if match else normalized_data
        content = base64.b64decode(encoded_content, validate=True)
    except (binascii.Error, IndexError) as exc:
        raise ValueError("INVALID_IMAGE_DATA") from exc

    if match:
        mime_type = match.group(1).lower()
        suffix = _MIME_TO_EXTENSION.get(mime_type)
    else:
        image_format = imghdr.what(None, h=content)
        suffix = _DETECTED_EXTENSION.get(image_format or "")

    if suffix not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError("UNSUPPORTED_IMAGE_TYPE")

    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{suffix}"
    destination = upload_dir / filename
    destination.write_bytes(content)

    public_prefix = public_prefix.rstrip("/") or "/"
    if public_prefix != "/":
        return f"{public_prefix}/{filename}"
    return f"/{filename}"
