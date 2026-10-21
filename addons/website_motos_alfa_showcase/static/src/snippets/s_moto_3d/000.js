/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import {
    createMediaImage,
    createModelViewer,
    getBaseYaw,
    isImageSrc,
    linkedSwatchIndex,
    loadModelViewer,
    prefersReducedMotion,
    waitForModelLoad,
} from "@website_motos_alfa_showcase/js/model_viewer_loader";
import { parseFrames } from "@website_motos_alfa_showcase/js/frame_sequence";

// Línea de tiempo de la animación de entrada (ms desde el inicio).
const INTRO_TIMELINE = [
    { phase: "enter", until: 500 },
    { phase: "accelerate", until: 1200 },
    { phase: "turnRight", until: 2000 },
    { phase: "brake", until: 2600 },
];
const INTRO_DURATION = 2600;

// Recorrido horizontal en % del ancho del escenario.
const START_X = -110;
const TURN_START_X = -8;
const TURN_END_X = 4;
// Giro hacia la derecha del piloto: la moto queda en vista tres cuartos.
const TURN_RIGHT_DEG = 25;
// Cabeceo al frenar (compresión de la horquilla) y desenfoque de velocidad.
const BRAKE_DIVE_DEG = 1.5;
const MAX_BLUR_PX = 2;

const clamp01 = (value) => Math.min(1, Math.max(0, value));
const progress = (time, from, to) => clamp01((time - from) / (to - from));
const easeIn = (t) => t * t;
const easeOut = (t) => 1 - (1 - t) * (1 - t);
const easeInOut = (t) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);

function introPose(time) {
    if (time < 1200) {
        const p = easeIn(progress(time, 0, 1200));
        return { x: START_X + (TURN_START_X - START_X) * p, turn: 0, dive: 0, blur: MAX_BLUR_PX * p };
    }
    if (time < 2000) {
        const p = progress(time, 1200, 2000);
        return {
            x: TURN_START_X + (TURN_END_X - TURN_START_X) * p,
            turn: TURN_RIGHT_DEG * easeInOut(p),
            dive: 0,
            blur: MAX_BLUR_PX * (1 - p),
        };
    }
    const p = progress(time, 2000, INTRO_DURATION);
    return {
        x: TURN_END_X * (1 - easeOut(p)),
        turn: TURN_RIGHT_DEG,
        dive: BRAKE_DIVE_DEG * Math.sin(Math.PI * p),
        blur: 0,
    };
}

function phaseAt(time) {
    if (time >= INTRO_DURATION) {
        return "settle";
    }
    return INTRO_TIMELINE.find((step) => time < step.until).phase;
}

/**
 * Bloque «Moto 3D»: carga el modelo (o una imagen).
 * - Modelo 3D: al hacerse visible reproduce la entrada (entrada, aceleración, giro a la derecha y frenada)
 *   y emite "moto-intro-phase" en cada fase.
 * - Foto (o fotos 360°, de las que se usa la primera, de frente): foto fija, sin animación.
 * En la página de una moto, el color elegido cambia la foto: con los colores dentro de este bloque
 * o en el «Visor 360°» (evento "moto-color-change").
 */
publicWidget.registry.MotoIntro3D = publicWidget.Widget.extend({
    selector: ".s_moto_3d",
    disabledInEditableMode: false,
    read_events: {
        "click .s_moto_3d_replay": "_onReplayClick",
        "click .s_moto_360_swatch": "_onSwatchClick",
        "keydown .s_moto_360_swatch": "_onSwatchKeydown",
    },

    async start() {
        await this._super(...arguments);
        this.stage = this.el.querySelector(".s_moto_3d_stage");
        // Con una secuencia de fotos 360° se muestra la primera (de frente).
        const rawSrc = (this.el.dataset.modelSrc || "").trim();
        const src = parseFrames(rawSrc)[0] || rawSrc;
        if (!this.stage || !src) {
            return;
        }
        this.isImage = isImageSrc(src);
        if (this.isImage) {
            this.media = createMediaImage(this.el, src);
        } else {
            try {
                await loadModelViewer();
            } catch {
                this.el.classList.add("s_moto_error");
                return;
            }
            if (this.isDestroyed()) {
                return;
            }
            this.baseYaw = getBaseYaw(this.el);
            this.media = createModelViewer(this.el, {
                "camera-orbit": "0deg 80deg 105%",
                "interaction-prompt": "none",
                "disable-tap": "",
            });
        }
        this.stage.appendChild(this.media);
        if (this.isImage) {
            this._onColorChange = (ev) => this._showImage(ev.detail.src);
            document.addEventListener("moto-color-change", this._onColorChange);
        }
        this.el.classList.add("s_moto_has_model");

        this._setupSwatches();
        if (this.isImage) {
            return;
        }
        const animate = this.el.dataset.motoIntro !== "false" && !this.editableMode && !prefersReducedMotion();
        if (!animate) {
            this._applyPose(introPose(INTRO_DURATION));
            return;
        }
        this._applyPose(introPose(0));
        try {
            await waitForModelLoad(this.media);
        } catch {
            this._applyPose(introPose(INTRO_DURATION));
            return;
        }
        if (this.isDestroyed()) {
            return;
        }
        this._playWhenVisible(() => this._playIntro());
    },

    destroy() {
        // Deja el HTML como estaba para que el editor no guarde estados de visualización.
        for (const swatch of this.swatches || []) {
            swatch.classList.remove("active");
            for (const attribute of ["role", "tabindex", "aria-pressed", "aria-label"]) {
                swatch.removeAttribute(attribute);
            }
        }
        if (this.colorNameEl && this.initialColorName !== undefined) {
            this.colorNameEl.textContent = this.initialColorName;
        }
        if (this._onColorChange) {
            document.removeEventListener("moto-color-change", this._onColorChange);
        }
        if (this.frame) {
            cancelAnimationFrame(this.frame);
        }
        this.observer?.disconnect();
        this.replayButton?.remove();
        this.media?.remove();
        this.el.classList.remove("s_moto_has_model", "s_moto_error");
        this._super(...arguments);
    },

    _playWhenVisible(play) {
        this.observer = new IntersectionObserver((entries) => {
            if (entries.some((entry) => entry.isIntersecting)) {
                this.observer.disconnect();
                this.observer = null;
                play();
            }
        }, { threshold: 0.35 });
        this.observer.observe(this.stage);
    },

    _applyPose({ x, turn, dive, blur }) {
        this.media.style.transform = `translate3d(${x}%, 0, 0) rotate(${dive}deg)`;
        this.media.style.filter = blur > 0.1 ? `blur(${blur.toFixed(2)}px)` : "";
        this.media.setAttribute("orientation", `0deg 0deg ${this.baseYaw - turn}deg`);
    },

    /**
     * Colores movidos a este bloque (panel «Colores» del Visor 360°): al elegir uno se muestran sus fotos.
     * Abre en el color del enlace de la tienda (#attribute_values=…) o en el primero.
     */
    _setupSwatches() {
        this.swatches = [...this.el.querySelectorAll(".s_moto_360_swatch")];
        this.colorNameEl = this.el.querySelector(".s_moto_360_color_name");
        this.initialColorName = this.colorNameEl?.textContent;
        if (this.editableMode || !this.swatches.length) {
            return;
        }
        this.swatches.forEach((swatch, index) => {
            swatch.setAttribute("role", "button");
            swatch.setAttribute("tabindex", "0");
            swatch.setAttribute("aria-label", swatch.dataset.colorName || `Color ${index + 1}`);
        });
        this._selectSwatch(Math.max(linkedSwatchIndex(this.swatches), 0));
    },

    _selectSwatch(index) {
        const swatch = this.swatches[index];
        this.swatches.forEach((el, i) => {
            el.classList.toggle("active", i === index);
            el.setAttribute("aria-pressed", i === index ? "true" : "false");
        });
        if (this.colorNameEl && swatch.dataset.colorName) {
            this.colorNameEl.textContent = swatch.dataset.colorName;
        }
        const src = swatch.dataset.mainSrc || swatch.dataset.modelSrc;
        if (this.isImage && src) {
            this._showImage(src);
        }
    },

    /** Color elegido: su foto (con fotos 360°, la primera, de frente). */
    _showImage(rawSrc) {
        const src = parseFrames(rawSrc)[0] || (rawSrc || "").trim();
        if (isImageSrc(src) && this.media.getAttribute("src") !== src) {
            this.media.src = src;
        }
    },

    _playIntro() {
        this.replayButton?.remove();
        this.replayButton = null;
        const startTime = performance.now();
        let currentPhase;
        const step = (now) => {
            const time = Math.min(now - startTime, INTRO_DURATION);
            this._applyPose(introPose(time));
            const phase = phaseAt(time);
            if (phase !== currentPhase) {
                currentPhase = phase;
                this.el.dispatchEvent(new CustomEvent("moto-intro-phase", { detail: { phase } }));
            }
            if (time < INTRO_DURATION) {
                this.frame = requestAnimationFrame(step);
            } else {
                this.frame = null;
                this._showReplayButton("Repetir animación");
            }
        };
        this.frame = requestAnimationFrame(step);
    },

    _showReplayButton(label) {
        this.replayButton = document.createElement("button");
        this.replayButton.type = "button";
        this.replayButton.className = "btn btn-light s_moto_3d_replay";
        this.replayButton.textContent = label;
        this.stage.appendChild(this.replayButton);
    },

    _onSwatchClick(ev) {
        this._selectSwatch(this.swatches.indexOf(ev.currentTarget));
    },

    _onSwatchKeydown(ev) {
        if (ev.key === "Enter" || ev.key === " ") {
            ev.preventDefault();
            ev.currentTarget.click();
        }
    },

    _onReplayClick() {
        this._playIntro();
    },
});

export default publicWidget.registry.MotoIntro3D;
