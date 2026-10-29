from lxml import html
from werkzeug.exceptions import NotFound
from urllib.parse import quote

from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale

from .moto_template import fill_moto_page

# Las URL de la foto principal llevan ?unique=<fecha de modificación>; los adjuntos no cambian de contenido.
MEDIA_MAX_AGE = 24 * 60 * 60

# «Plantilla de motos» (views/moto_template.xml): diseño de todas las páginas /moto/<moto>.
MOTO_TEMPLATE = "website_motos_alfa_showcase.moto_template"
# Página «Motocicletas» (views/motos_page.xml); /motos/<tipo> usa su diseño.
MOTOS_PAGE = "website_motos_alfa_showcase.motos_page"

# Página del editor con el bloque «Tipos de moto»; /motos/<tipo> la muestra con las motos de ese tipo.
MOTOS_PAGE_URL = "/motos"
WHATSAPP_NUMBER = "573223995269"
def sitemap_motos(env, rule, qs):
    """Páginas de las motos publicadas en /sitemap.xml (antes no estaban: sitemap=False)."""
    for moto in env["product.template"]._moto_search():
        url = moto._moto_url()
        if not qs or qs.lower() in url:
            yield {"loc": url}


class MotoPages(http.Controller):
    """Página de cada moto del inventario (categoría MOTOS) con la «Plantilla de motos» (views/moto_template.xml)."""

    def _get_moto(self, moto_id):
        moto = request.env["product.template"].sudo().browse(moto_id).exists()
        if not moto or not moto._moto_is_moto():
            raise NotFound()
        # Sin publicar: solo la ven los editores del sitio (para revisarla antes de publicarla).
        if not moto.is_published and not request.env.user.has_group("website.group_website_restricted_editor"):
            raise NotFound()
        return moto

    @http.route("/moto/<string:moto_slug>", type="http", auth="public", website=True, sitemap= sitemap_motos)
    def moto_page(self, moto_slug, **kwargs):
        _name, moto_id = request.env["ir.http"]._unslug(moto_slug)
        if not moto_id:
            raise NotFound()
        moto = self._get_moto(moto_id)
        # Si cambia el nombre del producto, la dirección antigua lleva a la nueva.
        if f"/moto/{moto_slug}" != moto._moto_url():
            return request.redirect(moto._moto_url(), code=301)
        image_url = moto._moto_image_url()
        model_url = moto._moto_model_url()
        values = {
            "motos": request.env["product.template"]._moto_search(),
            "colors": moto._moto_colors(),
            "specs": moto._moto_specs(),
            "spec_sheet_url": moto._moto_spec_sheet_url(),
            "media": moto._moto_media(moto.product_template_image_ids),
            "description": moto._moto_description(),
            "model_url": model_url,
            "image_url": image_url,
            "price": moto.list_price,
        }
        # Imagen principal y visor con el primer color: la imagen principal es una foto fija (la primera
        # foto 360°, de frente, o la del color); el visor gira con las fotos 360° o usa el modelo .glb.
        # Elegir otro color solo cambia la imagen principal.
        colors = values["colors"]
        frames = colors[0]["frames"] if colors else moto._moto_360_urls(moto.moto_360_image_ids)
        first_color_image = colors[0]["image_url"] if colors else ""
        sequence = " ".join(frames) if len(frames) > 1 else ""
        values["intro_src"] = first_color_image or (frames[:1] or [image_url or model_url])[0]
        values["viewer_src"] = model_url or sequence or (frames[:1] or [first_color_image or image_url])[0]
        values["has_360"] = bool(model_url or sequence)
        # «Otras motos» al final de la moto
        moto_type = moto._moto_type()
        others = (moto_type._moto_type_motos() - moto)[:4] if moto_type else moto.browse()
        values["related"] = {
            "type_name": moto_type.name or "",
            "type_url": moto_type._moto_type_url() if moto_type else MOTOS_PAGE_URL,
            "cards": [self._moto_card(other.name, other._moto_url(), other) for other in others],
        }
        base_url = request.httprequest.host_url.rstrip("/")
        values["structured_data"] = moto._moto_structured_data(base_url, request.website.currency_id)
        moto_link = base_url + moto._moto_url()
        whatsapp_text = f"Hola Motos Alfa, estoy interesado en la moto {moto.name}"
        whatsapp_url = f"https://wa.me/{WHATSAPP_NUMBER}?text={quote(whatsapp_text)}"
        # Sin marcas del editor: así nadie puede guardar los datos de esta moto dentro del diseño maestro.
        page_html = request.env["ir.ui.view"].with_context(inherit_branding=False)._render_template(
            MOTO_TEMPLATE, {"additional_title": moto.name, "whatsapp_url": whatsapp_url, "main_object": moto},
        )
        notice = None
        if request.env.user.has_group("website.group_website_restricted_editor"):
            notice = self._editor_notice()
        return request.make_response(
            fill_moto_page(str(page_html), moto, values, notice),
            headers=[("Content-Type", "text/html; charset=utf-8")],
        )

    def _editor_notice(self):
        return html.fragment_fromstring(
            '<div class="alert alert-info rounded-0 mb-0 text-center o_not_editable">'
            "Esta página usa la «Plantilla de motos» con los datos del producto. "
            "El diseño se cambia en el código (views/moto_template.xml), no en el editor.</div>"
        )

    @http.route("/motos/<string:type_slug>", type="http", auth="public", website=True, sitemap=False)
    def moto_type_page(self, type_slug, **kwargs):
        """La página /motos (con su diseño) para un tipo: el bloque «Tipos de moto» muestra sus motos."""
        _name, type_id = request.env["ir.http"]._unslug(type_slug)
        moto_type = request.env["product.category"].sudo().browse(type_id).exists() if type_id else None
        if not moto_type or not moto_type._moto_is_type():
            raise NotFound()
        if f"/motos/{type_slug}" != moto_type._moto_type_url():
            return request.redirect(moto_type._moto_type_url(), code=301)
        page = request.env.ref(MOTOS_PAGE).sudo()
        # Sin publicar, /motos/<tipo> tampoco se ve, salvo para los editores (igual que /motos).
        if not (page.is_visible or request.env.user.has_group("website.group_website_restricted_editor")):
            raise NotFound()
        page_html = request.env["ir.ui.view"].with_context(inherit_branding=False)._render_template(
            page.view_id.key, {"additional_title": moto_type.name, "moto_type": moto_type},
        )
        return request.make_response(page_html, headers=[("Content-Type", "text/html; charset=utf-8")])

    @http.route([
        "/website_motos_alfa_showcase/moto_types",
        "/website_motos_alfa_showcase/moto_types/<int:type_id>",
    ], type="http", auth="public", website=True, methods=["GET"], readonly=True, sitemap=False)
    def moto_types_content(self, type_id=None, **kwargs):
        """Tarjetas del bloque «Tipos de moto»: los tipos o, con type_id, las motos de ese tipo."""
        categories = request.env["product.category"].sudo()
        moto_type = categories
        if type_id:
            moto_type = categories.browse(type_id).exists()
            if not moto_type or not moto_type._moto_is_type():
                raise NotFound()
            cards = [self._moto_card(moto.name, moto._moto_url(), moto) for moto in moto_type._moto_type_motos()]
        else:
            cards = [
                # Foto de la primera moto del tipo que tenga foto.
                self._moto_card(category.name, category._moto_type_url(),
                                next((m for m in category._moto_type_motos() if m.image_1920), None))
                for category in categories._moto_types()
            ]
        return request.render("website_motos_alfa_showcase.s_moto_types_content", {
            "moto_type": moto_type,
            "cards": cards,
            "motos_page_url": MOTOS_PAGE_URL,
        })

    @http.route("/website_motos_alfa_showcase/last_moto/<int:moto_id>", type="http", auth="public", website=True,
                methods=["GET"], readonly=True, sitemap=False)
    def last_moto_content(self, moto_id, **kwargs):
        """Contenido del bloque «Última moto vista»: la foto en grande y el nombre de la moto que el visitante
        vio (el id lo guarda s_moto_last/000.js en su navegador)."""
        moto = self._get_moto(moto_id)
        return request.render("website_motos_alfa_showcase.s_moto_last_content", {
            "card": self._moto_card(moto.name, moto._moto_url(), moto),
        })

    def _moto_card(self, name, url, moto):
        return {"name": name, "url": url, "image_url": moto._moto_image_url() if moto else ""}

    def _media_response(self, moto, stream):
        """Archivo de /moto/media/... guardado un día. De una moto publicada lo puede guardar también un proxy o
        Cloudflare (Cache-Control: public); de una sin publicar (solo la ven los editores), solo el navegador."""
        stream.public = moto.is_published
        return stream.get_response(max_age=MEDIA_MAX_AGE)

    @http.route("/moto/media/<int:moto_id>/foto/<string:filename>", type="http", auth="public", readonly=True)
    def moto_image(self, moto_id, filename, **kwargs):
        moto = self._get_moto(moto_id)
        if not moto.image_1920:
            raise NotFound()
        stream = request.env["ir.binary"]._get_image_stream_from(moto, "image_1920")
        return self._media_response(moto, stream)

    @http.route("/moto/media/<int:moto_id>/variante/<int:variant_id>/<string:filename>", type="http", auth="public", readonly=True)
    def moto_variant_image(self, moto_id, variant_id, filename, **kwargs):
        moto = self._get_moto(moto_id)
        variant = moto.product_variant_ids.filtered(lambda v: v.id == variant_id)
        if not variant or not variant.image_variant_1920:
            raise NotFound()
        stream = request.env["ir.binary"]._get_image_stream_from(variant, "image_variant_1920")
        return self._media_response(moto, stream)

    @http.route("/moto/media/<int:moto_id>/medio/<int:media_id>/<string:filename>", type="http", auth="public", readonly=True)
    def moto_extra_media(self, moto_id, media_id, filename, **kwargs):
        moto = self._get_moto(moto_id)
        media = moto._moto_extra_media().filtered(lambda m: m.id == media_id)
        if not media or not media.image_1920:
            raise NotFound()
        stream = request.env["ir.binary"]._get_image_stream_from(media, "image_1920")
        return self._media_response(moto, stream)

    @http.route("/moto/media/<int:moto_id>/giro/<int:attachment_id>/<string:filename>", type="http", auth="public", readonly=True)
    def moto_360_image(self, moto_id, attachment_id, filename, **kwargs):
        moto = self._get_moto(moto_id)
        attachment = moto._moto_360_attachments().filtered(lambda a: a.id == attachment_id)
        if not attachment:
            raise NotFound()
        stream = request.env["ir.binary"]._get_stream_from(attachment)
        if not stream.mimetype.startswith("image/") or stream.mimetype == "image/svg+xml":
            raise NotFound()
        return self._media_response(moto, stream)

    @http.route("/moto/media/<int:moto_id>/ficha/<string:filename>", type="http", auth="public", readonly=True)
    def moto_spec_sheet(self, moto_id, filename, **kwargs):
        moto = self._get_moto(moto_id)
        if not moto.with_context(bin_size=True).moto_spec_sheet:
            raise NotFound()
        stream = request.env["ir.binary"]._get_stream_from(moto, "moto_spec_sheet", filename_field="moto_spec_sheet_name")
        # Solo PDF: si alguien subió otro tipo de archivo en el campo, no se publica.
        if stream.mimetype != "application/pdf":
            raise NotFound()
        return self._media_response(moto, stream)

    @http.route("/moto/media/<int:moto_id>/adjunto/<int:attachment_id>/<string:filename>", type="http", auth="public", readonly=True)
    def moto_attachment(self, moto_id, attachment_id, filename, **kwargs):
        moto = self._get_moto(moto_id)
        attachment = moto._moto_attachments().filtered(lambda a: a.id == attachment_id)
        if not attachment:
            raise NotFound()
        stream = request.env["ir.binary"]._get_stream_from(attachment)
        if attachment.name.lower().endswith(".glb"):
            stream.mimetype = "model/gltf-binary"
        elif attachment.name.lower().endswith(".gltf"):
            stream.mimetype = "model/gltf+json"
        elif not stream.mimetype.startswith("image/") or stream.mimetype == "image/svg+xml":
            # Solo fotos y modelos: el resto de adjuntos del producto (facturas, manuales…) no se publica.
            raise NotFound()
        return self._media_response(moto, stream)


class WebsiteSaleMoto(WebsiteSale):

    @http.route()
    def product(self, product, category="", search="", **kwargs):
        """La ficha genérica de la tienda de una moto lleva a su página con la plantilla."""
        if product.sudo()._moto_is_moto():
            return request.redirect(product.sudo()._moto_url(), code=301)
        return super().product(product, category=category, search=search, **kwargs)
