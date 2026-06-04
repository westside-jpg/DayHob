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
        resource_type="image",
        transformation=[
            {"width": 300, "height": 300, "crop": "fill", "gravity": "face"},
            {"quality": "auto", "fetch_format": "auto"}
        ]
    )
    return result["secure_url"]

def upload_photo(file, user_post_id: str, username: str) -> str:
    result = cloudinary.uploader.upload(
        file,
        public_id=f"posts/{username}/{user_post_id}",
        overwrite=True,
        resource_type="image",
        transformation=[
            {
                "width": 1920,
                "height": 1920,
                "crop": "limit"
            },
            {
                "quality": "auto",
                "fetch_format": "auto"
            }
        ]
    )
    return result["secure_url"]

def delete_avatar(username: str) -> None:
    public_id = f"avatars/{username}"
    cloudinary.uploader.destroy(public_id, resource_type="image")