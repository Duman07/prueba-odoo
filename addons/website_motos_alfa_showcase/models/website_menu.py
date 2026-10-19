from odoo import models

# Mega menú que se llena solo con las motos del inventario.
CATALOG_MENU_NAME = "modelos"


class WebsiteMenu(models.Model):
    _inherit = "website.menu"

    def _moto_is_catalog_menu(self):
        self.ensure_one()
        return self.is_mega_menu and (self.name or "").strip().lower() == CATALOG_MENU_NAME
