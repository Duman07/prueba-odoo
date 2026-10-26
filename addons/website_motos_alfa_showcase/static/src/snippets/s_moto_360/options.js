/** @odoo-module **/

import options from "@web_editor/js/editor/snippets.options";

/**
 * Opciones de cada punto destacado del Visor 360°:
 * - «Foto n.º» + «Ubicar en la foto»: con fotos 360°, un clic sobre esa foto guarda dónde está el punto
 *   (data-frame, data-frame-x, data-frame-y). El widget (s_moto_360/000.js) muestra la foto y espera el clic.
 * - «Ubicación en el modelo 3D»: tras pulsar «Ubicar», un clic sobre el modelo guarda la posición 3D del punto.
 */
options.registry.MotoHotspotPosition = options.Class.extend({
    /** Al elegir el punto en el editor, el visor muestra su foto. */
    onFocus() {
        this._super(...arguments);
        this._showFrame();
    },

    async selectDataAttribute(previewMode, widgetValue, params) {
        await this._super(...arguments);
        if (params.attributeName === "frame" && !previewMode) {
            await this._refreshPublicWidgets($(this.$target[0].closest(".s_moto_360")));
            this._showFrame();
        }
    },

    async pickPhotoPosition(previewMode) {
        if (previewMode) {
            return;
        }
        const target = this.$target[0];
        const block = target.closest(".s_moto_360");
        const frame = this._frameIndex();
        const point = await this._askViewer(block, "moto-pick-photo", { frame, index: this._hotspotIndex() });
        if (!point) {
            return;
        }
        target.dataset.frame = String(frame + 1);
        target.dataset.frameX = point.x.toFixed(2);
        target.dataset.frameY = point.y.toFixed(2);
        await this._refreshPublicWidgets($(block));
        this._showFrame();
    },

    async clearPhotoPosition(previewMode) {
        if (previewMode) {
            return;
        }
        delete this.$target[0].dataset.frameX;
        delete this.$target[0].dataset.frameY;
        await this._refreshPublicWidgets($(this.$target[0].closest(".s_moto_360")));
        this._showFrame();
    },

    async pickPosition(previewMode) {
        if (previewMode) {
            return;
        }
        const block = this.$target[0].closest(".s_moto_360");
        const viewer = block?.querySelector("model-viewer");
        if (!viewer) {
            return;
        }
        const hit = await this._waitForModelClick(viewer);
        if (!hit) {
            return;
        }
        this.$target[0].dataset.position = hit.position.toString();
        this.$target[0].dataset.normal = hit.normal.toString();
        await this._refreshPublicWidgets($(block));
    },

    async clearPosition(previewMode) {
        if (previewMode) {
            return;
        }
        delete this.$target[0].dataset.position;
        delete this.$target[0].dataset.normal;
        await this._refreshPublicWidgets($(this.$target[0].closest(".s_moto_360")));
    },

    _computeWidgetState(methodName) {
        if (["pickPosition", "clearPosition", "pickPhotoPosition", "clearPhotoPosition"].includes(methodName)) {
            return "";
        }
        return this._super(...arguments);
    },

    /** «Foto n.º» del punto (desde 1 en el panel) → índice de la foto (desde 0). */
    _frameIndex() {
        return Math.max((parseInt(this.$target[0].dataset.frame, 10) || 1) - 1, 0);
    },

    _hotspotIndex() {
        const block = this.$target[0].closest(".s_moto_360");
        return [...block.querySelectorAll(".s_moto_360_hotspot")].indexOf(this.$target[0]);
    },

    _showFrame() {
        const block = this.$target[0].closest(".s_moto_360");
        if (block) {
            this._askViewer(block, "moto-show-frame", { frame: this._frameIndex(), index: this._hotspotIndex() });
        }
    },

    /**
     * Envía un aviso al widget del bloque (dentro del iframe del editor) y espera su respuesta.
     * Si el bloque no muestra fotos 360°, nadie lo atiende y se devuelve null.
     */
    _askViewer(block, name, detail) {
        const win = block.ownerDocument.defaultView;
        return new Promise((resolve) => {
            const event = new win.CustomEvent(name, { detail: { ...detail, resolve } });
            block.dispatchEvent(event);
            if (!event.detail.handled) {
                resolve(null);
            }
        });
    },

    /**
     * Espera un clic sobre el modelo (dentro del iframe del editor) y devuelve
     * su posición y normal. Un clic fuera del modelo o Escape cancelan.
     */
    _waitForModelClick(viewer) {
        const win = viewer.ownerDocument.defaultView;
        const wrap = viewer.closest(".s_moto_360_viewer");
        wrap.classList.add("s_moto_360_picking");
        return new Promise((resolve) => {
            const isOnModel = (ev) => ev.composedPath().includes(viewer);
            const block = (ev) => {
                if (isOnModel(ev)) {
                    ev.preventDefault();
                    ev.stopPropagation();
                }
            };
            const finish = (result) => {
                win.removeEventListener("mousedown", block, true);
                win.removeEventListener("click", onClick, true);
                win.removeEventListener("keydown", onKeydown, true);
                wrap.classList.remove("s_moto_360_picking");
                resolve(result);
            };
            const onClick = (ev) => {
                if (!isOnModel(ev)) {
                    finish(null);
                    return;
                }
                ev.preventDefault();
                ev.stopPropagation();
                finish(viewer.positionAndNormalFromPoint(ev.clientX, ev.clientY));
            };
            const onKeydown = (ev) => {
                if (ev.key === "Escape") {
                    finish(null);
                }
            };
            win.addEventListener("mousedown", block, true);
            win.addEventListener("click", onClick, true);
            win.addEventListener("keydown", onKeydown, true);
        });
    },
});
