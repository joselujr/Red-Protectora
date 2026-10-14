from flask import jsonify, request
from flask_jwt_extended import jwt_required

from api.services.request_media_service import (
    add_necesidad_media,
    delete_necesidad_media,
    prepare_necesidad_media_upload,
    set_necesidad_media_cover,
)
from api.utils import APIException

from . import api
from .auth import get_current_user


def _require_shelter_user():
    user = get_current_user()
    if not user.shelter_id:
        raise APIException("El usuario no pertenece a ninguna protectora", status_code=403)
    return user


# ######################
# ruta para firmar la subida directa a Cloudinary de una foto o video de la necesidad (solo su protectora)
# ######################
@api.route('/shelter/requests/<request_id>/media/upload-signature', methods=['POST'])
@jwt_required()
def sign_necesidad_media_upload_action(request_id):
    user = _require_shelter_user()

    data = request.get_json(silent=True) or {}
    signature = prepare_necesidad_media_upload(request_id, user.shelter_id, data.get('content_type'), data.get('size'))
    return jsonify(signature), 200


# ######################
# ruta para registrar en la necesidad la foto o video ya subido a Cloudinary
# ######################
@api.route('/shelter/requests/<request_id>/media', methods=['POST'])
@jwt_required()
def add_necesidad_media_action(request_id):
    user = _require_shelter_user()

    data = request.get_json(silent=True) or {}
    media = add_necesidad_media(request_id, user.shelter_id, data.get('media_id'), data.get('resource_type'),
                                is_cover=bool(data.get('is_cover')))
    return jsonify(media.serialize()), 201


# ######################
# ruta para eliminar una foto o video de una necesidad
# ######################
@api.route('/shelter/requests/<request_id>/media/<media_id>', methods=['DELETE'])
@jwt_required()
def delete_necesidad_media_action(request_id, media_id):
    user = _require_shelter_user()
    delete_necesidad_media(request_id, media_id, user.shelter_id)
    return jsonify({"success": True}), 200


# ######################
# ruta para marcar una foto o video ya subido como portada
# ######################
@api.route('/shelter/requests/<request_id>/media/<media_id>/cover', methods=['POST'])
@jwt_required()
def set_necesidad_media_cover_action(request_id, media_id):
    user = _require_shelter_user()
    media = set_necesidad_media_cover(request_id, media_id, user.shelter_id)
    return jsonify(media.serialize()), 200
