# app/services/file_service.py
from io import BytesIO
from pathlib import Path
from typing import Tuple, Optional

from PIL import Image
from uuid import uuid4
from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.user import User

settings = get_settings()

def validate_image_file(contents: bytes,max_size_mb: int,resize_size: Tuple[int, int] = (400, 400),  # default resize size
) -> Image.Image:
    if len(contents) > max_size_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large")
    try:
        img = Image.open(BytesIO(contents))
        # ✅ Check for allowed formats
        if img.format not in ("JPEG", "JPG", "PNG", "WEBP"):
            raise HTTPException(status_code=400, detail="Unsupported image format")
        img = img.convert("RGB")
        img.thumbnail(resize_size)  # use the passed resize size here
        return img
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image format")

def save_image(image: Image.Image, subfolder: str) -> str:
    folder = Path(settings.IMAGE_UPLOAD_DIR) / subfolder
    folder.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}.jpg"
    try:
        image.save(folder / filename, format="JPEG", optimize=True, quality=85)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to save image") from e
    return f"{subfolder}/{filename}"

def delete_image(path: str):
    filepath = Path(settings.IMAGE_UPLOAD_DIR) / path
    print("file path before delete_image",filepath)
    if filepath.exists():
        filepath.unlink()

async def process_image_upload(
    file: UploadFile,
    max_size_mb: int,
    resize_size: Tuple[int, int],
    subdir: str,
    old_filename: Optional[str] = None
) -> str:
    # ✅ Check file content type
    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(status_code=400, detail="Invalid content type")

    contents = await file.read()
    image = validate_image_file(contents, max_size_mb, resize_size)

    if old_filename:
        delete_image(old_filename)

    return save_image(image, subdir)


async def process_user_profile_image_upload(
    file: UploadFile,
    current_user: User,
    session: AsyncSession,
    max_size_mb: int = 4,
    resize_size: Tuple[int, int] = (300, 300),
    subdir: str = "users"
) -> str:
    filename = await process_image_upload(
        file=file,
        max_size_mb=max_size_mb,
        resize_size=resize_size,
        subdir=subdir,
        old_filename=current_user.user_pic
    )
    current_user.user_pic = filename
    session.add(current_user)
    await session.commit()
    return filename