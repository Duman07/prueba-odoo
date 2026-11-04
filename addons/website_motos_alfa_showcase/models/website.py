from urllib.parse import quote

from odoo import models

# [whatsApp] Número del botón flotante (con el indicativo de Colombia, sin «+» ni espacios). Solo se cambia aquí.
WHATSAPP_NUMBER = "573223995269"
WHATSAPP_DEFAULT_TEXT = "Hola Motos Alfa, estoy interesado en la moto"


class Website(models.Model):
    _inherit = "website"

    def _moto_whatsapp_url(self, moto=None):
        """Enlace del botón de WhatsApp (views/whatsapp_button.xml): en /moto/<moto> el mensaje lleva el nombre de la moto."""
        text = f"{WHATSAPP_DEFAULT_TEXT} {moto.name}" if moto else WHATSAPP_DEFAULT_TEXT
        return f"https://wa.me/{WHATSAPP_NUMBER}?text={quote(text)}"

    def _enumerate_pages(self, query_string=None, force=False):
        """Sitemap y sugerencias de enlaces sin el /shop/… de las motos: redirige a /moto/…, que ya está en la lista
        (sitemap_motos en controllers/motos.py). Se filtra aquí porque Odoo registra /shop/<producto> en tres
        controladores y cambiar el sitemap de uno solo no basta."""
        motos = {f"/shop/{self.env['ir.http']._slug(moto)}" for moto in self.env["product.template"]._moto_search()}
        for page in super()._enumerate_pages(query_string=query_string, force=force):
            if page["loc"] not in motos:
                yield page