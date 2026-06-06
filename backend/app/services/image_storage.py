import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

CONTENT_TYPE_EXT = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
}


async def save_image_file(file: UploadFile, *, relative_dir: str) -> str:
    content_type = file.content_type or ""
    if content_type not in CONTENT_TYPE_EXT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Допустимы только изображения JPEG, PNG, GIF и WebP",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пустой файл")
    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Изображение слишком большое (макс. {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} МБ)",
        )

    upload_dir = Path(settings.UPLOAD_DIR) / relative_dir
    upload_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4()}{CONTENT_TYPE_EXT[content_type]}"
    (upload_dir / filename).write_bytes(content)

    return f"/uploads/{relative_dir}/{filename}"
