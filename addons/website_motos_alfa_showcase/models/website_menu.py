from odoo import fields, models


class WebsiteMenu(models.Model):
    _inherit = "website.menu"

    # Marca el menú «Modelos» del módulo (views/moto_mega_menu.xml). Se usa un campo y no el nombre del menú para no
    # tocar un menú «Modelos» que ya existiera en el sitio, y no el id interno porque Odoo copia el menú en cada sitio
    # web (las copias no llevan el id, pero sí este campo).
    moto_catalog = fields.Boolean("Catálogo de motos", copy=True, default=False)

    def _moto_is_catalog_menu(self):
        self.ensure_one()
        return self.is_mega_menu and self.moto_catalog
