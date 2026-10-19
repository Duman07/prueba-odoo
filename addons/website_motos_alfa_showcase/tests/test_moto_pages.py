import re

from odoo.tests import HttpCase, new_test_user, tagged

from .test_model_upload import FAKE_GLB

PIXEL_PNG = b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="

# Página maestra de prueba con la misma estructura que la del editor (Moto 3D, Visor 360°, tarjetas, formulario).
MASTER_ARCH = """
<t t-name="website.test-moto-master">
    <t t-call="website.layout">
        <div id="wrap" class="oe_structure">
            <section class="s_text_block"><p><span class="o_small-fs">Diseño 150​</span></p></section>
            <section class="s_moto_3d" data-model-src="/web/content/1/diseno.png" data-model-yaw="180">
                <div class="o_grid_item">
                    <p><span class="o_small-fs"><strong><font style="color: red;">HERO · DISEÑO</font></strong></span></p>
                    <h1><span class="display-1-fs"><strong>DISEÑO 150</strong></span></h1>
                    <a class="btn" href="/test-moto-master#cotizar">Contáctanos</a>
                </div>
                <div class="s_moto_3d_stage"/>
            </section>
            <section class="s_moto_360" data-model-src="/web/content/2/diseno.glb">
                <div class="s_moto_360_panel">
                    <div class="s_moto_360_swatches">
                        <div class="s_moto_360_swatch o_diseno" style="background-color: red;" data-color-name="Color 1" data-model-src="/x.glb"/>
                        <div class="s_moto_360_swatch" data-color-name="Color 2"/>
                    </div>
                    <p class="s_moto_360_color_name">Color 1</p>
                </div>
            </section>
            <section class="s_product_list">
                <div class="row">
                    <div class="col-lg-12"><h2>Especificaciones técnicas</h2></div>
                    <div class="col-lg-2 o_diseno_col"><div class="s_card card">
                        <figure><a href="#"><img src="/web/image/1/diseno.webp" data-original-id="1"/></a></figure>
                        <strong>Motor </strong><strong><font style="color: red;">150 cc</font></strong>
                    </div></div>
                    <div class="col-lg-2"><div class="s_card card"><div class="card-body"><h3 class="card-title"><a href="#">Sutil</a></h3></div></div></div>
                </div>
            </section>
            <form><select name="Modelo" id="m"><option value="Opción 1">Opción 1</option></select></form>
        </div>
    </t>
</t>
"""


@tagged("post_install", "-at_install")
class TestMotoPages(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        website = cls.env["website"].get_current_website()
        master = cls.env["ir.ui.view"].create({
            "name": "Moto maestra prueba", "type": "qweb", "key": "website.test-moto-master",
            "arch": MASTER_ARCH, "website_id": website.id,
        })
        cls.env["website.page"].create({"view_id": master.id, "url": "/test-moto-master", "website_id": website.id})
        cls.env["ir.config_parameter"].set_param("website_motos_alfa_showcase.master_page_key", master.key)

        root = cls.env["product.category"]._moto_root() or cls.env["product.category"].create({"name": "MOTOS"})
        cls.line = cls.env["product.category"].create({"name": "Línea Prueba", "parent_id": root.id})
        color = cls.env["product.attribute"].create({
            "name": "Color prueba",
            "value_ids": [(0, 0, {"name": "Rojo"}), (0, 0, {"name": "Negro"})],
        })
        motor = cls.env["product.attribute"].create({
            "name": "Motor prueba",
            "create_variant": "no_variant",
            "value_ids": [(0, 0, {"name": "160 cc 4V"})],
        })
        cls.moto = cls.env["product.template"].create({
            "name": "Moto Prueba 160",
            "categ_id": cls.line.id,
            "image_1920": PIXEL_PNG,
            "is_published": True,
            "attribute_line_ids": [
                (0, 0, {"attribute_id": color.id, "value_ids": [(6, 0, color.value_ids.ids)]}),
                (0, 0, {"attribute_id": motor.id, "value_ids": [(6, 0, motor.value_ids.ids)]}),
            ],
        })
        cls.red = color.value_ids.filtered(lambda v: v.name == "Rojo")
        attachments = cls.env["ir.attachment"].create([
            {"name": "moto.glb", "raw": FAKE_GLB, "res_model": "product.template", "res_id": cls.moto.id},
            {"name": "Motor prueba.png", "datas": PIXEL_PNG, "res_model": "product.template", "res_id": cls.moto.id},
            {"name": "factura.pdf", "raw": b"%PDF-1.4", "res_model": "product.template", "res_id": cls.moto.id},
        ])
        cls.glb, cls.spec_image, cls.pdf = attachments
        cls.other = cls.env["product.template"].create({"name": "Casco Prueba", "image_1920": PIXEL_PNG})

        # Otra línea con su propio diseño, y una subcategoría suya sin página maestra (hereda la de su padre).
        line_master = cls.env["ir.ui.view"].create({
            "name": "Moto maestra línea 2", "type": "qweb", "key": "website.test-moto-master-2",
            "arch": MASTER_ARCH.replace("website.test-moto-master", "website.test-moto-master-2")
                               .replace('class="oe_structure"', 'class="oe_structure o_diseno_linea_2"'),
            "website_id": website.id,
        })
        cls.line_page = cls.env["website.page"].create({
            "view_id": line_master.id, "url": "/test-moto-master-2", "website_id": website.id,
        })
        cls.line2 = cls.env["product.category"].create({
            "name": "Línea Dos", "parent_id": root.id, "moto_master_page_id": cls.line_page.id,
        })
        cls.line2_child = cls.env["product.category"].create({"name": "Línea Dos Sport", "parent_id": cls.line2.id})
        cls.moto2 = cls.env["product.template"].create({"name": "Moto Dos", "categ_id": cls.line2.id})
        cls.moto3 = cls.env["product.template"].create({"name": "Moto Tres", "categ_id": cls.line2_child.id})

    def _wrap(self, response):
        self.assertEqual(response.status_code, 200)
        return response.text[response.text.index('<div id="wrap"'):response.text.index("</main>")].replace("&amp;", "&")

    def test_page_uses_master_design_with_product_data(self):
        wrap = self._wrap(self.url_open(self.moto._moto_url()))
        self.assertNotIn("DISEÑO", wrap.upper())
        self.assertIn('<h1><span class="display-1-fs"><strong>MOTO PRUEBA 160</strong></span></h1>', wrap)
        self.assertIn('<span class="o_small-fs">Moto Prueba 160</span>', wrap)
        self.assertIn('<font style="color: red;">LÍNEA PRUEBA</font>', wrap)
        # Opciones del diseño que se conservan y archivos del producto.
        self.assertIn('data-model-yaw="180"', wrap)
        self.assertIn(f'data-model-src="{self.moto._moto_image_url()}"', wrap)
        self.assertIn(f'data-model-src="{self.moto._moto_model_url()}"', wrap)
        # Una muestra por color, copiando la primera muestra del diseño.
        self.assertEqual(wrap.count("s_moto_360_swatch o_diseno"), 2)
        self.assertIn(f'data-color-name="Rojo" data-variant="Rojo" data-attribute-value-ids="{self.red.id}"', wrap)
        self.assertNotIn("/x.glb", wrap)
        # Una tarjeta por especificación, con el formato de la tarjeta «Motor» del diseño.
        self.assertEqual(wrap.count("o_diseno_col"), 1)
        self.assertNotIn("Sutil", wrap)
        self.assertIn('<strong>Motor prueba </strong><strong><font style="color: red;">160 cc 4V</font></strong>', wrap)
        self.assertIn(self.moto._moto_attachment_url(self.spec_image), wrap)
        self.assertIn("Especificaciones técnicas", wrap)
        # Formulario y enlaces.
        self.assertRegex(wrap, re.compile(r'<option[^>]*value="Moto Prueba 160"[^>]*selected'))
        self.assertNotIn("Opción 1", wrap)
        self.assertIn('href="#cotizar"', wrap)

    def test_page_cannot_be_saved_into_master(self):
        new_test_user(self.env, login="moto_designer", password="moto_designer",
                      groups="base.group_user,website.group_website_designer")
        self.authenticate("moto_designer", "moto_designer")
        wrap = self._wrap(self.url_open(self.moto._moto_url()))
        self.assertNotIn("data-oe-model", wrap)
        self.assertIn('href="/test-moto-master"', wrap)

    def test_mega_menu_lists_motos(self):
        html = self.url_open("/").text
        if "Modelos" not in html:
            self.skipTest("El sitio no tiene el mega menú «Modelos».")
        self.assertIn(self.moto._moto_url(), html)
        self.assertIn("Línea Prueba", html)
        self.assertNotIn("Casco Prueba", html)

    def test_only_motos_have_page(self):
        self.assertEqual(self.url_open(f"/moto/casco-prueba-{self.other.id}").status_code, 404)
        self.assertEqual(self.url_open(f"/moto/media/{self.other.id}/foto/imagen.png").status_code, 404)

    def test_old_slug_redirects(self):
        response = self.url_open(f"/moto/otro-nombre-{self.moto.id}", allow_redirects=False)
        self.assertEqual(response.status_code, 301)
        self.assertTrue(response.headers["Location"].endswith(self.moto._moto_url()))

    def test_media(self):
        image = self.url_open(self.moto._moto_image_url())
        self.assertEqual(image.status_code, 200)
        self.assertTrue(image.headers["Content-Type"].startswith("image/"))
        model = self.url_open(self.moto._moto_model_url())
        self.assertEqual(model.status_code, 200)
        self.assertEqual(model.headers["Content-Type"], "model/gltf-binary")
        # Los demás adjuntos del producto no se publican.
        self.assertEqual(self.url_open(self.moto._moto_attachment_url(self.pdf)).status_code, 404)

    def test_shop_links_use_moto_template(self):
        self.assertEqual(self.moto.website_url, self.moto._moto_url())
        self.assertTrue(self.moto.product_variant_ids[0].website_url.startswith(self.moto._moto_url()))
        self.assertTrue(self.other.website_url.startswith("/shop/"))
        response = self.url_open(f"/shop/{self.env['ir.http']._slug(self.moto)}", allow_redirects=False)
        self.assertEqual(response.status_code, 301)
        self.assertTrue(response.headers["Location"].endswith(self.moto._moto_url()))

    def test_each_category_uses_its_master_page(self):
        # Sin página maestra en su categoría: la general.
        self.assertNotIn("o_diseno_linea_2", self._wrap(self.url_open(self.moto._moto_url())))
        # Con página maestra propia, y en una subcategoría que no tiene: la de la categoría padre.
        for moto in (self.moto2, self.moto3):
            with self.subTest(moto=moto.name):
                wrap = self._wrap(self.url_open(moto._moto_url()))
                self.assertIn("o_diseno_linea_2", wrap)
                self.assertIn(moto.name.upper(), wrap)

    def test_colors_show_variant_photos_without_model(self):
        color = self.env["product.attribute"].create({
            "name": "Color fotos",
            "value_ids": [(0, 0, {"name": "Azul"}), (0, 0, {"name": "Blanco"})],
        })
        moto = self.env["product.template"].create({
            "name": "Moto Fotos",
            "categ_id": self.line.id,
            "image_1920": PIXEL_PNG,
            "attribute_line_ids": [(0, 0, {"attribute_id": color.id, "value_ids": [(6, 0, color.value_ids.ids)]})],
        })
        blue = moto.product_variant_ids.filtered(lambda v: v.product_template_attribute_value_ids.name == "Azul")
        blue.image_variant_1920 = PIXEL_PNG
        colors = {c["name"]: c for c in moto._moto_colors()}
        self.assertTrue(colors["Azul"]["image_url"])
        self.assertFalse(colors["Blanco"]["image_url"])

        wrap = self._wrap(self.url_open(moto._moto_url()))
        self.assertIn(f'data-color-name="Azul" data-model-src="{colors["Azul"]["image_url"]}"', wrap)
        self.assertNotIn('data-variant="Azul"', wrap)
        self.assertIn(f'data-color-name="Blanco" data-model-src="{moto._moto_image_url()}"', wrap)
        photo = self.url_open(colors["Azul"]["image_url"])
        self.assertEqual(photo.status_code, 200)
        self.assertTrue(photo.headers["Content-Type"].startswith("image/"))
