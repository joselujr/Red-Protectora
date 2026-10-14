from sqlalchemy.exc import SQLAlchemyError

from api.models import db
from api.repositories.animal_media_repository import AnimalMediaRepository
from api.repositories.animal_repository import AnimalRepository
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


def _get_owned_animal(animal_id, shelter_id):
    animal = AnimalRepository.get_by_animal_id(animal_id)

    if animal is None:
        raise APIException(
            "Animal no encontrado",
            status_code=404,
        )

    if animal.shelter_id != shelter_id:
        raise APIException(
            "No tienes permiso para modificar este animal",
            status_code=403,
        )

    return animal


def _media_public_id(animal, media_id):
    return f"animals/{animal.animal_id}/{media_id}"


# paso 1: firma la subida directa a Cloudinary
def prepare_animal_media_upload(animal_id, shelter_id, content_type, size):
    animal = _get_owned_animal(animal_id, shelter_id)

    media_id = new_media_id()
    signature = sign_media_upload(_media_public_id(animal, media_id), content_type, size)

    return {"media_id": media_id, **signature}


# paso 3: comprueba en Cloudinary lo subido y lo registra en la ficha del animal
def add_animal_media(animal_id, shelter_id, media_id, resource_type, is_cover=False):
    animal = _get_owned_animal(animal_id, shelter_id)
    media_id = parse_media_id(media_id)

    if AnimalMediaRepository.get_by_media_id(media_id) is not None:
        raise APIException("Este archivo ya está registrado", status_code=409)

    resource = get_confirmed_media(_media_public_id(animal, media_id), resource_type)

    try:
        if is_cover:
            AnimalMediaRepository.clear_cover(animal.id)

        media = AnimalMediaRepository.create(
            media_id=media_id,
            animal_id=animal.id,
            format=resource_type,
            url=resource["secure_url"],
            cloudinary_public_id=resource["public_id"],
            is_cover=bool(is_cover),
        )

        return AnimalMediaRepository.save(media)

    except SQLAlchemyError:
        db.session.rollback()

        # Si falla la base de datos, intentar retirar el archivo subido.
        discard_media(resource["public_id"], resource_type)

        raise APIException(
            "No se pudo guardar el archivo en la base de datos.",
            status_code=500,
        ) from None


def delete_animal_media(animal_id, media_id, shelter_id):
    animal = _get_owned_animal(animal_id, shelter_id)

    media = AnimalMediaRepository.get_by_media_id(media_id)

    if media is None or media.animal_id != animal.id:
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
        AnimalMediaRepository.delete(media)
    except SQLAlchemyError:
        db.session.rollback()
        raise APIException(
            "No se pudo eliminar el registro. Inténtalo de nuevo.",
            status_code=500,
        ) from None


def set_animal_media_cover(animal_id, media_id, shelter_id):
    animal = _get_owned_animal(animal_id, shelter_id)

    media = AnimalMediaRepository.get_by_media_id(media_id)

    if media is None or media.animal_id != animal.id:
        raise APIException(
            "Recurso no encontrado",
            status_code=404,
        )

    try:
        AnimalMediaRepository.clear_cover(animal.id)
        media.is_cover = True
        return AnimalMediaRepository.save(media)

    except SQLAlchemyError:
        db.session.rollback()
        raise APIException(
            "No se pudo cambiar la imagen de portada.",
            status_code=500,
        ) from None
