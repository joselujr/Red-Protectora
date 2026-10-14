import os
import time

import cloudinary
import cloudinary.api
import cloudinary.uploader
import cloudinary.utils
from cloudinary.exceptions import Error as CloudinaryError
from cloudinary.exceptions import NotFound as CloudinaryNotFound


MAX_BYTES = 10 * 1024 * 1024

# endpoint de subida directa desde el navegador (Vercel no admite peticiones de mas de 4,5 MB)
UPLOAD_URL = "https://api.cloudinary.com/v1_1/{cloud_name}/{resource_type}/upload"

CREDENTIALS = (
    "CLOUDINARY_CLOUD_NAME",
    "CLOUDINARY_API_KEY",
    "CLOUDINARY_API_SECRET",
)

ALLOWED_TYPES = {
    "image/jpeg": "image",
    "image/png": "image",
    "image/webp": "image",
    "video/mp4": "video",
    "video/quicktime": "video",
}

MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_VIDEO_BYTES = 50 * 1024 * 1024

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/quicktime"}

ALLOWED_IMAGE_FORMATS = ["jpg", "png"]
ALLOWED_VIDEO_FORMATS = ["mp4", "mov"]

# Error genérico al llamar a Cloudinary
class CloudinaryServiceError(Exception):
    pass

# Las credenciales o configuracion de .env no están completas
class CloudinaryConfigError(CloudinaryServiceError):
    pass

# Conectamos con coludinary pero devolvió un error
class CloudinaryUploadError(CloudinaryServiceError):
    pass

# Custom exception para raise haci arriba
class UploadMediaError(Exception):
    def __init__(self, message, status=400, provider_error=None):
        super().__init__(message)
        self.status = status
        self.provider_error = provider_error

# el fichero no cumple con lo que marcamos
class MediaValidationError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code


# validamos que tenemos los .env bien
def _missing_credentials():
    return [
        name
        for name in CREDENTIALS
        if not os.getenv(name, "").strip()
    ]


# Comprobar las variables
def upload_config():
    missing = _missing_credentials()
    return {
        "cloudinary_configured": not missing,
        "missing_variables": missing,
        "max_bytes": MAX_BYTES,
    }

def is_configured():
    return not _missing_credentials()


def configure():
    if _missing_credentials():
        raise CloudinaryConfigError("Faltan las credenciales de Cloudinary.")

    cloudinary.config(
        cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"].strip(),
        api_key=os.environ["CLOUDINARY_API_KEY"].strip(),
        api_secret=os.environ["CLOUDINARY_API_SECRET"].strip(),
        secure=True,
    )


MEDIA_LIMITS = {
    "image": (MAX_IMAGE_BYTES, ALLOWED_IMAGE_FORMATS),
    "video": (MAX_VIDEO_BYTES, ALLOWED_VIDEO_FORMATS),
}


def _check_size(size, max_bytes):
    if size <= 0:
        raise MediaValidationError("El archivo está vacío")

    if size > max_bytes:
        raise MediaValidationError("El archivo supera el tamaño máximo permitido")


# Comprueba el tipo y tamaño que declara el navegador antes de firmar la subida. Devuelve (media_format, allowed_formats)
def validate_media_meta(mimetype, size):
    if mimetype in ALLOWED_IMAGE_TYPES:
        media_format = "image"
    elif mimetype in ALLOWED_VIDEO_TYPES:
        media_format = "video"
    else:
        raise MediaValidationError("Formato de archivo no admitido")

    try:
        size = int(size)
    except (TypeError, ValueError):
        raise MediaValidationError("Tamaño de archivo inválido") from None

    max_bytes, allowed_formats = MEDIA_LIMITS[media_format]
    _check_size(size, max_bytes)

    return media_format, allowed_formats


# Revalida lo que realmente quedo subido en Cloudinary (el navegador podria haber mentido en la firma)
def validate_uploaded_resource(resource, media_format):
    max_bytes, allowed_formats = MEDIA_LIMITS[media_format]

    if resource.get("format") not in allowed_formats:
        raise MediaValidationError("Formato de archivo no admitido")

    _check_size(resource.get("bytes", 0), max_bytes)


# Firma los parametros para que el navegador suba el archivo directamente a Cloudinary.
# El navegador debe enviar exactamente los mismos "params" que se firman aqui.
def sign_upload(public_id, resource_type, allowed_formats, overwrite=False):
    configure()

    params = {
        "timestamp": str(int(time.time())),
        "public_id": public_id,
        "allowed_formats": ",".join(allowed_formats),
        "overwrite": "true" if overwrite else "false",
    }
    config = cloudinary.config()
    signature = cloudinary.utils.api_sign_request(params, config.api_secret)

    return {
        "upload_url": UPLOAD_URL.format(cloud_name=config.cloud_name, resource_type=resource_type),
        "resource_type": resource_type,
        "params": {**params, "api_key": config.api_key, "signature": signature},
    }


# Devuelve el recurso subido (bytes, format, secure_url, public_id) o None si no existe
def get_uploaded_resource(public_id, resource_type, timeout=30):
    configure()

    try:
        return cloudinary.api.resource(public_id, resource_type=resource_type, timeout=timeout)

    except CloudinaryNotFound:
        return None

    except CloudinaryError as error:
        raise CloudinaryUploadError(str(error)) from error


def delete_media(public_id, resource_type, invalidate=True, timeout=30):
    configure()

    try:
        result = cloudinary.uploader.destroy(
            public_id,
            resource_type=resource_type,
            invalidate=invalidate,
            timeout=timeout,
        )

    except CloudinaryError as error:
        raise CloudinaryUploadError(str(error)) from error

    return result.get("result") in ("ok", "not found")