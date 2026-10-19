from lxml import html
from werkzeug.exceptions import NotFound

from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale

from .moto_template import fill_moto_page

# Las URL de la foto principal llevan ?unique=<fecha de modificación>; los adjuntos no cambian de contenido.
MEDIA_MAX_AGE = 24 * 60 * 60

# Página hecha en el editor que usan las motos cuya categoría no tiene página maestra (clave de su vista).
MASTER_KEY_PARAM = "website_motos_alfa_showcase.master_page_key"
DEFAULT_MASTER_KEY = "website.hunk-160r-4v"


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
            # Como en la página maestra: la foto en «Moto 3D» y el modelo .glb en el «Visor 360°».
            "intro_src": image_url or model_url,
            "model_url": model_url,
            "image_url": image_url,
        }
        # Sin modelo 3D, el visor empieza con la foto del primer color.
        first_color_image = values["colors"][0]["image_url"] if values["colors"] else ""
        values["viewer_src"] = model_url or first_color_image or image_url
        # Sin marcas del editor: así nadie puede guardar los datos de esta moto dentro del diseño maestro.
        page_html = request.env["ir.ui.view"].with_context(inherit_branding=False)._render_template(
            master.key, {"additional_title": moto.name},
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
