/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

const STATES_URL = "/website_motos_alfa_showcase/colombia_states";
let statesPromise;

function loadColombiaStates() {
    statesPromise ||= fetch(STATES_URL).then((response) => {
        if (!response.ok) {
            throw new Error("No se pudieron cargar los departamentos");
        }
        return response.json();
    });
    statesPromise.catch(() => (statesPromise = undefined));
    return statesPromise;
}

/**
 * Formularios del sitio con el campo Estado (state_id): solo se atiende en Colombia,
 * así que la lista se limita a sus departamentos. Si el formulario no tiene campo País,
 * se envía Colombia en un campo oculto para que el registro quede con país.
 * En el editor no se aplica y destroy() deja el HTML como estaba, para no guardarlo filtrado.
 */
publicWidget.registry.MotoColombiaFormStates = publicWidget.Widget.extend({
    selector: ".s_website_form form, form.s_website_form",

    async start() {
        await this._super(...arguments);
        this.stateSelect = this.el.querySelector('select[name="state_id"]');
        if (!this.stateSelect) {
            return;
        }
        let data;
        try {
            data = await loadColombiaStates();
        } catch {
            return;
        }
        if (this.isDestroyed()) {
            return;
        }
        const allowed = new Set(data.state_ids.map(String));
        this.originalOptions = [...this.stateSelect.options];
        for (const option of this.originalOptions) {
            if (option.value && !allowed.has(option.value)) {
                option.remove();
            }
        }
        if (!this.el.querySelector('[name="country_id"]')) {
            this.countryInput = document.createElement("input");
            this.countryInput.type = "hidden";
            this.countryInput.name = "country_id";
            this.countryInput.value = String(data.country_id);
            this.el.appendChild(this.countryInput);
        }
    },

    destroy() {
        if (this.originalOptions) {
            const value = this.stateSelect.value;
            this.stateSelect.replaceChildren(...this.originalOptions);
            this.stateSelect.value = value;
        }
        this.countryInput?.remove();
        this._super(...arguments);
    },
});

export default publicWidget.registry.MotoColombiaFormStates;
