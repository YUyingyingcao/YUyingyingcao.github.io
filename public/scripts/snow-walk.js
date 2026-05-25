(() => {
  const scene = document.querySelector("[data-snow-walk]");
  const person = document.querySelector("[data-snow-walk-person]");
  const notes = Array.from(document.querySelectorAll("[data-walk-note]"));
  if (!scene || !person) return;

  const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
  const easeInOut = (value) => (value < 0.5 ? 2 * value * value : 1 - Math.pow(-2 * value + 2, 2) / 2);
  const lerp = (from, to, amount) => from + (to - from) * amount;
  const P2_END_RAW = 0.74;
  const P3_FULL_RAW = 0.94;
  const P3_REVEAL_START_RAW = 0.765;
  const SNAP_EDGE = 0.012;
  const P2_END_EPSILON = 0.002;
  let lastRaw = -1;
  let lastWidth = 0;
  let lastHeight = 0;
  let isWalkSnapping = false;
  let snapFrame = 0;
  let snapExpectedY = 0;
  let p2EndReady = false;

  function updateWalk() {
    const rect = scene.getBoundingClientRect();
    const travel = Math.max(1, rect.height - window.innerHeight);
    const raw = clamp(-rect.top / travel, 0, 1);
    const vw = window.innerWidth;
    const vh = window.innerHeight;

    if (
      Math.abs(raw - lastRaw) < 0.0005 &&
      vw === lastWidth &&
      vh === lastHeight
    ) {
      return;
    }

    lastRaw = raw;
    lastWidth = vw;
    lastHeight = vh;

    if (raw < P2_END_RAW - SNAP_EDGE || raw >= P3_REVEAL_START_RAW) {
      p2EndReady = false;
    } else if (raw >= P2_END_RAW - P2_END_EPSILON) {
      p2EndReady = true;
    }

    const p2Raw = clamp(raw / P2_END_RAW, 0, 1);
    const progress = easeInOut(p2Raw);
    const p2Progress = progress;
    const p3Reveal = clamp((raw - P3_REVEAL_START_RAW) / (P3_FULL_RAW - P3_REVEAL_START_RAW), 0, 1);
    const p3Ease = easeInOut(p3Reveal);
    const longTakeFade = p3Ease;
    const p2PersonFade = p3Ease;
    const startX = vw * 0.32;
    const endX = vw * 0.64;
    const startY = vh * 0.78;
    const endY = vh * 0.38;
    const startScale = vw < 720 ? 0.74 : 0.82;
    const endScale = vw < 720 ? 0.34 : 0.3;

    person.style.setProperty("--walk-progress", progress.toFixed(4));
    scene.style.setProperty("--walk-progress", progress.toFixed(4));
    scene.style.setProperty("--p2-progress", p2Progress.toFixed(4));
    scene.style.setProperty("--long-take-fade", longTakeFade.toFixed(4));
    scene.style.setProperty("--p2-person-fade", p2PersonFade.toFixed(4));
    scene.style.setProperty("--p3-reveal", p3Ease.toFixed(4));
    scene.style.setProperty("--walk-bg-scale", (1.03 - p2Progress * 0.018).toFixed(4));
    scene.style.setProperty("--walk-bg-x", `${(-p2Progress * vw * 0.018).toFixed(2)}px`);
    scene.style.setProperty("--walk-bg-y", `${(p2Progress * vh * 0.018).toFixed(2)}px`);
    scene.style.setProperty("--walk-x", `${lerp(startX, endX, p2Progress).toFixed(2)}px`);
    scene.style.setProperty("--walk-y", `${lerp(startY, endY, p2Progress).toFixed(2)}px`);
    scene.style.setProperty("--walk-scale", lerp(startScale, endScale, p2Progress).toFixed(4));
    scene.style.setProperty("--walk-opacity", ((1 - p2Progress * 0.08) * (1 - p2PersonFade)).toFixed(4));
    scene.style.setProperty("--walk-blur", `${(p2Progress * 0.22 + p2PersonFade * 0.18).toFixed(3)}px`);

    const noteStops = [0.24, 0.5, 0.74];
    const noteReveals = [];
    notes.forEach((note, index) => {
      const revealIn = clamp((p2Progress - noteStops[index]) / 0.12, 0, 1);
      const revealOut = 1 - p3Ease;
      const reveal = revealIn * revealOut;
      noteReveals[index] = reveal;
      note.style.setProperty("--note-reveal", reveal.toFixed(4));
    });
    scene.style.setProperty("--campfire-reveal", (noteReveals[0] || 0).toFixed(4));
    scene.style.setProperty("--tent-reveal", (noteReveals[1] || 0).toFixed(4));
  }

  function getSceneMetrics() {
    const top = scene.offsetTop;
    const travel = Math.max(1, scene.offsetHeight - window.innerHeight);
    const raw = clamp((window.scrollY - top) / travel, 0, 1);
    return { top, travel, raw };
  }

  function smoothSnapToRaw(targetRaw, onDone) {
    if (isWalkSnapping) return;

    cancelAnimationFrame(snapFrame);
    isWalkSnapping = true;
    document.body.classList.add("is-scene-snapping");

    const { top, travel } = getSceneMetrics();
    const start = window.scrollY;
    const end = top + targetRaw * travel;
    const distance = end - start;
    snapExpectedY = start;
    const duration = clamp(Math.abs(distance) * 0.9, 560, 960);
    const startedAt = performance.now();

    const step = (now) => {
      const t = clamp((now - startedAt) / duration, 0, 1);
      const eased = easeInOut(t);
      snapExpectedY = start + distance * eased;
      window.scrollTo(0, snapExpectedY);
      updateWalk();

      if (t >= 1) {
        snapExpectedY = end;
        window.scrollTo(0, end);
        updateWalk();
        isWalkSnapping = false;
        document.body.classList.remove("is-scene-snapping");
        snapFrame = 0;
        onDone?.();
        return;
      }

      snapFrame = requestAnimationFrame(step);
    };

    snapFrame = requestAnimationFrame(step);
  }

  function handleWheel(event) {
    if (isWalkSnapping) {
      event.preventDefault();
      return;
    }

    const { top, travel, raw } = getSceneMetrics();
    const sceneDistance = window.scrollY - top;
    const inScene = sceneDistance >= -2 && sceneDistance <= travel + 2;
    if (!inScene) return;

    const projectedRaw = clamp((sceneDistance + event.deltaY) / travel, 0, 1);

    if (event.deltaY > 0) {
      if (raw < P2_END_RAW - P2_END_EPSILON || (!p2EndReady && raw < P3_REVEAL_START_RAW)) {
        if (projectedRaw < P2_END_RAW - SNAP_EDGE) {
          return;
        }

        event.preventDefault();
        smoothSnapToRaw(P2_END_RAW, () => {
          p2EndReady = true;
        });
        return;
      }

      if (raw >= P2_END_RAW - P2_END_EPSILON && raw < P3_FULL_RAW - SNAP_EDGE) {
        event.preventDefault();
        p2EndReady = false;
        smoothSnapToRaw(P3_FULL_RAW);
      }
      return;
    }

    if (event.deltaY < 0 && raw > P2_END_RAW + SNAP_EDGE) {
      event.preventDefault();
      smoothSnapToRaw(P2_END_RAW, () => {
        p2EndReady = true;
      });
    }
  }

  function tick() {
    updateWalk();
    requestAnimationFrame(tick);
  }

  updateWalk();
  window.addEventListener("wheel", handleWheel, { passive: false, capture: true });
  window.addEventListener(
    "scroll",
    () => {
      if (isWalkSnapping && Math.abs(window.scrollY - snapExpectedY) > 10) {
        window.scrollTo(0, snapExpectedY);
      }
      updateWalk();
    },
    { passive: true },
  );
  window.addEventListener("resize", updateWalk);
  window.addEventListener("pagehide", () => {
    cancelAnimationFrame(snapFrame);
    isWalkSnapping = false;
    p2EndReady = false;
    document.body.classList.remove("is-scene-snapping");
  });
  requestAnimationFrame(tick);
})();
