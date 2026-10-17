from odoo import http
from odoo.tests import HttpCase, new_test_user, tagged

UPLOAD_URL = "/website_motos_alfa_showcase/upload_model"
FAKE_GLB = b"glTF" + b"\x02\x00\x00\x00" + b"\x00" * 64
FAKE_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
EMBEDDED_GLTF = b'{"asset": {"version": "2.0"}, "buffers": [{"uri": "data:application/octet-stream;base64,AAAA"}]}'
EXTERNAL_GLTF = b'{"asset": {"version": "2.0"}, "buffers": [{"uri": "moto.bin"}]}'


@tagged("post_install", "-at_install")
class TestModelUpload(HttpCase):

    def setUp(self):
        super().setUp()
        new_test_user(self.env, login="moto_designer", password="moto_designer",
                      groups="base.group_user,website.group_website_designer")
        new_test_user(self.env, login="moto_employee", password="moto_employee", groups="base.group_user")

    def _upload(self, content, name="hunk-150-xt-rojo.glb"):
        return self.url_open(
            UPLOAD_URL,
            data={"csrf_token": http.Request.csrf_token(self)},
            files={"ufile": (name, content, "application/octet-stream")},
        )

    def test_designer_upload_is_public(self):
        self.authenticate("moto_designer", "moto_designer")
        response = self._upload(FAKE_GLB)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        attachment = self.env["ir.attachment"].browse(result["id"])
        self.assertTrue(attachment.public)
        self.assertEqual(attachment.mimetype, "model/gltf-binary")

        self.authenticate(None, None)
        served = self.url_open(result["url"])
        self.assertEqual(served.status_code, 200)
        self.assertTrue(served.content.startswith(b"glTF"))

    def test_accepts_images_and_gltf(self):
        self.authenticate("moto_designer", "moto_designer")
        for content, name, mimetype, kind in [
            (FAKE_PNG, "hunk-roja.png", "image/png", "image"),
            (b"\xff\xd8\xff\xe0" + b"\x00" * 64, "hunk-roja.JPG", "image/jpeg", "image"),
            (b"RIFF\x00\x00\x00\x00WEBPVP8 " + b"\x00" * 64, "hunk-roja.webp", "image/webp", "image"),
            (EMBEDDED_GLTF, "hunk-roja.gltf", "model/gltf+json", "model"),
        ]:
            with self.subTest(name=name):
                response = self._upload(content, name=name)
                self.assertEqual(response.status_code, 200, response.text)
                result = response.json()
                self.assertEqual(result["kind"], kind)
                attachment = self.env["ir.attachment"].browse(result["id"])
                self.assertTrue(attachment.public)
                self.assertEqual(attachment.mimetype, mimetype)

    def test_rejects_invalid_files(self):
        self.authenticate("moto_designer", "moto_designer")
        self.assertEqual(self._upload(b"no es un modelo").status_code, 400)
        self.assertEqual(self._upload(FAKE_GLB, name="foto.png").status_code, 400)
        self.assertEqual(self._upload(FAKE_PNG, name="moto.glb").status_code, 400)
        self.assertEqual(self._upload(EXTERNAL_GLTF, name="moto.gltf").status_code, 400)
        self.assertEqual(self._upload(b"<svg></svg>", name="logo.svg").status_code, 400)
        self.assertEqual(self._upload(b"MZ", name="programa.exe").status_code, 400)

    def test_requires_website_editor(self):
        self.authenticate("moto_employee", "moto_employee")
        self.assertEqual(self._upload(FAKE_GLB).status_code, 403)
