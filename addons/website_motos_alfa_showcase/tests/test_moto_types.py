from odoo.tests import HttpCase, tagged

from .test_moto_pages import PIXEL_PNG

CONTENT_URL = "/website_motos_alfa_showcase/moto_types"

# Página /motos de prueba: un título propio y el bloque «Tipos de moto».
MOTOS_ARCH = """
<t t-name="{key}">
    <t t-call="website.layout">
        <div id="wrap" class="oe_structure">
            <section class="s_title"><h2>Motocicletas prueba</h2></section>
            <section class="s_moto_types"><div class="container"><div class="s_moto_types_content o_not_editable"/></div></section>
        </div>
    </t>
</t>
"""


@tagged("post_install", "-at_install")
class TestMotoTypes(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        website = cls.env["website"].get_current_website()
        # Se usa la página /motos del sitio si existe (los cambios se deshacen al terminar) o se crea una.
        cls.page = cls.env["website.page"].search([("url", "=", "/motos")] + website.website_domain(), limit=1)
        if not cls.page:
            view = cls.env["ir.ui.view"].create({
                "name": "Motos prueba", "type": "qweb", "key": "website.test-motos", "arch": "<t/>", "website_id": website.id,
            })
            cls.page = cls.env["website.page"].create({"view_id": view.id, "url": "/motos", "website_id": website.id})
        cls.page.view_id.arch = MOTOS_ARCH.format(key=cls.page.view_id.key)
        cls.page.is_published = True

        Category = cls.env["product.category"]
        root = Category._moto_root() or Category.create({"name": "MOTOS"})
        # Tipo → línea → moto, otro tipo después con su moto, y un tipo sin motos.
        cls.type = Category.create({"name": "Tipo Prueba", "parent_id": root.id})
        cls.line = Category.create({"name": "Línea Tipo", "parent_id": cls.type.id})
        cls.type2 = Category.create({"name": "Tipo Dos", "parent_id": root.id})
        cls.empty_type = Category.create({"name": "Tipo Vacío", "parent_id": root.id})
        cls.moto_no_image = cls.env["product.template"].create({"name": "A Moto Sin Foto", "categ_id": cls.line.id,"is_published":True })
        cls.moto = cls.env["product.template"].create({
            "name": "B Moto Tipo", "categ_id": cls.line.id, "image_1920": PIXEL_PNG, "is_published": True,
        })
        cls.moto2 = cls.env["product.template"].create({"name": "Moto Tipo Dos", "categ_id": cls.type2.id,"is_published": True})
        cls.other = cls.env["product.template"].create({"name": "Casco Tipo", "image_1920": PIXEL_PNG})

    def test_types_cards(self):
        self.assertEqual(self.env["product.category"]._moto_types().filtered(
            lambda t: t in self.type | self.type2 | self.empty_type), self.type | self.type2)
        response = self.url_open(CONTENT_URL)
        self.assertEqual(response.status_code, 200)
        cards = response.text.replace("&amp;", "&")
        # Cada tipo con motos enlaza a /motos/<tipo>, en el orden en que se crearon; el tipo vacío no sale.
        self.assertIn(f'href="{self.type._moto_type_url()}"', cards)
        self.assertLess(cards.index("Tipo Prueba"), cards.index("Tipo Dos"))
        self.assertNotIn("Tipo Vacío", cards)
        # Foto de la primera moto del tipo que tenga foto (la primera por nombre no tiene).
        self.assertIn(self.moto._moto_image_url(), cards)
        # Las líneas no son tipos y no salen como tarjeta.
        self.assertNotIn("Línea Tipo", cards)
        self.assertNotIn("Todos los tipos", cards)

    def test_type_motos_cards(self):
        response = self.url_open(f"{CONTENT_URL}/{self.type.id}")
        self.assertEqual(response.status_code, 200)
        cards = response.text
        self.assertIn("Tipo Prueba", cards)
        self.assertIn('href="/motos"', cards)
        self.assertIn(f'href="{self.moto._moto_url()}"', cards)
        self.assertIn(f'href="{self.moto_no_image._moto_url()}"', cards)
        self.assertNotIn("Moto Tipo Dos", cards)
        self.assertNotIn("Casco Tipo", cards)
        # Solo los tipos: una línea o una categoría que no es de motos da 404.
        self.assertEqual(self.url_open(f"{CONTENT_URL}/{self.line.id}").status_code, 404)
        self.assertEqual(self.url_open(f"{CONTENT_URL}/{self.env.ref('product.product_category_all').id}").status_code, 404)

    def test_type_page_uses_motos_page(self):
        response = self.url_open(self.type._moto_type_url())
        self.assertEqual(response.status_code, 200)
        self.assertIn("Motocicletas prueba", response.text)
        self.assertIn("s_moto_types_content", response.text)
        self.assertIn("Tipo Prueba", response.text[:response.text.index("</title>")])
        self.assertNotIn("data-oe-model", response.text)
        # Dirección vieja → la actual; una línea no tiene página de tipo.
        old = self.url_open(f"/motos/otro-nombre-{self.type.id}", allow_redirects=False)
        self.assertEqual(old.status_code, 301)
        self.assertTrue(old.headers["Location"].endswith(self.type._moto_type_url()))
        self.assertEqual(self.url_open(f"/motos/linea-tipo-{self.line.id}").status_code, 404)

    def test_type_page_unpublished(self):
        self.page.is_published = False
        self.assertEqual(self.url_open(self.type._moto_type_url()).status_code, 404)
