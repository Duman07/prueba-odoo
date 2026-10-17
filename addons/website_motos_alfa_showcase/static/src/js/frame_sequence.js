/** @odoo-module **/

// Una vuelta completa del giro automático dura esto, sin importar cuántas fotos haya.
const AUTO_ROTATE_TURN_MS = 4800;
// Tras soltar el arrastre, el giro automático se reanuda pasado este tiempo (como en <model-viewer>).
const AUTO_ROTATE_RESUME_MS = 2000;
const MAX_ZOOM = 3;
const ZOOM_FACTOR = 1.25;

/**
 * Lista de fotos de un giro 360°: data-model-src con varias URL separadas por espacios
 * (las URL de /web/content llevan los espacios codificados). Devuelve [] si no es una secuencia.
 */
export function parseFrames(src) {
    const frames = (src || "").trim().split(/\s+/).filter(Boolean);
    return frames.length > 1 ? frames : [];
}

/**
 * Vista 360° a partir de fotos tomadas alrededor de la moto: arrastrar recorre las fotos
 * (todo el ancho del visor = una vuelta), con giro automático, zoom y teclado (flechas).
 */
export class FrameSequence {
    constructor(blockEl, frames, { interactive = true, reverse = false, onAutoRotateChange } = {}) {
        this.frames = frames;
        this.interactive = interactive;
        this.direction = reverse ? -1 : 1;
        this.onAutoRotateChange = onAutoRotateChange;
        this.index = 0;
        this.zoom = 1;
        this.autoRotate = false;

        this.el = document.createElement("div");
        this.el.className = "s_moto_360_sequence";
        this.img = document.createElement("img");
        this.img.className = "s_moto_media_img";
        this.img.alt = blockEl.dataset.modelAlt || "Motocicleta";
        this.img.draggable = false;
        this.img.src = frames[0];
        this.el.appendChild(this.img);

        // Precarga todas las fotos para que el giro no parpadee.
        this.preloaded = frames.map((url) => {
            const image = new Image();
            image.decoding = "async";
            image.src = url;
            return image;
        });

        if (interactive) {
            this.el.tabIndex = 0;
            this.el.setAttribute("role", "slider");
            this.el.setAttribute("aria-label", "Vista 360°: usa las flechas para girar");
            this.el.setAttribute("aria-valuemin", "1");
            this.el.setAttribute("aria-valuemax", String(frames.length));
            this._bindEvents();
        }
        this._render();
    }

    destroy() {
        this.setAutoRotate(false);
        clearTimeout(this.resumeTimer);
        this.el.remove();
    }

    setFrame(index) {
        const count = this.frames.length;
        this.index = ((Math.round(index) % count) + count) % count;
        this._render();
    }

    setAutoRotate(active) {
        clearInterval(this.autoRotateTimer);
        this.autoRotateTimer = null;
        this.autoRotate = active;
        if (active) {
            const delay = AUTO_ROTATE_TURN_MS / this.frames.length;
            this.autoRotateTimer = setInterval(() => this.setFrame(this.index + this.direction), delay);
        }
        this.onAutoRotateChange?.(active);
    }

    zoomBy(steps) {
        this.zoom = Math.min(MAX_ZOOM, Math.max(1, this.zoom * ZOOM_FACTOR ** steps));
        this._render();
    }

    reset() {
        this.zoom = 1;
        this.setFrame(0);
    }

    _render() {
        this.img.src = this.frames[this.index];
        this.img.style.transform = this.zoom === 1 ? "" : `scale(${this.zoom})`;
        if (this.interactive) {
            this.el.setAttribute("aria-valuenow", String(this.index + 1));
        }
    }

    _bindEvents() {
        // Un dedo (o el ratón) gira; dos dedos hacen zoom (pellizco).
        const pointers = new Map();
        let start = null;
        let pinch = null;
        const distance = () => {
            const [a, b] = [...pointers.values()];
            return Math.hypot(a.x - b.x, a.y - b.y) || 1;
        };
        this.el.addEventListener("pointerdown", (ev) => {
            if (ev.button !== 0) {
                return;
            }
            pointers.set(ev.pointerId, { x: ev.clientX, y: ev.clientY });
            this.el.setPointerCapture(ev.pointerId);
            if (pointers.size === 2) {
                pinch = { distance: distance(), zoom: this.zoom };
                // Tras el pellizco, el dedo que queda no gira la moto.
                if (start) {
                    start.locked = true;
                }
                return;
            }
            if (pointers.size > 2) {
                return;
            }
            start = { x: ev.clientX, index: this.index, wasRotating: this.autoRotate };
            clearTimeout(this.resumeTimer);
            if (this.autoRotate) {
                this.setAutoRotate(false);
            }
            this.el.classList.add("s_moto_360_dragging");
        });
        this.el.addEventListener("pointermove", (ev) => {
            if (!pointers.has(ev.pointerId)) {
                return;
            }
            pointers.set(ev.pointerId, { x: ev.clientX, y: ev.clientY });
            if (pinch) {
                this.zoom = Math.min(MAX_ZOOM, Math.max(1, pinch.zoom * (distance() / pinch.distance)));
                this._render();
                return;
            }
            if (!start || start.locked) {
                return;
            }
            const pxPerFrame = this.el.clientWidth / this.frames.length;
            this.setFrame(start.index - this.direction * ((ev.clientX - start.x) / pxPerFrame));
        });
        const end = (ev) => {
            pointers.delete(ev.pointerId);
            if (pointers.size < 2) {
                pinch = null;
            }
            if (pointers.size || !start) {
                return;
            }
            if (start.wasRotating) {
                this.resumeTimer = setTimeout(() => this.setAutoRotate(true), AUTO_ROTATE_RESUME_MS);
            }
            start = null;
            this.el.classList.remove("s_moto_360_dragging");
        };
        this.el.addEventListener("pointerup", end);
        this.el.addEventListener("pointercancel", end);
        this.el.addEventListener("wheel", (ev) => {
            ev.preventDefault();
            this.zoomBy(ev.deltaY < 0 ? 1 : -1);
        }, { passive: false });
        this.el.addEventListener("keydown", (ev) => {
            const step = { ArrowLeft: 1, ArrowRight: -1 }[ev.key];
            if (step) {
                ev.preventDefault();
                this.setAutoRotate(false);
                this.setFrame(this.index + this.direction * step);
            }
        });
    }
}
