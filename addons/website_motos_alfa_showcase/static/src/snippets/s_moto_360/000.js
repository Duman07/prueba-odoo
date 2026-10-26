/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import {
    createMediaImage,
    createModelViewer,
    isImageSrc,
    linkedSwatchIndex,
    loadModelViewer,
    prefersReducedMotion,
    waitForModelLoad,
} from "@website_motos_alfa_showcase/js/model_viewer_loader";
import { FrameSequence, parseFrames } from "@website_motos_alfa_showcase/js/frame_sequence";

const INITIAL_ORBIT = "-30deg 75deg 105%";
const ZOOM_STEP = 3;
// Distancia de cámara al enfocar un punto destacado (% de la distancia ideal).
const HOTSPOT_RADIUS = "55%";

/**
 * Bloque «Visor 360°»: rotación con arrastre, acercamiento, giro automático,
 * pantalla completa, selector de colores y puntos destacados sobre el modelo.
 * Cada color (o el bloque) puede usar un modelo .glb/.gltf, una secuencia de fotos
 * tomadas alrededor de la moto (giro 360° con arrastre; cada punto destacado se ubica en una foto)
 * o una imagen (solo la vista estática y la pantalla completa).
 * En el editor se muestra sin interacción, pero con los puntos ya ubicados.
 */
publicWidget.registry.MotoViewer360 = publicWidget.Widget.extend({
    selector: ".s_moto_360",
    disabledInEditableMode: false,
    read_events: {
        "click .s_moto_360_autorotate": "_onAutoRotateClick",
        "click .s_moto_360_zoom_in": "_onZoomInClick",
        "click .s_moto_360_zoom_out": "_onZoomOutClick",
        "click .s_moto_360_reset": "_onResetClick",
        "click .s_moto_360_fullscreen": "_onFullscreenClick",
        "click .s_moto_360_swatch": "_onSwatchClick",
        "keydown .s_moto_360_swatch": "_onItemKeydown",
        "click .s_moto_360_hotspot": "_onHotspotClick",
        "keydown .s_moto_360_hotspot": "_onItemKeydown",
        "click .s_moto_360_marker": "_onMarkerClick",
    },

    async start() {
        await this._super(...arguments);
        this.viewerWrap = this.el.querySelector(".s_moto_360_viewer");
        this.autoRotateButton = this.el.querySelector(".s_moto_360_autorotate");
        this.initialPressed = this.autoRotateButton?.getAttribute("aria-pressed");
        this.swatches = [...this.el.querySelectorAll(".s_moto_360_swatch")];
        this.hotspots = [...this.el.querySelectorAll(".s_moto_360_hotspot")];
        this.colorNameEl = this.el.querySelector(".s_moto_360_color_name");
        this.initialColorName = this.colorNameEl?.textContent;
        this.markers = [];
        this.photoMarkers = [];
        this.autoRotate = this.el.dataset.autoRotate !== "false";
        // Avisos de la opción de los puntos en el editor (s_moto_360/options.js).
        this._onShowFrameEvent = (ev) => this._showFrame(ev.detail.frame, ev.detail.index);
        this._onPickPhotoEvent = (ev) => this._pickPhotoPoint(ev);
        this.el.addEventListener("moto-show-frame", this._onShowFrameEvent);
        this.el.addEventListener("moto-pick-photo", this._onPickPhotoEvent);

        const mainSrc = (this.el.dataset.modelSrc || "").trim();
        let linkedIndex = -1;
        if (!this.editableMode) {
            this._makeItemsInteractive();
            if (this.swatches.length) {
                linkedIndex = linkedSwatchIndex(this.swatches);
                const initial = this.swatches.findIndex((swatch) => mainSrc && swatch.dataset.modelSrc === mainSrc);
                this._selectSwatch(linkedIndex >= 0 ? linkedIndex : Math.max(initial, 0), false);
            }
        }
        if (!this.viewerWrap || !mainSrc) {
            return;
        }
        await this._showSrc(mainSrc);
        if (linkedIndex >= 0) {
            // La variante de material del color solo se conoce cuando termina de cargar el modelo.
            if (this.viewer && !this.viewer.classList.contains("d-none")) {
                try {
                    await waitForModelLoad(this.viewer);
                } catch {
                    return;
                }
            }
            if (!this.isDestroyed()) {
                await this._selectSwatch(linkedIndex);
            }
        }
    },

    destroy() {
        this.el.removeEventListener("moto-show-frame", this._onShowFrameEvent);
        this.el.removeEventListener("moto-pick-photo", this._onPickPhotoEvent);
        this.resizeObserver?.disconnect();
        this.viewer?.remove();
        this.image?.remove();
        this.sequence?.destroy();
        this.el.classList.remove("s_moto_has_model", "s_moto_error", "s_moto_360_image_mode", "s_moto_360_sequence_mode");
        if (this.autoRotateButton && this.initialPressed !== null) {
            this.autoRotateButton.setAttribute("aria-pressed", this.initialPressed);
            this.autoRotateButton.classList.remove("active");
        }
        // Deja el HTML como estaba para que el editor no guarde estados de visualización.
        for (const el of [...(this.swatches || []), ...(this.hotspots || [])]) {
            el.classList.remove("active");
            el.removeAttribute("role");
            el.removeAttribute("tabindex");
            el.removeAttribute("aria-pressed");
            el.removeAttribute("aria-label");
        }
        if (this.colorNameEl && this.initialColorName !== undefined) {
            this.colorNameEl.textContent = this.initialColorName;
        }
        this._super(...arguments);
    },

    /**
     * Muestra el archivo indicado: una secuencia de fotos, una imagen estática o el modelo 3D
     * (el <model-viewer> se crea la primera vez que hace falta).
     */
    async _showSrc(src) {
        const request = (this.showRequest = (this.showRequest || 0) + 1);
        const frames = parseFrames(src);
        if (frames.length) {
            this._showSequence(frames);
            return;
        }
        this._hideSequence();
        if (isImageSrc(src)) {
            if (!this.image) {
                this.image = createMediaImage(this.el, src);
                this.viewerWrap.appendChild(this.image);
            } else if (this.image.getAttribute("src") !== src) {
                this.image.src = src;
            }
            this.image.classList.remove("d-none");
            this.viewer?.classList.add("d-none");
            this.el.classList.add("s_moto_has_model", "s_moto_360_image_mode");
            return;
        }
        if (!this.viewer) {
            try {
                await loadModelViewer();
            } catch {
                this.el.classList.add("s_moto_error");
                return;
            }
            if (this.isDestroyed() || request !== this.showRequest) {
                return;
            }
            this._createViewer(src);
        } else if (src !== this.viewer.getAttribute("src")) {
            this.viewer.setAttribute("src", src);
        }
        this.viewer.classList.remove("d-none");
        this.image?.classList.add("d-none");
        this.el.classList.remove("s_moto_360_image_mode");
        this.el.classList.add("s_moto_has_model");
        this._updateAutoRotateButton(Boolean(this.viewer.autoRotate));
    },

    _showSequence(frames) {
        if (this.sequence?.frames.join(" ") !== frames.join(" ")) {
            this.sequence?.destroy();
            this.sequence = new FrameSequence(this.el, frames, {
                interactive: !this.editableMode,
                reverse: this.el.dataset.sequenceReverse === "true",
                onAutoRotateChange: (active) => this._updateAutoRotateButton(active),
                onRender: () => this._updatePhotoMarkers(),
            });
            this.viewerWrap.appendChild(this.sequence.el);
            this._renderPhotoMarkers();
            this.resizeObserver ||= new ResizeObserver(() => this._updatePhotoMarkers());
            this.resizeObserver.observe(this.sequence.el);
        }
        this.viewer?.classList.add("d-none");
        this.image?.classList.add("d-none");
        this.el.classList.remove("s_moto_360_image_mode");
        this.el.classList.add("s_moto_has_model", "s_moto_360_sequence_mode");
        const autoRotate = !this.editableMode && this.autoRotate && !prefersReducedMotion();
        if (this.sequence.autoRotate !== autoRotate) {
            this.sequence.setAutoRotate(autoRotate);
        } else {
            this._updateAutoRotateButton(autoRotate);
        }
    },

    _hideSequence() {
        this.sequence?.destroy();
        this.sequence = null;
        this.el.classList.remove("s_moto_360_sequence_mode");
    },

    _createViewer(src) {
        const autoRotate = this.autoRotate;
        const attributes = {
            "camera-orbit": INITIAL_ORBIT,
            "min-camera-orbit": "auto 20deg auto",
            "max-camera-orbit": "auto 100deg auto",
            "interaction-prompt": "auto",
            "touch-action": "pan-y",
            "rotation-per-second": "20deg",
            "auto-rotate-delay": "2000",
        };
        if (!this.editableMode) {
            attributes["camera-controls"] = "";
            if (autoRotate) {
                attributes["auto-rotate"] = "";
            }
        }
        attributes.src = src;
        this.viewer = createModelViewer(this.el, attributes);
        this._renderMarkers();
        this.viewerWrap.appendChild(this.viewer);
        this._updateAutoRotateButton(!this.editableMode && autoRotate);
    },

    _makeItemsInteractive() {
        this.swatches.forEach((swatch, index) => {
            swatch.setAttribute("role", "button");
            swatch.setAttribute("tabindex", "0");
            swatch.setAttribute("aria-label", swatch.dataset.colorName || `Color ${index + 1}`);
        });
        for (const item of this.hotspots) {
            item.setAttribute("role", "button");
            item.setAttribute("tabindex", "0");
        }
    },

    _renderMarkers() {
        this.hotspots.forEach((item, index) => {
            const position = (item.dataset.position || "").trim();
            if (!position) {
                return;
            }
            const marker = this._createMarker(item, index);
            marker.slot = `hotspot-${index}`;
            marker.dataset.position = position;
            marker.dataset.normal = item.dataset.normal || "0m 1m 0m";
            this.viewer.appendChild(marker);
            this.markers[index] = marker;
        });
    },

    /**
     * Círculo numerado de un punto destacado, con la burbuja de su título y descripción
     * (copiados del panel «Puntos destacados»); la burbuja se ve cuando el punto está activo.
     */
    _createMarker(item, index) {
        const title = item.querySelector("strong")?.textContent.trim() || `Punto ${index + 1}`;
        const marker = document.createElement("button");
        marker.type = "button";
        marker.className = "s_moto_360_marker";
        marker.dataset.index = String(index);
        marker.textContent = String(index + 1);
        marker.setAttribute("aria-label", title);
        const info = document.createElement("span");
        info.className = "s_moto_360_marker_info";
        const titleEl = document.createElement("strong");
        titleEl.textContent = title;
        const text = document.createElement("span");
        text.textContent = [...item.querySelectorAll("p")].slice(1).map((p) => p.textContent.trim()).join(" ");
        info.append(titleEl, text);
        marker.appendChild(info);
        return marker;
    },

    /**
     * Puntos sobre las fotos 360°: cada punto ubicado en una foto (data-frame, nº de foto desde 1;
     * data-frame-x y data-frame-y, % del ancho y del alto de la foto) tiene su círculo, que solo
     * se ve mientras se muestra esa foto.
     */
    _renderPhotoMarkers() {
        this.photoMarkers = [];
        this.hotspots.forEach((item, index) => {
            const frame = parseInt(item.dataset.frame, 10) - 1;
            const x = parseFloat(item.dataset.frameX);
            const y = parseFloat(item.dataset.frameY);
            if (!(frame >= 0) || Number.isNaN(x) || Number.isNaN(y)) {
                return;
            }
            const marker = this._createMarker(item, index);
            marker.classList.add("s_moto_360_photo_marker");
            // Cerca del borde derecho, la burbuja se abre hacia la izquierda.
            marker.classList.toggle("s_moto_360_marker_left", x > 60);
            // Tocar el punto no empieza a girar la moto.
            marker.addEventListener("pointerdown", (ev) => ev.stopPropagation());
            this.sequence.el.appendChild(marker);
            this.photoMarkers[index] = { marker, frame: frame % this.sequence.frames.length, x, y };
        });
        this._updatePhotoMarkers();
    },

    _updatePhotoMarkers() {
        if (!this.sequence) {
            return;
        }
        for (const point of this.photoMarkers) {
            if (!point) {
                continue;
            }
            const visible = this.sequence.index === point.frame;
            point.marker.classList.toggle("d-none", !visible);
            if (visible) {
                const { left, top } = this.sequence.pointToView(point.x, point.y);
                point.marker.style.left = `${left}px`;
                point.marker.style.top = `${top}px`;
            }
        }
    },

    _setActiveHotspot(index) {
        this.hotspots.forEach((el, i) => el.classList.toggle("active", i === index));
        this.markers.forEach((el, i) => el?.classList.toggle("active", i === index));
        this.photoMarkers.forEach((point, i) => point?.marker.classList.toggle("active", i === index));
    },

    /** Editor: muestra la foto del punto elegido en el panel (frame desde 0) y su burbuja. */
    _showFrame(frame, index) {
        if (!this.sequence) {
            return;
        }
        this.sequence.setFrame(frame);
        this._setActiveHotspot(index);
    },

    /** Editor, «Ubicar» en la foto: muestra esa foto y espera el clic (ver FrameSequence.pickPoint). */
    _pickPhotoPoint(ev) {
        if (!this.sequence) {
            return;
        }
        const { frame, index, resolve } = ev.detail;
        ev.detail.handled = true;
        this._showFrame(frame, index);
        this.sequence.pickPoint().then(resolve);
    },

    _updateAutoRotateButton(active) {
        this.autoRotateButton?.setAttribute("aria-pressed", active ? "true" : "false");
        this.autoRotateButton?.classList.toggle("active", active);
    },

    async _selectSwatch(index, applyToModel = true) {
        const swatch = this.swatches[index];
        this.swatches.forEach((el, i) => {
            el.classList.toggle("active", i === index);
            el.setAttribute("aria-pressed", i === index ? "true" : "false");
        });
        if (this.colorNameEl && swatch.dataset.colorName) {
            this.colorNameEl.textContent = swatch.dataset.colorName;
        }
        if ("mainSrc" in swatch.dataset) {
            // Página de una moto: el color solo cambia la imagen principal («Moto 3D»); el visor no cambia.
            this.el.dispatchEvent(new CustomEvent("moto-color-change", {
                bubbles: true,
                detail: { src: swatch.dataset.mainSrc },
            }));
            return;
        }
        if (!applyToModel || !this.el.classList.contains("s_moto_has_model")) {
            return;
        }
        // Un color puede tener su propio archivo (modelo o imagen) o usar una variante de material del modelo.
        const src = (swatch.dataset.modelSrc || this.el.dataset.modelSrc || "").trim();
        if (src) {
            await this._showSrc(src);
        }
        if (swatch.dataset.modelSrc && isImageSrc(src)) {
            // La foto del color también se muestra en el bloque «Moto 3D» de la página.
            this.el.dispatchEvent(new CustomEvent("moto-color-change", { bubbles: true, detail: { src } }));
        }
        const variant = (swatch.dataset.variant || "").trim();
        if (variant && this.viewer && !isImageSrc(src) && this.viewer.availableVariants?.includes(variant)) {
            this.viewer.variantName = variant;
        }
    },

    _focusHotspot(index) {
        this._setActiveHotspot(index);
        if (this.sequence) {
            // Fotos 360°: gira hasta la foto donde está el punto (su círculo y burbuja aparecen ahí).
            const point = this.photoMarkers[index];
            if (point) {
                this.sequence.setAutoRotate(false);
                this.sequence.setFrame(point.frame);
            }
            return;
        }
        const marker = this.markers[index];
        if (!marker || !this.viewer) {
            return;
        }
        this.viewer.autoRotate = false;
        this._updateAutoRotateButton(false);
        const orbit = this.viewer.getCameraOrbit();
        this.viewer.cameraTarget = marker.dataset.position;
        this.viewer.cameraOrbit = `${orbit.theta}rad ${orbit.phi}rad ${HOTSPOT_RADIUS}`;
    },

    _onAutoRotateClick() {
        if (this.sequence) {
            this.sequence.setAutoRotate(!this.sequence.autoRotate);
            return;
        }
        if (!this.viewer) {
            return;
        }
        this.viewer.autoRotate = !this.viewer.autoRotate;
        this._updateAutoRotateButton(this.viewer.autoRotate);
    },

    _onZoomInClick() {
        if (this.sequence) {
            this.sequence.zoomBy(1);
        } else {
            this.viewer?.zoom(ZOOM_STEP);
        }
    },

    _onZoomOutClick() {
        if (this.sequence) {
            this.sequence.zoomBy(-1);
        } else {
            this.viewer?.zoom(-ZOOM_STEP);
        }
    },

    _onResetClick() {
        this._setActiveHotspot(-1);
        if (this.sequence) {
            this.sequence.reset();
            return;
        }
        if (!this.viewer) {
            return;
        }
        this.viewer.cameraOrbit = INITIAL_ORBIT;
        this.viewer.cameraTarget = "auto auto auto";
        this.viewer.fieldOfView = "auto";
        this.viewer.resetTurntableRotation?.();
    },

    _onFullscreenClick() {
        if (document.fullscreenElement) {
            document.exitFullscreen();
        } else {
            this.viewerWrap.requestFullscreen?.();
        }
    },

    _onSwatchClick(ev) {
        this._selectSwatch(this.swatches.indexOf(ev.currentTarget));
    },

    _onHotspotClick(ev) {
        this._focusHotspot(this.hotspots.indexOf(ev.currentTarget));
    },

    _onMarkerClick(ev) {
        this._focusHotspot(parseInt(ev.currentTarget.dataset.index, 10));
    },

    _onItemKeydown(ev) {
        if (ev.key === "Enter" || ev.key === " ") {
            ev.preventDefault();
            ev.currentTarget.click();
        }
    },
});

export default publicWidget.registry.MotoViewer360;
