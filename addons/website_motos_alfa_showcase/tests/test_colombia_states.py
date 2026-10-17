from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestColombiaStates(HttpCase):

    def test_returns_colombian_states(self):
        response = self.url_open("/website_motos_alfa_showcase/colombia_states")
        self.assertEqual(response.status_code, 200)
        result = response.json()
        colombia = self.env.ref("base.co")
        self.assertEqual(result["country_id"], colombia.id)
        self.assertEqual(set(result["state_ids"]), set(colombia.state_ids.ids))
        self.assertTrue(result["state_ids"])
