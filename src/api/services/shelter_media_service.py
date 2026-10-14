from sqlalchemy.exc import SQLAlchemyError

from api.models import db
from api.repositories.shelter_repository import ShelterRepository
from api.services.cloudinary_service import (
    CloudinaryConfigError,
    CloudinaryUploadError,
    delete_media,
)
from api.services.media_upload_service import (
    discard_media,
    get_confirmed_media,
    sign_media_upload,
)
from api.utils import APIException


def _get_owned_shelter(shelter_pk):
    shelter = ShelterRepository.get_by_id(shelter_pk)
    if shelter is None:
        raise APIException("Protectora no encontrada", status_code=404)
    return shelter


def _logo_public_id(shelter):
    return f"shelters/{shelter.shelter_id}/logo"


def _borrar_logo_actual(shelter):
    if not shelter.logo_url:
        return

    try:
        delete_media(_logo_public_id(shelter), "image")
    except CloudinaryConfigError as error:
        raise APIException(str(error), status_code=503) from None
    except CloudinaryUploadError as error:
        raise APIException(str(error), status_code=502) from None


# paso 1: firma la subida directa del logo a Cloudinary.
# No hace falta borrar antes: overwrite=true sustituye el logo anterior en la misma subida.
def prepare_shelter_logo_upload(shelter_pk, content_type, size):
    shelter = _get_owned_shelter(shelter_pk)
    return sign_media_upload(_logo_public_id(shelter), content_type, size, overwrite=True, images_only=True)


# paso 3: comprueba en Cloudinary el logo subido y lo guarda en la protectora
def add_shelter_logo(shelter_pk):
    shelter = _get_owned_shelter(shelter_pk)
    resource = get_confirmed_media(_logo_public_id(shelter), "image", images_only=True)

    try:
        shelter.logo_url = resource["secure_url"]
        return ShelterRepository.save(shelter)

    except SQLAlchemyError:
        db.session.rollback()

        # Si falla la base de datos, intentar retirar el archivo subido.
        discard_media(resource["public_id"], "image")

        raise APIException(
            "No se pudo guardar el logo en la base de datos.",
            status_code=500,
        ) from None


def delete_shelter_logo(shelter_pk):
    shelter = _get_owned_shelter(shelter_pk)

    _borrar_logo_actual(shelter)
    shelter.logo_url = None
    return ShelterRepository.save(shelter)
