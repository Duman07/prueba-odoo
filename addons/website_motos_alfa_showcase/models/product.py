import re
from urllib.parse import quote

from lxml import html

from odoo import api, fields, models

from odoo.addons.web_editor.tools import get_video_url_data

# Categoría raíz del inventario cuyas motos (y las de sus subcategorías) tienen página en el sitio.
MOTO_CATEGORY_NAME = "MOTOS"

# Marca de las motos en los datos para Google (_moto_structured_data): el producto de Odoo no tiene campo de marca.
MOTO_BRAND = "Hero"

# Color de la muestra cuando el valor del atributo no tiene un color HTML configurado.
FALLBACK_COLORS = {
    "negro": "#1a1b1e",
    "rojo": "#e00000",
    "verde": "#1f7a3a",
    "azul": "#1d4ed8",
    "blanco": "#ffffff",
    "gris": "#8a9097",
    "plata": "#c0c4c9",
    "amarillo": "#f2c200",
    "naranja": "#f26b00",
}
DEFAULT_SWATCH = "#8a9097"

# Campos que cambian lo que muestra el mega menú «Modelos».
MENU_FIELDS = {"name", "categ_id", "active", "sale_ok", "parent_id", "is_published", "website_published"}


def _natural_key(attachment):
    """Orden natural por nombre: moto-2 antes que moto-10."""
    return [int(part) if part.isdigit() else part.casefold() for part in re.split(r"(\d+)", attachment.name or "")]


def _clear_menu_cache(env):
    """El encabezado del sitio (con el mega menú) se guarda en caché: se limpia si cambia una moto."""
    env.registry.clear_cache("templates")


class ProductCategory(models.Model):
    _inherit = "product.category"

    @api.model
    def _moto_root(self):
        return self.sudo().search([("name", "=ilike", MOTO_CATEGORY_NAME), ("parent_id", "=", False)], limit=1)

    @api.model
    def _moto_create_root(self):
        """Crea MOTOS al instalar si la base no la tiene (data/product_category_motos.xml)."""
        return self._moto_root() or self.sudo().create({"name": MOTO_CATEGORY_NAME})

    # Tipos de moto: subcategorías directas de MOTOS (Trabajadora, Urbana…), para el bloque «Tipos de moto».

    @api.model
    def _moto_types(self):
        """Tipos que tienen motos, en el orden en que se crearon."""
        root = self._moto_root()
        return root.child_id.sorted("id").filtered(lambda moto_type: moto_type._moto_type_motos())

    def _moto_is_type(self):
        self.ensure_one()
        root = self._moto_root()
        return bool(root) and self.sudo().parent_id == root

    def _moto_type_motos(self):
        """Motos del tipo (de sus líneas y subcategorías), por nombre."""
        self.ensure_one()
        parent_path = self.sudo().parent_path
        return self.env["product.template"]._moto_search().filtered(
            lambda moto: moto.categ_id.parent_path.startswith(parent_path))

    def _moto_type_url(self):
        self.ensure_one()
        # Con el nombre del tipo y no el completo («MOTOS / Urbana»): /motos/urbana-95.
        return f"/motos/{self.env['ir.http']._slug((self.id, self.name))}"

    def write(self, vals):
        res = super().write(vals)
        if MENU_FIELDS & set(vals):
            _clear_menu_cache(self.env)
        return res


class ProductTemplate(models.Model):
    _inherit = "product.template"

    moto_main_variant_id = fields.Many2one(
        "product.product", string="Color principal", domain="[('product_tmpl_id', '=', id)]",
        help="Color con el que se abre la página de la moto (primera muestra, imagen principal, visor, "
             "fondo y video). Si está vacío, el primero de Odoo (por referencia interna).")
    moto_360_image_ids = fields.Many2many(
        "ir.attachment", "product_template_moto_360_rel", "product_tmpl_id", "attachment_id",
        string="Fotos 360°",
        help="Fotos tomadas alrededor de la moto (p. ej. 24, una cada 15°), para motos sin colores o "
             "colores sin fotos propias. Se ordenan por nombre: la primera es la vista de frente.")
    moto_spec_sheet = fields.Binary(
        "Ficha técnica (PDF)", attachment=True,
        help="Ficha técnica de la moto en PDF: la página de la moto muestra el botón «Descargar ficha técnica (PDF)».")
    moto_spec_sheet_name = fields.Char("Nombre de la ficha técnica")

    @api.model
    def _moto_domain(self):
        root = self.env["product.category"]._moto_root()
        if not root:
            return [("id", "=", False)]
        return [("categ_id", "child_of", root.id), ("sale_ok", "=", True), ("is_published", "=", True)]

    @api.model
    def _moto_search(self):
        return self.sudo().search(self._moto_domain(), order="name")

    @api.model
    def _moto_menu_groups(self):
        """Motos agrupadas por subcategoría de MOTOS (ECO, HUNK…), para las columnas del mega menú."""
        groups = {}
        for moto in self._moto_search():
            groups.setdefault(moto.categ_id, []).append(moto)
        return sorted(groups.items(), key=lambda item: item[0].name.lower())

    def _moto_is_moto(self):
        self.ensure_one()
        root = self.env["product.category"]._moto_root()
        return bool(
            root and self.active and self.sale_ok and self.categ_id
            and self.categ_id.sudo().parent_path.startswith(root.parent_path)
        )

    def _moto_url(self):
        self.ensure_one()
        return f"/moto/{self.env['ir.http']._slug(self)}"

    def _moto_type(self):
        """Tipo de la moto (subcategoria directa de MOTOS: Urbana....); si no tiene queda vacio."""
        self.ensure_one()
        category = self.sudo().categ_id
        while category and not category._moto_is_type():
            category = category.parent_id
        return category

    def _compute_website_url(self):
        """Las motos enlazan a su página con la plantilla de la Hunk 160R 4V en lugar de /shop:
        así lo hacen el bloque «Productos», la tienda y la búsqueda del sitio."""
        super()._compute_website_url()
        for template in self:
            if template.id and template._moto_is_moto():
                template.website_url = template._moto_url()

    # Archivos que usa la página: se sirven con controllers/motos.py porque los visitantes no pueden leer productos.

    def _moto_attachments(self):
        self.ensure_one()
        return self.env["ir.attachment"].sudo().search([
            ("res_model", "=", "product.template"),
            ("res_id", "=", self.id),
            ("res_field", "=", False),
        ], order="name, id")

    def _moto_attachment_url(self, attachment):
        return f"/moto/media/{self.id}/adjunto/{attachment.id}/{quote(attachment.name)}"

    def _moto_image_url(self):
        """Foto principal del producto; la extensión le indica al bloque que es una imagen y no un modelo."""
        self.ensure_one()
        if not self.image_1920:
            return ""
        unique = int(self.write_date.timestamp()) if self.write_date else 0
        return f"/moto/media/{self.id}/foto/imagen.png?unique={unique}"

    def _moto_model_url(self):
        """Primer .glb/.gltf adjunto al producto (clip de adjuntos del formulario)."""
        self.ensure_one()
        model = self._moto_attachments().filtered(lambda a: a.name.lower().endswith((".glb", ".gltf")))[:1]
        return self._moto_attachment_url(model) if model else ""

    def _moto_spec_sheet_url(self):
        """Ficha técnica en PDF (campo «Ficha técnica (PDF)»); ?unique cambia al subir otra, para que no salga la vieja de la caché."""
        self.ensure_one()
        # bin_size: solo el tamaño del archivo, sin leerlo entero.
        if not self.with_context(bin_size=True).moto_spec_sheet:
            return ""
        unique = int(self.write_date.timestamp()) if self.write_date else 0
        return f"/moto/media/{self.id}/ficha/{quote(self.moto_spec_sheet_name or 'ficha-tecnica.pdf')}?unique={unique}"

    def _moto_specs(self):
        """Atributos que no crean variantes (p. ej. Motor = Cilindraje: 160 cc): un grupo de «Especificaciones técnicas»
        cada uno, con un valor por fila."""
        self.ensure_one()
        return [
            {"name": line.attribute_id.name, "values": line.value_ids.mapped("name")}
            for line in self.attribute_line_ids.filtered(lambda l: l.attribute_id.create_variant == "no_variant")
        ]

    def _moto_360_attachments(self):
        """Fotos 360° de la moto y de sus colores."""
        self.ensure_one()
        return self.moto_360_image_ids | self.product_variant_ids.moto_360_image_ids

    def _moto_360_urls(self, attachments):
        """URL de las fotos 360°, en orden natural por nombre (solo imágenes)."""
        images = attachments.filtered(lambda a: (a.mimetype or "").startswith("image/") and a.mimetype != "image/svg+xml")
        return [
            f"/moto/media/{self.id}/giro/{attachment.id}/{quote(attachment.name)}"
            for attachment in images.sorted(_natural_key)
        ]

    def _moto_media_url(self, media):
        unique = int(media.write_date.timestamp()) if media.write_date else 0
        return f"/moto/media/{self.id}/medio/{media.id}/imagen.png?unique={unique}"

    def _moto_extra_media(self):
        """«Medios adicionales» del producto y de sus variantes (eCommerce)."""
        self.ensure_one()
        return self.product_template_image_ids | self.product_variant_ids.product_variant_image_ids

    def _moto_media(self, medias):
        """Fotos y videos de unos «Medios adicionales», en su orden: fondos y videos de la página."""
        images, videos = [], []
        for media in medias.sorted(lambda m: (m.sequence, m.id)):
            if media.video_url:
                data = get_video_url_data(media.video_url, autoplay=True, loop=True, hide_controls=True)
                if not data.get("error"):
                    videos.append(data["embed_url"])
            elif media.image_1920:
                images.append(self._moto_media_url(media))
        return {"images": images, "videos": videos}

    def _moto_description(self):
        """Frase del producto (Descripción para comercio electrónico) en texto plano."""
        self.ensure_one()
        if not self.description_ecommerce:
            return ""
        return " ".join(html.fragment_fromstring(self.description_ecommerce, create_parent="div").text_content().split())


    def _moto_structured_data(self, base_url, currency):
        """Datos de la moto para Google (schema.org Product, JSON-LD): nombre, dirección, foto, descripción, tipo,
        marca y precio. Sin foto, descripción, tipo o precio, ese dato no va."""
        self.ensure_one()
        data = {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": self.name,
            "url": base_url + self._moto_url(),
            "brand": {"@type": "Brand", "name": MOTO_BRAND},
        }
        if self.image_1920:
            data["image"] = base_url + self._moto_image_url()
        description = self._moto_description()
        if description:
            data["description"] = description
        moto_type = self._moto_type()
        if moto_type:
            data["category"] = moto_type.name
        if self.list_price:
            data["offers"] = {
                "@type": "Offer",
                "url": data["url"],
                "price": f"{self.list_price:.0f}",
                "priceCurrency": currency.name,
            }
        return data

    def _default_website_meta(self):
        """Motos sin «Descripción de venta»: la descripción para buscadores y al compartir es su frase
        («Descripción para comercio electrónico»)."""
        res = super()._default_website_meta()
        if self._moto_is_moto() and not self.description_sale:
            description = self._moto_description()
            res["default_opengraph"]["og:description"] = res["default_twitter"]["twitter:description"] = description
            res["default_meta_description"] = description
        return res

    def _moto_colors(self):
        """Una muestra por variante (Negro, Rojo, Verde…)."""
        self.ensure_one()
        product_media = self._moto_media(self.product_template_image_ids)
        product_frames = self._moto_360_urls(self.moto_360_image_ids)
        product_image = self._moto_image_url()
        colors = []
        variants = self.product_variant_ids
        if self.moto_main_variant_id in variants:
            # El color principal va primero.
            variants = self.moto_main_variant_id | variants
        for variant in variants:
            values = variant.product_template_attribute_value_ids
            if not values:
                continue
            html_color = next((value.html_color for value in values if value.html_color), None) or next(
                (FALLBACK_COLORS[key] for value in values for key in FALLBACK_COLORS if key in value.name.lower()),
                DEFAULT_SWATCH,
            )
            unique = int(variant.write_date.timestamp()) if variant.write_date else 0
            # Fotos y videos del color (Variantes → Medios adicionales); sin ellos, los del producto.
            media = self._moto_media(variant.product_variant_image_ids)
            image_url = (
                f"/moto/media/{self.id}/variante/{variant.id}/imagen.png?unique={unique}"
                if variant.image_variant_1920 else ""
            )
            frames = self._moto_360_urls(variant.moto_360_image_ids) or product_frames
            colors.append({
                "name": ", ".join(values.mapped("name")),
                "html_color": html_color,
                # Foto propia de la variante (Variantes → imagen); sin ella el color usa la foto del producto.
                "image_url": image_url,
                "frames": frames,
                "main_src": image_url or (frames[:1] or [product_image])[0],
                # Mismos ids que el enlace de la tienda (#attribute_values=…), para abrir el visor en ese color.
                "attribute_value_ids": ",".join(map(str, values.product_attribute_value_id.ids)),
                "media_images": media["images"] or product_media["images"],
                "media_videos": media["videos"] or product_media["videos"],
            })
        return colors

    @api.model_create_multi
    def create(self, vals_list):
        templates = super().create(vals_list)
        _clear_menu_cache(self.env)
        return templates

    def write(self, vals):
        res = super().write(vals)
        if MENU_FIELDS & set(vals):
            _clear_menu_cache(self.env)
        return res

    def unlink(self):
        res = super().unlink()
        _clear_menu_cache(self.env)
        return res


class ProductProduct(models.Model):
    _inherit = "product.product"

    moto_360_image_ids = fields.Many2many(
        "ir.attachment", "product_product_moto_360_rel", "product_id", "attachment_id",
        string="Fotos 360°",
        help="Fotos de este color tomadas alrededor de la moto (p. ej. 24, una cada 15°). "
             "Se ordenan por nombre: la primera es la vista de frente.")
