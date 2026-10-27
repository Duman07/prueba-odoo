from odoo import models 

class Website(models.Model):
    _inherit = "website"

    def _enumerate_pages(self, query_string=None, force=False):
        """Sitemap y sugerencias de enlaces sin el /shop/… de las motos: redirige a /moto/…, que ya está en la lista
        (sitemap_motos en controllers/motos.py). Se filtra aquí porque Odoo registra /shop/<producto> en tres
        controladores y cambiar el sitemap de uno solo no basta."""
        motos = {f"/shop/{self.env['ir.http']._slug(moto)}" for moto in self.env["product.template"]._moto_search()}
        for page in super()._enumerate_pages(query_string=query_string, force=force):
            if page["loc"] not in motos:
                yield page