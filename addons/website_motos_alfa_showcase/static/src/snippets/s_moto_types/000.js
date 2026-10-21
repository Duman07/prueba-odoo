/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

const CONTENT_URL = "/website_motos_alfa_showcase/moto_types";

/** Id del tipo en /motos/<tipo>-<id> (también con idioma: /es/motos/...); en /motos no hay. */
function currentTypeId() {
    const match = window.location.pathname.match(/\/motos\/[^/]*-(\d+)\/?$/);
    return match ? match[1] : "";
}

/**
 * Bloque «Tipos de moto»: en /motos muestra los tipos (subcategorías de MOTOS) y en /motos/<tipo>
 * las motos de ese tipo. Las tarjetas las arma el servidor (controllers/motos.py).
 * En el editor no se inicia y destroy() deja el aviso del bloque, para no guardar las tarjetas en la página.
 */
publicWidget.registry.MotoTypes = publicWidget.Widget.extend({
    selector: ".s_moto_types",

    async start() {
        await this._super(...arguments);
        this.content = this.el.querySelector(".s_moto_types_content");
        if (!this.content) {
            return;
        }
        const typeId = currentTypeId();
        let cardsHtml;
        try {
            const response = await fetch(typeId ? `${CONTENT_URL}/${typeId}` : CONTENT_URL);
            if (!response.ok) {
                throw new Error("No se pudieron cargar los tipos de moto");
            }
            cardsHtml = await response.text();
        } catch {
            return;
        }
        if (this.isDestroyed()) {
            return;
        }
        this.originalChildren = [...this.content.childNodes];
        this.content.innerHTML = cardsHtml;
        this.el.classList.add("s_moto_has_content");
    },

    destroy() {
        if (this.originalChildren) {
            this.content.replaceChildren(...this.originalChildren);
        }
        this.el.classList.remove("s_moto_has_content");
        this._super(...arguments);
    },
});

export default publicWidget.registry.MotoTypes;
