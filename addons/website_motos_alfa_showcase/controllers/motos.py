from lxml import html
from werkzeug.exceptions import NotFound
from urllib.parse import quote

from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale

from .moto_template import fill_moto_page

# Las URL de la foto principal llevan ?unique=<fecha de modificación>; los adjuntos no cambian de contenido.
MEDIA_MAX_AGE = 24 * 60 * 60

# Página hecha en el editor que usan las motos cuya categoría no tiene página maestra (clave de su vista).
MASTER_KEY_PARAM = "website_motos_alfa_showcase.master_page_key"
DEFAULT_MASTER_KEY = "website.hunk-160r-4v"

# Página del editor con el bloque «Tipos de moto»; /motos/<tipo> la muestra con las motos de ese tipo.
MOTOS_PAGE_URL = "/motos"
WHATSAPP_NUMBER = "573223995269"


class MotoPages(http.Controller):
    """Página de cada moto del inventario (categoría MOTOS) con el diseño de la página maestra del editor."""

    def _get_moto(self, moto_id):
        moto = request.env["product.template"].sudo().browse(moto_id).exists()
        if not moto or not moto._moto_is_moto():
            raise NotFound()
        return moto

    @http.route("/moto/<string:moto_slug>", type="http", auth="public", website=True, sitemap=False)
    def moto_page(self, moto_slug, **kwargs):
        _name, moto_id = request.env["ir.http"]._unslug(moto_slug)
        if not moto_id:
            raise NotFound()
        moto = self._get_moto(moto_id)
        # Si cambia el nombre del producto, la dirección antigua lleva a la nueva.
        if f"/moto/{moto_slug}" != moto._moto_url():
            return request.redirect(moto._moto_url(), code=301)
        master = self._get_master_view(moto)
        if not master:
            raise NotFound()
        image_url = moto._moto_image_url()
        model_url = moto._moto_model_url()
        values = {
            "motos": request.env["product.template"]._moto_search(),
            "colors": moto._moto_colors(),
            "specs": moto._moto_specs(),
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
        values["intro_src"] = (frames[:1] or [first_color_image or image_url or model_url])[0]
        values["viewer_src"] = model_url or sequence or (frames[:1] or [first_color_image or image_url])[0]
        moto_link = request.httprequest.host_url.rstrip("/") + moto._moto_url()
        whatsapp_text = f"Hola Motos Alfa, estoy interesado en la moto {moto.name}"
        whatsapp_url = f"https://wa.me/{WHATSAPP_NUMBER}?text={quote(whatsapp_text)}"
        # Sin marcas del editor: así nadie puede guardar los datos de esta moto dentro del diseño maestro.
        page_html = request.env["ir.ui.view"].with_context(inherit_branding=False)._render_template(
            master.key, {"additional_title": moto.name, "whatsapp_url": whatsapp_url},
        )
        master_url = request.env["website.page"].sudo().search([("view_id", "=", master.id)], limit=1).url
        notice = None
        if request.env.user.has_group("website.group_website_restricted_editor"):
            notice = self._editor_notice(master_url)
        return request.make_response(
            fill_moto_page(str(page_html), moto, values, master_url, notice),
            headers=[("Content-Type", "text/html; charset=utf-8")],
        )

    def _get_master_view(self, moto):
        """Página del editor cuyo diseño usa la moto: la de su categoría (o la de una categoría padre)
        y, si ninguna tiene, la general (por defecto la de la Hunk 160R 4V)."""
        page = moto.categ_id._moto_master_page()
        if page.view_id:
            return page.view_id
        key = request.env["ir.config_parameter"].sudo().get_param(MASTER_KEY_PARAM, DEFAULT_MASTER_KEY)
        website = request.env["website"].get_current_website()
        return website.with_context(website_id=website.id).sudo().viewref(key, raise_if_not_found=False)

    def _editor_notice(self, master_url):
        notice = html.fragment_fromstring(
            '<div class="alert alert-info rounded-0 mb-0 text-center o_not_editable">'
            "Esta página usa el diseño de la página maestra con los datos del producto. "
            "Para cambiar el diseño de todas las motos, edita la página maestra.</div>"
        )
        if master_url:
            link = html.Element("a", href=master_url, **{"class": "alert-link ms-1"})
            link.text = "Editar el diseño"
            notice.append(link)
        return notice

    @http.route("/motos/<string:type_slug>", type="http", auth="public", website=True, sitemap=False)
    def moto_type_page(self, type_slug, **kwargs):
        """La página /motos (con su diseño) para un tipo: el bloque «Tipos de moto» muestra sus motos."""
        _name, type_id = request.env["ir.http"]._unslug(type_slug)
        moto_type = request.env["product.category"].sudo().browse(type_id).exists() if type_id else None
        if not moto_type or not moto_type._moto_is_type():
            raise NotFound()
        if f"/motos/{type_slug}" != moto_type._moto_type_url():
            return request.redirect(moto_type._moto_type_url(), code=301)
        page = request.env["website.page"].sudo().search(
            [("url", "=", MOTOS_PAGE_URL)] + request.website.website_domain(), order="website_id", limit=1)
        # Sin publicar, /motos/<tipo> tampoco se ve, salvo para los editores (igual que /motos).
        if not page or not (page.is_visible or request.env.user.has_group("website.group_website_restricted_editor")):
            raise NotFound()
        # Sin marcas del editor: el diseño se edita en /motos.
        page_html = request.env["ir.ui.view"].with_context(inherit_branding=False)._render_template(
            page.view_id.key, {"additional_title": moto_type.name},
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

    def _moto_card(self, name, url, moto):
        return {"name": name, "url": url, "image_url": moto._moto_image_url() if moto else ""}

    @http.route("/moto/media/<int:moto_id>/foto/<string:filename>", type="http", auth="public", readonly=True)
    def moto_image(self, moto_id, filename, **kwargs):
        moto = self._get_moto(moto_id)
        if not moto.image_1920:
            raise NotFound()
        stream = request.env["ir.binary"]._get_image_stream_from(moto, "image_1920")
        return stream.get_response(max_age=MEDIA_MAX_AGE)

    @http.route("/moto/media/<int:moto_id>/variante/<int:variant_id>/<string:filename>", type="http", auth="public", readonly=True)
    def moto_variant_image(self, moto_id, variant_id, filename, **kwargs):
        moto = self._get_moto(moto_id)
        variant = moto.product_variant_ids.filtered(lambda v: v.id == variant_id)
        if not variant or not variant.image_variant_1920:
            raise NotFound()
        stream = request.env["ir.binary"]._get_image_stream_from(variant, "image_variant_1920")
        return stream.get_response(max_age=MEDIA_MAX_AGE)

    @http.route("/moto/media/<int:moto_id>/medio/<int:media_id>/<string:filename>", type="http", auth="public", readonly=True)
    def moto_extra_media(self, moto_id, media_id, filename, **kwargs):
        moto = self._get_moto(moto_id)
        media = moto._moto_extra_media().filtered(lambda m: m.id == media_id)
        if not media or not media.image_1920:
            raise NotFound()
        stream = request.env["ir.binary"]._get_image_stream_from(media, "image_1920")
        return stream.get_response(max_age=MEDIA_MAX_AGE)

    @http.route("/moto/media/<int:moto_id>/giro/<int:attachment_id>/<string:filename>", type="http", auth="public", readonly=True)
    def moto_360_image(self, moto_id, attachment_id, filename, **kwargs):
        moto = self._get_moto(moto_id)
        attachment = moto._moto_360_attachments().filtered(lambda a: a.id == attachment_id)
        if not attachment:
            raise NotFound()
        stream = request.env["ir.binary"]._get_stream_from(attachment)
        if not stream.mimetype.startswith("image/") or stream.mimetype == "image/svg+xml":
            raise NotFound()
        return stream.get_response(max_age=MEDIA_MAX_AGE)

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
        return stream.get_response(max_age=MEDIA_MAX_AGE)


class WebsiteSaleMoto(WebsiteSale):

    @http.route()
    def product(self, product, category="", search="", **kwargs):
        """La ficha genérica de la tienda de una moto lleva a su página con la plantilla."""
        if product.sudo()._moto_is_moto():
            return request.redirect(product.sudo()._moto_url(), code=301)
        return super().product(product, category=category, search=search, **kwargs)
