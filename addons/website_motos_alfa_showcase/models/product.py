from urllib.parse import quote

from odoo import api, fields, models

# Categoría raíz del inventario cuyas motos (y las de sus subcategorías) tienen página en el sitio.
MOTO_CATEGORY_NAME = "MOTOS"

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
MENU_FIELDS = {"name", "categ_id", "active", "sale_ok", "parent_id"}


def _clear_menu_cache(env):
    """El encabezado del sitio (con el mega menú) se guarda en caché: se limpia si cambia una moto."""
    env.registry.clear_cache("templates")


class ProductCategory(models.Model):
    _inherit = "product.category"

    moto_master_page_id = fields.Many2one(
        "website.page", string="Página maestra (diseño web)", ondelete="set null",
        help="Página del editor cuyo diseño usan las motos de esta categoría. "
             "Si está vacío se usa la de la categoría padre.")

    def _moto_master_page(self):
        """Página maestra de la categoría o, si no tiene, de la más cercana hacia arriba."""
        self.ensure_one()
        category = self.sudo()
        while category:
            if category.moto_master_page_id:
                return category.moto_master_page_id
            category = category.parent_id
        return self.env["website.page"]

    @api.model
    def _moto_root(self):
        return self.sudo().search([("name", "=ilike", MOTO_CATEGORY_NAME), ("parent_id", "=", False)], limit=1)

    def write(self, vals):
        res = super().write(vals)
        if MENU_FIELDS & set(vals):
            _clear_menu_cache(self.env)
        return res


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def _moto_domain(self):
        root = self.env["product.category"]._moto_root()
        if not root:
            return [("id", "=", False)]
        return [("categ_id", "child_of", root.id), ("sale_ok", "=", True)]

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

    def _moto_specs(self):
        """Atributos que no crean variantes (p. ej. Motor = 160 cc 4V). Si hay un adjunto con el
        nombre del atributo (Motor.jpg), se usa como foto de la tarjeta."""
        self.ensure_one()
        images = {
            attachment.name.rsplit(".", 1)[0].strip().lower(): attachment
            for attachment in self._moto_attachments()
            if (attachment.mimetype or "").startswith("image/")
        }
        specs = []
        for line in self.attribute_line_ids.filtered(lambda l: l.attribute_id.create_variant == "no_variant"):
            image = images.get(line.attribute_id.name.strip().lower())
            specs.append({
                "name": line.attribute_id.name,
                "value": ", ".join(line.value_ids.mapped("name")),
                "image_url": self._moto_attachment_url(image) if image else "",
            })
        return specs

    def _moto_colors(self):
        """Una muestra por variante (Negro, Rojo, Verde…)."""
        self.ensure_one()
        colors = []
        for variant in self.product_variant_ids:
            values = variant.product_template_attribute_value_ids
            if not values:
                continue
            html_color = next((value.html_color for value in values if value.html_color), None) or next(
                (FALLBACK_COLORS[key] for value in values for key in FALLBACK_COLORS if key in value.name.lower()),
                DEFAULT_SWATCH,
            )
            unique = int(variant.write_date.timestamp()) if variant.write_date else 0
            colors.append({
                "name": ", ".join(values.mapped("name")),
                "html_color": html_color,
                # Foto propia de la variante (Variantes → imagen); sin ella el color usa la foto del producto.
                "image_url": (
                    f"/moto/media/{self.id}/variante/{variant.id}/imagen.png?unique={unique}"
                    if variant.image_variant_1920 else ""
                ),
                # Mismos ids que el enlace de la tienda (#attribute_values=…), para abrir el visor en ese color.
                "attribute_value_ids": ",".join(map(str, values.product_attribute_value_id.ids)),
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
