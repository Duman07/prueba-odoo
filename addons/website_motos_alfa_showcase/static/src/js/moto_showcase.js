/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

/**
 * Fases previstas para la animación de entrada (se implementarán en una etapa posterior).
 */
export const INTRO_PHASES = Object.freeze(["enter", "accelerate", "turnRight", "brake", "settle"]);

/**
 * Punto de entrada de la ficha de producto.
 *
 * Por ahora solo localiza los contenedores reservados (data-moto-slot) y lee la
 * configuración. Las etapas siguientes completarán los métodos _mountModel,
 * _playIntro y _mount360 sin cambiar la plantilla.
 */
export const MotoShowcase = publicWidget.Widget.extend({
    selector: ".o_moto_showcase",

    async start() {
        await this._super(...arguments);
        this.slots = {};
        for (const el of this.el.querySelectorAll("[data-moto-slot]")) {
            this.slots[el.dataset.motoSlot] = el;
        }
        this.config = {
            modelSrc: this.el.dataset.modelSrc || "",
            reducedMotion: window.matchMedia("(prefers-reduced-motion: reduce)").matches,
        };
        this.el.classList.add("o_moto_showcase_ready");

        if (this.config.modelSrc) {
            await this._mountModel();
            await this._playIntro();
            await this._mount360();
        }
    },

    destroy() {
        this.el.classList.remove("o_moto_showcase_ready");
        this._super(...arguments);
    },

    /** Carga el modelo GLB/glTF en this.slots.model3d. */
    async _mountModel() {},

    /** Reproduce INTRO_PHASES; debe omitirse si this.config.reducedMotion. */
    async _playIntro() {},

    /** Activa rotación y acercamiento en this.slots.viewer360. */
    async _mount360() {},
});

publicWidget.registry.MotoShowcase = MotoShowcase;
