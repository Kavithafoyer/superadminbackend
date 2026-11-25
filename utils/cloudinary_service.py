import os
import logging
from django.conf import settings
from django.core.files.storage import default_storage

logger = logging.getLogger(__name__)

try:
    import cloudinary
    import cloudinary.uploader
    import cloudinary.api
    CLOUDINARY_AVAILABLE = True
except ImportError:
    CLOUDINARY_AVAILABLE = False
    logger.warning("Cloudinary package is not installed.")


def _get_setting(name, default=''):
    """Safely get setting from Django settings or environment."""
    try:
        if settings.configured:
            val = getattr(settings, name, None)
            if val:
                return val
    except Exception:
        pass
    return os.getenv(name, default) or ''


def get_cloudinary_config():
    """Retrieve and ensure Cloudinary configuration is active."""
    cloud_name = _get_setting('CLOUDINARY_CLOUD_NAME')
    api_key = _get_setting('CLOUDINARY_API_KEY')
    api_secret = _get_setting('CLOUDINARY_API_SECRET')
    cloudinary_url = _get_setting('CLOUDINARY_URL')

    if CLOUDINARY_AVAILABLE and (cloud_name or cloudinary_url):
        try:
            if cloudinary_url:
                os.environ['CLOUDINARY_URL'] = cloudinary_url
            cloudinary.config(
                cloud_name=cloud_name,
                api_key=api_key,
                api_secret=api_secret,
                secure=True
            )
            return True
        except Exception as e:
            logger.error(f"Error configuring Cloudinary: {e}")
            return False
    return False


def is_cloudinary_configured():
    """Check if Cloudinary credentials are fully present."""
    if not CLOUDINARY_AVAILABLE:
        return False
    cloud_name = _get_setting('CLOUDINARY_CLOUD_NAME')
    api_key = _get_setting('CLOUDINARY_API_KEY')
    api_secret = _get_setting('CLOUDINARY_API_SECRET')
    cloudinary_url = _get_setting('CLOUDINARY_URL')
    return bool((cloud_name and api_key and api_secret) or cloudinary_url)


def upload_image_to_cloudinary(file_obj, folder="addons", public_id=None, tags=None):
    """
    Upload a single image to Cloudinary.
    
    Args:
        file_obj: Django UploadedFile, file-like object, local path, or data URI.
        folder (str): Target folder in Cloudinary (e.g. 'addons').
        public_id (str, optional): Custom public ID for the asset.
        tags (list, optional): Metadata tags.

    Returns:
        dict: {
            "success": bool,
            "url": str (secure_url or fallback url),
            "secure_url": str,
            "public_id": str,
            "format": str,
            "width": int,
            "height": int,
            "fallback": bool
        }
    """
    if not file_obj:
        return {"success": False, "error": "No file provided"}

    # Attempt Cloudinary upload if configured
    if is_cloudinary_configured() and get_cloudinary_config():
        try:
            # If file has a read method, rewind to start
            if hasattr(file_obj, 'seek'):
                file_obj.seek(0)

            upload_options = {
                "folder": folder,
                "resource_type": "image",
                "overwrite": True,
            }
            if public_id:
                upload_options["public_id"] = public_id
            if tags:
                upload_options["tags"] = tags

            result = cloudinary.uploader.upload(file_obj, **upload_options)

            secure_url = result.get("secure_url") or result.get("url")
            return {
                "success": True,
                "url": secure_url,
                "secure_url": secure_url,
                "public_id": result.get("public_id"),
                "format": result.get("format"),
                "width": result.get("width"),
                "height": result.get("height"),
                "bytes": result.get("bytes"),
                "fallback": False
            }
        except Exception as e:
            logger.error(f"Cloudinary upload error: {e}. Falling back to default storage.")

    # Graceful Fallback to Django Default Storage (Local / S3)
    try:
        filename = getattr(file_obj, 'name', 'addon_image')
        # If file has a seek method, rewind to start
        if hasattr(file_obj, 'seek'):
            file_obj.seek(0)
        saved_path = default_storage.save(f"{folder}/{filename}", file_obj)
        local_url = default_storage.url(saved_path)
        return {
            "success": True,
            "url": local_url,
            "secure_url": local_url,
            "public_id": saved_path,
            "fallback": True
        }
    except Exception as e:
        logger.error(f"Fallback storage error: {e}")
        return {
            "success": False,
            "error": str(e),
            "fallback": True
        }


def upload_multiple_images_to_cloudinary(file_list, folder="addons"):
    """
    Upload multiple images to Cloudinary.
    
    Args:
        file_list (list): List of file objects.
        folder (str): Cloudinary folder.

    Returns:
        list[dict]: List of upload result dictionaries.
    """
    results = []
    if not file_list:
        return results

    for file_obj in file_list:
        res = upload_image_to_cloudinary(file_obj, folder=folder)
        results.append(res)
    return results


def delete_image_from_cloudinary(public_id, resource_type="image"):
    """
    Delete an image asset from Cloudinary by its public ID.
    """
    if not public_id or not is_cloudinary_configured():
        return {"success": False, "error": "Not configured or missing public_id"}

    try:
        get_cloudinary_config()
        res = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
        return {"success": res.get("result") == "ok", "result": res}
    except Exception as e:
        logger.error(f"Cloudinary delete error: {e}")
        return {"success": False, "error": str(e)}


def delete_multiple_from_cloudinary(public_ids, resource_type="image"):
    """
    Delete multiple image assets from Cloudinary.
    """
    if not public_ids or not is_cloudinary_configured():
        return {"success": False, "error": "Not configured or missing public_ids"}

    if isinstance(public_ids, str):
        public_ids = [public_ids]

    try:
        get_cloudinary_config()
        try:
            res = cloudinary.api.delete_resources(public_ids, resource_type=resource_type)
            return {"success": True, "result": res}
        except Exception:
            results = []
            for pid in public_ids:
                if pid:
                    results.append(delete_image_from_cloudinary(pid, resource_type=resource_type))
            return {"success": True, "results": results}
    except Exception as e:
        logger.error(f"Cloudinary batch delete error: {e}")
        return {"success": False, "error": str(e)}
