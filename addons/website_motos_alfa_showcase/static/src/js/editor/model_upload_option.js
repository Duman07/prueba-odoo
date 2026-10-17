/** @odoo-module **/

import options from "@web_editor/js/editor/snippets.options";

const UPLOAD_URL = "/website_motos_alfa_showcase/upload_model";
// Debe coincidir con ALLOWED_TYPES de controllers/main.py.
const ACCEPTED_FILES = ".glb,.gltf,.png,.jpg,.jpeg,.webp,.gif,.avif";
const ACCEPTED_IMAGES = ".png,.jpg,.jpeg,.webp,.avif";
// Fotos que se suben a la vez al crear una secuencia 360°.
const PARALLEL_UPLOADS = 4;

/**
 * Botón «Subir archivo» de los bloques Moto 3D / Visor 360° y de cada color:
 * sube un modelo (.glb/.gltf) o una imagen como adjunto público y guarda su URL en data-model-src.
 * «Subir fotos 360°» sube varias fotos (ordenadas por nombre) y guarda sus URL separadas por espacios.
 */
options.registry.MotoModelUpload = options.Class.extend({
    init() {
        this._super(...arguments);
        this.notification = this.bindService("notification");
    },

    async uploadModel(previewMode) {
        if (previewMode) {
            return;
        }
        const file = await this._pickFile();
        if (!file) {
            return;
        }
        const closeProgress = this.notification.add(`Subiendo «${file.name}»…`, { type: "info", sticky: true });
        let result;
        try {
            result = await this._uploadFile(file);
        } catch (error) {
            closeProgress();
            this.notification.add(error.message, { type: "danger" });
            return;
        }
        closeProgress();
        await this._setSrc(result.url);
        this.notification.add(`${result.kind === "image" ? "Imagen" : "Modelo"} «${result.name}» subido.`, { type: "success" });
    },

    async uploadFrames(previewMode) {
        if (previewMode) {
            return;
        }
        // El orden de las fotos es el del giro: foto-01, foto-02… (orden natural, 2 antes que 10).
        const files = (await this._pickFiles(ACCEPTED_IMAGES, true)).sort((a, b) =>
            a.name.localeCompare(b.name, undefined, { numeric: true, sensitivity: "base" })
        );
        if (!files.length) {
            return;
        }
        if (files.length < 2) {
            this.notification.add("Selecciona todas las fotos del giro a la vez (al menos 2).", { type: "warning" });
            return;
        }
        let done = 0;
        const progressText = () => `Subiendo fotos 360°: ${done} de ${files.length}…`;
        let closeProgress = this.notification.add(progressText(), { type: "info", sticky: true });
        const urls = new Array(files.length);
        let next = 0;
        let failed = false;
        const worker = async () => {
            while (next < files.length) {
                const index = next++;
                const result = await this._uploadFile(files[index]);
                if (failed) {
                    return;
                }
                if (result.kind !== "image") {
                    throw new Error(`«${result.name}» no es una foto.`);
                }
                urls[index] = result.url;
                done++;
                closeProgress();
                closeProgress = this.notification.add(progressText(), { type: "info", sticky: true });
            }
        };
        try {
            await Promise.all(Array.from({ length: Math.min(PARALLEL_UPLOADS, files.length) }, worker));
        } catch (error) {
            failed = true;
            closeProgress();
            this.notification.add(error.message, { type: "danger" });
            return;
        }
        closeProgress();
        await this._setSrc(urls.join(" "));
        this.notification.add(`Vista 360° creada con ${files.length} fotos.`, { type: "success" });
    },

    _computeWidgetState(methodName) {
        if (methodName === "uploadModel" || methodName === "uploadFrames") {
            return "";
        }
        return this._super(...arguments);
    },

    async _uploadFile(file) {
        const body = new FormData();
        body.append("ufile", file);
        body.append("csrf_token", odoo.csrf_token);
        const response = await fetch(UPLOAD_URL, { method: "POST", body });
        const result = await response.json().catch(() => ({}));
        if (!response.ok || !result.url) {
            throw new Error(result.error || `No se pudo subir «${file.name}».`);
        }
        return result;
    },

    async _setSrc(src) {
        const target = this.$target[0];
        target.dataset.modelSrc = src;
        // Al subir el archivo de un color en un bloque sin archivo principal, también lo usa como principal.
        const block = target.closest(".s_moto_3d, .s_moto_360");
        if (block !== target && !(block.dataset.modelSrc || "").trim()) {
            block.dataset.modelSrc = src;
        }
        await this._refreshPublicWidgets($(block));
    },

    async _pickFile() {
        return (await this._pickFiles(ACCEPTED_FILES, false))[0] || null;
    },

    _pickFiles(accept, multiple) {
        return new Promise((resolve) => {
            const input = document.createElement("input");
            input.type = "file";
            input.accept = accept;
            input.multiple = multiple;
            input.addEventListener("change", () => resolve([...input.files]), { once: true });
            input.addEventListener("cancel", () => resolve([]), { once: true });
            input.click();
        });
    },
});
