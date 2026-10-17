/** @odoo-module **/

import options from "@web_editor/js/editor/snippets.options";

/**
 * Opción «Ubicación en el modelo» de cada punto destacado del Visor 360°:
 * tras pulsar «Ubicar», un clic sobre el modelo guarda la posición 3D del punto.
 */
options.registry.MotoHotspotPosition = options.Class.extend({
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
        if (methodName === "pickPosition" || methodName === "clearPosition") {
            return "";
        }
        return this._super(...arguments);
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
