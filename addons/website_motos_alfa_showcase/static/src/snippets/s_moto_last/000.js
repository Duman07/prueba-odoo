/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

const CONTENT_URL = "/website_motos_alfa_showcase/last_moto";
// Última moto vista: {id, time} en el navegador del visitante. No va al servidor (no es una cookie).
const LAST_MOTO_KEY = "motos_alfa_last_moto";
const LAST_MOTO_MAX_AGE = 24 * 60 * 60 * 1000;

/** Id de la moto en /moto/<nombre>-<id> (también con idioma: /es/moto/...); en otras páginas no hay. */
function currentMotoId() {
    const match = window.location.pathname.match(/\/moto\/[^/]*-(\d+)\/?$/);
    return match ? match[1] : "";
}

/** Id de la última moto vista si fue hace menos de 24 horas; si es más vieja, se borra. */
function lastMotoId() {
    try {
        const last = JSON.parse(window.localStorage.getItem(LAST_MOTO_KEY));
        if (last && Date.now() - last.time < LAST_MOTO_MAX_AGE) {
            return String(last.id);
        }
        window.localStorage.removeItem(LAST_MOTO_KEY);
    } catch {
        // Navegador sin localStorage (ventana privada, datos bloqueados): no hay última moto.
    }
    return "";
}

// En la página de una moto: se guarda como la última vista, con la hora (cada visita la renueva).
const motoId = currentMotoId();
if (motoId) {
    try {
        window.localStorage.setItem(LAST_MOTO_KEY, JSON.stringify({ id: motoId, time: Date.now() }));
    } catch {
        // Sin localStorage no se recuerda nada.
    }
}

/**
 * Bloque «Última moto vista»: la foto en grande y el nombre de la moto que el visitante abrió en las últimas
 * 24 horas (los arma controllers/motos.py). Si no ha visto ninguna, el bloque queda oculto (s_moto_snippets.scss).
 * En el editor no se inicia y destroy() deja el aviso del bloque, para no guardar la moto en la página.
 */
publicWidget.registry.MotoLast = publicWidget.Widget.extend({
    selector: ".s_moto_last",

    async start() {
        await this._super(...arguments);
        this.content = this.el.querySelector(".s_moto_last_content");
        const lastId = lastMotoId();
        if (!this.content || !lastId) {
            return;
        }
        let motoHtml;
        try {
            const response = await fetch(`${CONTENT_URL}/${lastId}`);
            if (!response.ok) {
                throw new Error("No se pudo cargar la última moto vista");
            }
            motoHtml = await response.text();
        } catch {
            return;
        }
        if (this.isDestroyed()) {
            return;
        }
        this.originalChildren = [...this.content.childNodes];
        this.content.innerHTML = motoHtml;
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

export default publicWidget.registry.MotoLast;
