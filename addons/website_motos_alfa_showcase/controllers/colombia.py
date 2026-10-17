from odoo import http
from odoo.http import request


class ColombiaStates(http.Controller):

    @http.route("/website_motos_alfa_showcase/colombia_states", type="http", auth="public", methods=["GET"], readonly=True)
    def colombia_states(self, **kwargs):
        """País Colombia y sus departamentos, para limitar el campo Estado de los formularios del sitio."""
        country = request.env.ref("base.co").sudo()
        response = request.make_json_response({
            "country_id": country.id,
            "state_ids": country.state_ids.ids,
        })
        response.headers["Cache-Control"] = "public, max-age=3600"
        return response
