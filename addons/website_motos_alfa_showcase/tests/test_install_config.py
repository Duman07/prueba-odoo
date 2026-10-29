from odoo import http
from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestInstallConfig(HttpCase):
    """[Inventario de motos] Lo que el módulo deja listo en una base nueva, sin tocar Ajustes (data/)."""

    def test_depends_installed(self):
        """Con instalar solo este módulo quedan la tienda, el CRM, el inventario y BIN/chasis."""
        modules = self.env["ir.module.module"].search([
            ("name", "in", ["website_sale", "website_crm", "crm", "stock", "motos_trazabilidad"]),
        ])
        self.assertEqual(set(modules.mapped("state")), {"installed"})
        self.assertEqual(len(modules), 5)

    def test_variants_for_internal_users(self):
        """data/product_variant_group.xml: «Variantes» para todos, también para los usuarios nuevos."""
        group_user = self.env.ref("base.group_user")
        self.assertIn(self.env.ref("product.group_product_variant"), group_user.implied_ids)
        self.assertTrue(self.env.ref("base.user_admin").has_group("product.group_product_variant"))
        user = self.env["res.users"].create({"name": "Vendedor Motos", "login": "vendedor_motos_prueba"})
        self.assertTrue(user.has_group("product.group_product_variant"))

    def test_moto_root_category(self):
        """data/product_category_motos.xml: existe MOTOS y volver a crearla no la duplica."""
        Category = self.env["product.category"]
        root = Category._moto_root()
        self.assertTrue(root)
        self.assertEqual(Category._moto_create_root(), root)
        self.assertEqual(Category.search_count([("name", "=ilike", "MOTOS"), ("parent_id", "=", False)]), 1)

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
