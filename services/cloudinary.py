import cloudinary
import cloudinary.uploader
from config import settings

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET
)

def upload_avatar(file, username: str) -> str:
    result = cloudinary.uploader.upload(
        file,
        public_id=f"avatars/{username}",
        overwrite=True,
        resource_type="image"
    )
    return result["secure_url"]