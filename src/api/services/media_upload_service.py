import uuid

from api.services.cloudinary_service import (
    CloudinaryConfigError,
    CloudinaryServiceError,
    CloudinaryUploadError,
    MediaValidationError,
    delete_media,
    get_uploaded_resource,
    sign_upload,
    validate_media_meta,
    validate_uploaded_resource,
)
from api.utils import APIException

# Subida en dos pasos, comun a animales, necesidades y logo de protectora:
# 1. el backend valida tipo/tamaño declarados y firma la subida (sign_media_upload)
# 2. el navegador sube el archivo directamente a Cloudinary con esa firma
# 3. el backend comprueba en Cloudinary lo que se subio y lo registra (get_confirmed_media)

MEDIA_FORMATS = {"image", "video"}


def new_media_id():
    return str(uuid.uuid4())


# evita que el cliente meta rutas arbitrarias en el public_id
def parse_media_id(media_id):
    try:
        return str(uuid.UUID(str(media_id)))
    except ValueError:
        raise APIException("Identificador de archivo inválido", status_code=400) from None


def sign_media_upload(public_id, content_type, size, overwrite=False, images_only=False):
    try:
        media_format, allowed_formats = validate_media_meta(content_type, size)
    except MediaValidationError as error:
        raise APIException(str(error), status_code=error.status_code) from None

    if images_only and media_format != "image":
        raise APIException("Formato de archivo no admitido", status_code=400)

    try:
        return sign_upload(public_id, media_format, allowed_formats, overwrite=overwrite)
    except CloudinaryConfigError as error:
        raise APIException(str(error), status_code=503) from None


def get_confirmed_media(public_id, resource_type, images_only=False):
    if resource_type not in MEDIA_FORMATS or (images_only and resource_type != "image"):
        raise APIException("Formato de archivo no admitido", status_code=400)

    try:
        resource = get_uploaded_resource(public_id, resource_type)
    except CloudinaryConfigError as error:
        raise APIException(str(error), status_code=503) from None
    except CloudinaryUploadError as error:
        raise APIException(f"No se pudo comprobar el archivo en Cloudinary: {error}", status_code=502) from None

    if resource is None:
        raise APIException("No se ha encontrado el archivo subido", status_code=404)

    try:
        validate_uploaded_resource(resource, resource_type)
    except MediaValidationError as error:
        discard_media(public_id, resource_type)
        raise APIException(str(error), status_code=error.status_code) from None

    return resource


# intenta retirar un archivo subido que no se va a registrar; si falla no interrumpe el flujo
def discard_media(public_id, resource_type):
    try:
        delete_media(public_id, resource_type)
    except CloudinaryServiceError:
        pass
