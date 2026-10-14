from sqlalchemy.exc import SQLAlchemyError

from api.models import db
from api.repositories.request_media_repository import RequestMediaRepository
from api.repositories.request_repository import RequestRepository
from api.services.cloudinary_service import (
    CloudinaryConfigError,
    CloudinaryUploadError,
    delete_media,
)
from api.services.media_upload_service import (
    discard_media,
    get_confirmed_media,
    new_media_id,
    parse_media_id,
    sign_media_upload,
)
from api.utils import APIException


def _get_owned_necesidad(request_id, shelter_id):
    necesidad = RequestRepository.get_by_request_id(request_id)

    if necesidad is None:
        raise APIException(
            "Necesidad no encontrada",
            status_code=404,
        )

    if necesidad.shelter_id != shelter_id:
        raise APIException(
            "No tienes permiso para modificar esta necesidad",
            status_code=403,
        )

    return necesidad


def _media_public_id(necesidad, media_id):
    return f"requests/{necesidad.request_id}/{media_id}"


# paso 1: firma la subida directa a Cloudinary
def prepare_necesidad_media_upload(request_id, shelter_id, content_type, size):
    necesidad = _get_owned_necesidad(request_id, shelter_id)

    media_id = new_media_id()
    signature = sign_media_upload(_media_public_id(necesidad, media_id), content_type, size)

    return {"media_id": media_id, **signature}


# paso 3: comprueba en Cloudinary lo subido y lo registra en la necesidad
def add_necesidad_media(request_id, shelter_id, media_id, resource_type, is_cover=False):
    necesidad = _get_owned_necesidad(request_id, shelter_id)
    media_id = parse_media_id(media_id)

    if RequestMediaRepository.get_by_media_id(media_id) is not None:
        raise APIException("Este archivo ya está registrado", status_code=409)

    resource = get_confirmed_media(_media_public_id(necesidad, media_id), resource_type)

    try:
        if is_cover:
            RequestMediaRepository.clear_cover(necesidad.id)

        media = RequestMediaRepository.create(
            media_id=media_id,
            request_id=necesidad.id,
            format=resource_type,
            url=resource["secure_url"],
            is_cover=bool(is_cover),
        )

        media.cloudinary_public_id = resource["public_id"]

        return RequestMediaRepository.save(media)

    except SQLAlchemyError:
        db.session.rollback()

        # Si falla la base de datos, intentar retirar el archivo subido.
        discard_media(resource["public_id"], resource_type)

        raise APIException(
            "No se pudo guardar el archivo en la base de datos.",
            status_code=500,
        ) from None


def delete_necesidad_media(request_id, media_id, shelter_id):
    necesidad = _get_owned_necesidad(request_id, shelter_id)

    media = RequestMediaRepository.get_by_media_id(media_id)

    if media is None or media.request_id != necesidad.id:
        raise APIException(
            "Recurso no encontrado",
            status_code=404,
        )

    if media.cloudinary_public_id:
        try:
            delete_media(
                media.cloudinary_public_id,
                media.format,
            )
        except CloudinaryConfigError as error:
            raise APIException(str(error), status_code=503) from None
        except CloudinaryUploadError as error:
            raise APIException(str(error), status_code=502) from None

    try:
        RequestMediaRepository.delete(media)

    except SQLAlchemyError:
        db.session.rollback()

        raise APIException(
            "No se pudo eliminar el registro. Inténtalo de nuevo.",
            status_code=500,
        ) from None


def set_necesidad_media_cover(request_id, media_id, shelter_id):
    necesidad = _get_owned_necesidad(request_id, shelter_id)

    media = RequestMediaRepository.get_by_media_id(media_id)

    if media is None or media.request_id != necesidad.id:
        raise APIException(
            "Recurso no encontrado",
            status_code=404,
        )

    try:
        RequestMediaRepository.clear_cover(necesidad.id)
        media.is_cover = True

        return RequestMediaRepository.save(media)

    except SQLAlchemyError:
        db.session.rollback()

        raise APIException(
            "No se pudo cambiar la imagen de portada.",
            status_code=500,
        ) from None