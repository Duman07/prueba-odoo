import json
from urllib.parse import quote

from odoo import http
from odoo.http import request

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

# Extensión → tipo MIME de los archivos aceptados por los bloques de moto.
# SVG queda fuera a propósito: se sirve desde el mismo dominio y puede contener scripts.
ALLOWED_TYPES = {
    "glb": "model/gltf-binary",
    "gltf": "model/gltf+json",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
    "gif": "image/gif",
    "avif": "image/avif",
}
ALLOWED_LABEL = ".glb, .gltf, .png, .jpg, .webp, .gif o .avif"


def _is_embedded_gltf(data):
    """Un .gltf solo funciona subido si lleva sus buffers e imágenes incrustados (data:)."""
    try:
        gltf = json.loads(data)
    except ValueError:
        return False
    if not isinstance(gltf, dict) or "asset" not in gltf:
        return False
    resources = gltf.get("buffers", []) + gltf.get("images", [])
    return all(
        isinstance(item, dict) and ("uri" not in item or str(item["uri"]).startswith("data:"))
        for item in resources
    )


def _content_matches(extension, data):
    """Comprueba la firma del archivo para no aceptar contenido con una extensión falsa."""
    if extension == "glb":
        return data.startswith(b"glTF")
    if extension == "gltf":
        return _is_embedded_gltf(data)
    if extension == "png":
        return data.startswith(b"\x89PNG\r\n\x1a\n")
    if extension in ("jpg", "jpeg"):
        return data.startswith(b"\xff\xd8\xff")
    if extension == "webp":
        return data[:4] == b"RIFF" and data[8:12] == b"WEBP"
    if extension == "gif":
        return data[:6] in (b"GIF87a", b"GIF89a")
    if extension == "avif":
        return data[4:12] in (b"ftypavif", b"ftypavis")
    return False


class MotoModelUpload(http.Controller):

    @http.route("/website_motos_alfa_showcase/upload_model", type="http", auth="user", methods=["POST"])
    def upload_model(self, ufile, **kwargs):
        """Guarda un modelo 3D o una imagen como adjunto público y devuelve su URL para los bloques de moto."""
        if not request.env.user.has_group("website.group_website_restricted_editor"):
            return request.make_json_response({"error": "No tienes permiso para editar el sitio web."}, status=403)

        name = (ufile.filename or "archivo").rsplit("/", 1)[-1]
        extension = name.rsplit(".", 1)[-1].lower() if "." in name else ""
        if extension not in ALLOWED_TYPES:
            return request.make_json_response({"error": f"Formato no admitido. Usa {ALLOWED_LABEL}."}, status=400)

        data = ufile.read(MAX_FILE_SIZE + 1)
        if len(data) > MAX_FILE_SIZE:
            return request.make_json_response({"error": "El archivo supera el límite de 50 MB."}, status=400)
        if not _content_matches(extension, data):
            if extension == "gltf":
                error = "El .gltf no es válido o usa archivos externos; expórtalo como .glb o con los datos incrustados."
            else:
                error = f"El contenido del archivo no corresponde a un .{extension} válido."
            return request.make_json_response({"error": error}, status=400)

        mimetype = ALLOWED_TYPES[extension]
        attachment = request.env["ir.attachment"].create({
            "name": name,
            "raw": data,
            "mimetype": mimetype,
            "public": True,
        })
        return request.make_json_response({
            "id": attachment.id,
            "name": name,
            "url": f"/web/content/{attachment.id}/{quote(name)}",
            "kind": "image" if mimetype.startswith("image/") else "model",
        })
