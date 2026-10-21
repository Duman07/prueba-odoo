/** @odoo-module **/

// <model-viewer> (Google, Apache-2.0) se sirve desde el módulo y solo se carga
// en las páginas que contienen un bloque de moto, no en todo el sitio.
const MODEL_VIEWER_URL = "/website_motos_alfa_showcase/static/lib/model-viewer/model-viewer.min.js";

let loadingPromise;

export function loadModelViewer() {
    if (customElements.get("model-viewer")) {
        return Promise.resolve();
    }
    if (!loadingPromise) {
        loadingPromise = new Promise((resolve, reject) => {
            const script = document.createElement("script");
            script.type = "module";
            script.src = MODEL_VIEWER_URL;
            script.onerror = () => {
                loadingPromise = undefined;
                script.remove();
                reject(new Error("No se pudo cargar model-viewer"));
            };
            document.head.appendChild(script);
            customElements.whenDefined("model-viewer").then(resolve);
        });
    }
    return loadingPromise;
}

/**
 * Crea un <model-viewer> a partir de los data-* del bloque.
 * La orientación (yaw) permite corregir modelos exportados con otro eje frontal.
 */
export function createModelViewer(blockEl, attributes = {}) {
    const viewer = document.createElement("model-viewer");
    viewer.setAttribute("src", blockEl.dataset.modelSrc.trim());
    viewer.setAttribute("alt", blockEl.dataset.modelAlt || "Motocicleta");
    viewer.setAttribute("orientation", `0deg 0deg ${getBaseYaw(blockEl)}deg`);
    viewer.setAttribute("shadow-intensity", "1");
    viewer.setAttribute("environment-image", "neutral");
    viewer.setAttribute("loading", "eager");
    for (const [name, value] of Object.entries(attributes)) {
        viewer.setAttribute(name, value);
    }
    return viewer;
}

const IMAGE_EXTENSIONS = /\.(png|jpe?g|webp|gif|avif)$/i;

/** Indica si la URL del bloque o del color apunta a una imagen en lugar de a un modelo 3D. */
export function isImageSrc(src) {
    const path = (src || "").trim().split(/[?#]/, 1)[0];
    try {
        return IMAGE_EXTENSIONS.test(decodeURIComponent(path));
    } catch {
        return IMAGE_EXTENSIONS.test(path);
    }
}

/** Imagen estática que ocupa el lugar del modelo cuando el archivo subido es una foto. */
export function createMediaImage(blockEl, src) {
    const img = document.createElement("img");
    img.className = "s_moto_media_img";
    img.src = src;
    img.alt = blockEl.dataset.modelAlt || "Motocicleta";
    img.decoding = "async";
    return img;
}

export function getBaseYaw(blockEl) {
    return parseFloat(blockEl.dataset.modelYaw) || 0;
}

export function prefersReducedMotion() {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function waitForModelLoad(viewer) {
    if (viewer.loaded) {
        return Promise.resolve();
    }
    return new Promise((resolve, reject) => {
        viewer.addEventListener("load", resolve, { once: true });
        viewer.addEventListener("error", reject, { once: true });
    });
}

/**
 * Valores de atributo del enlace de la tienda (/moto/...#attribute_values=19), que indican
 * el color elegido por el visitante en el bloque «Productos».
 */
export function hashAttributeValues() {
    const match = window.location.hash.match(/attribute_values=([\d,]+)/);
    return match ? match[1].split(",") : [];
}

/** Posición de la muestra de color del enlace de la tienda, o -1. */
export function linkedSwatchIndex(swatches) {
    const values = hashAttributeValues();
    if (!values.length) {
        return -1;
    }
    return swatches.findIndex((swatch) =>
        (swatch.dataset.attributeValueIds || "").split(",").some((id) => values.includes(id)));
}
