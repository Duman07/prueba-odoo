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
    constructor(blockEl, frames, { interactive = true, reverse = false, onAutoRotateChange, onRender } = {}) {
        this.frames = frames;
        this.interactive = interactive;
        this.direction = reverse ? -1 : 1;
        this.onAutoRotateChange = onAutoRotateChange;
        // Se llama al cambiar de foto o de zoom (y al cargar cada foto), para mover los puntos destacados.
        this.onRender = onRender;
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
        this.img.addEventListener("load", () => this.onRender?.());
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
        this.onRender?.();
    }

    /**
     * Rectángulo de la foto dentro del visor, sin zoom: la foto se ve completa (object-fit: contain),
     * así que puede dejar franjas a los lados o arriba y abajo.
     */
    _photoBox() {
        const width = this.el.clientWidth;
        const height = this.el.clientHeight;
        const naturalWidth = this.img.naturalWidth || width;
        const naturalHeight = this.img.naturalHeight || height;
        const scale = Math.min(width / naturalWidth, height / naturalHeight);
        const boxWidth = naturalWidth * scale;
        const boxHeight = naturalHeight * scale;
        return { left: (width - boxWidth) / 2, top: (height - boxHeight) / 2, width: boxWidth, height: boxHeight };
    }

    /**
     * Punto de la foto (x, y en % de su ancho y alto) → posición en px dentro del visor, con el zoom
     * aplicado (el zoom agranda la foto desde el centro del visor).
     */
    pointToView(x, y) {
        const box = this._photoBox();
        const centerX = this.el.clientWidth / 2;
        const centerY = this.el.clientHeight / 2;
        return {
            left: centerX + (box.left + (x / 100) * box.width - centerX) * this.zoom,
            top: centerY + (box.top + (y / 100) * box.height - centerY) * this.zoom,
        };
    }

    /** Lo contrario: un clic en la pantalla → punto de la foto en %, o null si cae fuera de la foto. */
    viewToPoint(clientX, clientY) {
        const rect = this.el.getBoundingClientRect();
        const box = this._photoBox();
        const centerX = this.el.clientWidth / 2;
        const centerY = this.el.clientHeight / 2;
        const viewX = centerX + (clientX - rect.left - centerX) / this.zoom;
        const viewY = centerY + (clientY - rect.top - centerY) / this.zoom;
        const x = ((viewX - box.left) / box.width) * 100;
        const y = ((viewY - box.top) / box.height) * 100;
        return x < 0 || x > 100 || y < 0 || y > 100 ? null : { x, y };
    }

    /**
     * Editor, «Ubicar en la foto»: espera un clic sobre la foto y devuelve el punto en %.
     * Un clic fuera de la foto o Escape cancelan (null).
     */
    pickPoint() {
        const doc = this.el.ownerDocument;
        const wrap = this.el.parentElement;
        wrap?.classList.add("s_moto_360_picking");
        return new Promise((resolve) => {
            const isOnPhoto = (ev) => this.el.contains(ev.target);
            const block = (ev) => {
                if (isOnPhoto(ev)) {
                    ev.preventDefault();
                    ev.stopPropagation();
                }
            };
            const finish = (point) => {
                doc.removeEventListener("mousedown", block, true);
                doc.removeEventListener("click", onClick, true);
                doc.removeEventListener("keydown", onKeydown, true);
                wrap?.classList.remove("s_moto_360_picking");
                resolve(point);
            };
            const onClick = (ev) => {
                if (!isOnPhoto(ev)) {
                    finish(null);
                    return;
                }
                ev.preventDefault();
                ev.stopPropagation();
                finish(this.viewToPoint(ev.clientX, ev.clientY));
            };
            const onKeydown = (ev) => {
                if (ev.key === "Escape") {
                    finish(null);
                }
            };
            doc.addEventListener("mousedown", block, true);
            doc.addEventListener("click", onClick, true);
            doc.addEventListener("keydown", onKeydown, true);
        });
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
