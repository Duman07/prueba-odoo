/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import {
    createMediaImage,
    createModelViewer,
    getBaseYaw,
    isImageSrc,
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
// Con una imagen en lugar de modelo, el giro se simula con perspectiva: la foto se inclina
// durante la fase de giro y vuelve a quedar de frente (ángulo máximo en grados).
const IMAGE_TURN_DEG = 12;

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
 * Bloque «Moto 3D»: carga el modelo (o una imagen) y reproduce la animación de entrada
 * (entrada, aceleración, giro a la derecha, frenada) al hacerse visible.
 * Emite el evento "moto-intro-phase" en cada cambio de fase.
 */
publicWidget.registry.MotoIntro3D = publicWidget.Widget.extend({
    selector: ".s_moto_3d",
    disabledInEditableMode: false,
    read_events: {
        "click .s_moto_3d_replay": "_onReplayClick",
    },

    async start() {
        await this._super(...arguments);
        this.stage = this.el.querySelector(".s_moto_3d_stage");
        // Con una secuencia de fotos 360° se usa la primera foto.
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
        this.el.classList.add("s_moto_has_model");

        const animate = this.el.dataset.motoIntro !== "false" && !this.editableMode && !prefersReducedMotion();
        if (!animate) {
            this._applyPose(introPose(INTRO_DURATION));
            return;
        }
        this._applyPose(introPose(0));
        try {
            await (this.isImage ? this.media.decode() : waitForModelLoad(this.media));
        } catch {
            this._applyPose(introPose(INTRO_DURATION));
            return;
        }
        if (this.isDestroyed()) {
            return;
        }
        this.observer = new IntersectionObserver((entries) => {
            if (entries.some((entry) => entry.isIntersecting)) {
                this.observer.disconnect();
                this.observer = null;
                this._playIntro();
            }
        }, { threshold: 0.35 });
        this.observer.observe(this.stage);
    },

    destroy() {
        if (this.frame) {
            cancelAnimationFrame(this.frame);
        }
        this.observer?.disconnect();
        this.replayButton?.remove();
        this.media?.remove();
        this.el.classList.remove("s_moto_has_model", "s_moto_error");
        this._super(...arguments);
    },

    _applyPose({ x, turn, dive, blur }) {
        const imageTilt = IMAGE_TURN_DEG * Math.sin((Math.PI * turn) / TURN_RIGHT_DEG);
        const imageTurn = this.isImage ? ` perspective(1200px) rotateY(${-imageTilt}deg)` : "";
        this.media.style.transform = `translate3d(${x}%, 0, 0) rotate(${dive}deg)${imageTurn}`;
        this.media.style.filter = blur > 0.1 ? `blur(${blur.toFixed(2)}px)` : "";
        if (!this.isImage) {
            this.media.setAttribute("orientation", `0deg 0deg ${this.baseYaw - turn}deg`);
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
                this._showReplayButton();
            }
        };
        this.frame = requestAnimationFrame(step);
    },

    _showReplayButton() {
        this.replayButton = document.createElement("button");
        this.replayButton.type = "button";
        this.replayButton.className = "btn btn-light s_moto_3d_replay";
        this.replayButton.textContent = "Repetir animación";
        this.stage.appendChild(this.replayButton);
    },

    _onReplayClick() {
        this._playIntro();
    },
});

export default publicWidget.registry.MotoIntro3D;
