from odoo import http
from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestInstallConfig(HttpCase):
    """[Inventario de motos] Lo que el módulo deja listo en una base nueva (data/), sin tocar lo que ya existía."""

    def test_depends_installed(self):
        """Con instalar solo este módulo quedan la tienda, el CRM, el inventario y BIN/chasis."""
        modules = self.env["ir.module.module"].search([
            ("name", "in", ["website_sale", "website_crm", "crm", "stock", "motos_trazabilidad"]),
        ])
        self.assertEqual(set(modules.mapped("state")), {"installed"})
        self.assertEqual(len(modules), 5)

    def test_moto_root_category(self):
        """data/product_category_motos.xml: la categoría MOTOS del módulo se reconoce por su id interno."""
        root = self.env["product.category"]._moto_root()
        self.assertEqual(root, self.env.ref("website_motos_alfa_showcase.category_motos"))
        self.assertEqual(root.name, "MOTOS")

    def test_existing_motos_category_untouched(self):
        """Una categoría «MOTOS» que ya existía en la base no se usa: sus productos siguen en la tienda normal."""
        other_root = self.env["product.category"].create({"name": "MOTOS"})
        product = self.env["product.template"].create({
            "name": "Producto Ajeno", "categ_id": other_root.id, "sale_ok": True, "is_published": True,
        })
        self.assertNotEqual(self.env["product.category"]._moto_root(), other_root)
        self.assertFalse(product._moto_is_moto())
        self.assertNotIn(product, self.env["product.template"]._moto_search())
        self.assertFalse(product.website_url.startswith("/moto/"))

    def test_existing_modelos_menu_untouched(self):
        """Un mega menú «Modelos» creado a mano no se reemplaza; el del módulo (y su copia en cada sitio) sí es el catálogo."""
        website = self.env["website"].get_current_website()
        own = self.env["website.menu"].create({
            "name": "Modelos", "url": "#", "is_mega_menu": True, "website_id": website.id, "parent_id": website.menu_id.id,
        })
        self.assertFalse(own._moto_is_catalog_menu())
        module_menu = self.env.ref("website_motos_alfa_showcase.menu_modelos")
        self.assertTrue(module_menu._moto_is_catalog_menu())
        copies = self.env["website.menu"].search([("moto_catalog", "=", True), ("website_id", "=", website.id)])
        self.assertTrue(copies, "La copia del menú en el sitio debe conservar moto_catalog")

    def test_quote_form_fills_location_fields(self):
        """data/crm_lead_form_whitelist.xml: País, Departamento y Ciudad van a sus campos y no a «Otra información»."""
        country = self.env.ref("base.co")
        state = self.env["res.country.state"].search([("country_id", "=", country.id)], limit=1)
        self.authenticate(None, None)
        response = self.url_open("/website/form/crm.lead", data={
            "contact_name": "Cliente Prueba",
            "email_from": "cliente@prueba.com",
            "phone": "3000000000",
            "name": "Cotización Moto Prueba",
            "country_id": country.id,
            "state_id": state.id,
            "city": "Medellín",
            "csrf_token": http.Request.csrf_token(self),
        })
        lead = self.env["crm.lead"].browse(response.json().get("id"))
        self.assertTrue(lead.exists())
        self.assertEqual(lead.country_id, country)
        self.assertEqual(lead.state_id, state)
        self.assertEqual(lead.city, "Medellín")
        self.assertNotIn("Medellín", str(lead.description or ""))
