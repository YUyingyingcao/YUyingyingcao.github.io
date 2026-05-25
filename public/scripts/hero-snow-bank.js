(() => {
  const bank = document.querySelector("[data-hero-snow-bank]");
  const canvas = document.querySelector("[data-hero-snow-canvas]");
  if (!bank || !canvas) return;

  const context = canvas.getContext("2d", { alpha: true });
  const stages = [
    { height: 42, crest: 7, alpha: 0.96 },
    { height: 70, crest: 12, alpha: 0.98 },
    { height: 100, crest: 17, alpha: 0.99 },
    { height: 134, crest: 23, alpha: 1 },
  ];

  const state = {
    currentStage: 0,
    targetStage: 0,
    displayedStage: 0,
    smoothTimer: 0,
    lastGrowth: performance.now(),
    width: 0,
    height: 0,
    dpr: 1,
    drift: 0,
    passes: 0,
    lastPointer: null,
    pointerInside: false,
  };
  const topPadding = 62;

  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const growDelay = prefersReducedMotion ? 12000 : 7600;
  const passesToRetreat = 4;
  const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
  const lerp = (from, to, amount) => from + (to - from) * amount;
  const randomUnit = (seed) => {
    const value = Math.sin(seed * 12.9898 + 78.233) * 43758.5453;
    return value - Math.floor(value);
  };

  function resize() {
    const rect = bank.getBoundingClientRect();
    state.dpr = Math.min(2, window.devicePixelRatio || 1);
    state.width = Math.max(1, Math.round(rect.width));
    state.height = Math.max(1, Math.round(rect.height));
    canvas.width = Math.round(state.width * state.dpr);
    canvas.height = Math.round(state.height * state.dpr);
    canvas.style.width = `${state.width}px`;
    canvas.style.height = `${state.height}px`;
    context.setTransform(state.dpr, 0, 0, state.dpr, 0, 0);
    draw();
  }

  function stageAt(value) {
    const lower = Math.floor(value);
    const upper = Math.min(stages.length - 1, lower + 1);
    const mix = value - lower;
    return {
      height: lerp(stages[lower].height, stages[upper].height, mix),
      crest: lerp(stages[lower].crest, stages[upper].crest, mix),
      alpha: lerp(stages[lower].alpha, stages[upper].alpha, mix),
    };
  }

  function buildSurface(stage) {
    const points = [];
    const step = Math.max(16, state.width / 78);

    for (let x = -step; x <= state.width + step; x += step) {
      const driftedX = x + state.drift * 0.16;
      const lump =
        Math.pow(Math.max(0, Math.sin(driftedX * 0.008 + 0.8)), 2.2) * stage.crest * 1.1 +
        Math.pow(Math.max(0, Math.sin(driftedX * 0.015 - 1.4)), 2.6) * stage.crest * 0.48;
      const powder =
        (randomUnit(Math.round(x / step)) - 0.5) *
        stage.crest *
        0.18;
      const wave =
        Math.sin(driftedX * 0.012) * stage.crest * 0.13 +
        Math.sin(driftedX * 0.032) * stage.crest * 0.06;
      const surfaceY = state.height - stage.height - lump - wave - powder;
      points.push({
        x,
        y: Math.max(topPadding, surfaceY),
      });
    }

    return points;
  }

  function traceSurface(surface, offset = 0) {
    if (!surface.length) return;

    context.moveTo(surface[0].x, surface[0].y + offset);
    for (let i = 1; i < surface.length - 1; i += 1) {
      const current = surface[i];
      const next = surface[i + 1];
      const midX = (current.x + next.x) / 2;
      const midY = (current.y + next.y) / 2 + offset;
      context.quadraticCurveTo(current.x, current.y + offset, midX, midY);
    }

    const last = surface[surface.length - 1];
    context.lineTo(last.x, last.y + offset);
  }

  function drawSparkles(surfaceTop, stage) {
    context.save();
    context.globalAlpha = 0.62;
    context.fillStyle = "rgba(255, 255, 255, 0.96)";

    for (let i = 0; i < 54; i += 1) {
      const x = ((i * 97 + state.drift * 0.7) % (state.width + 80)) - 40;
      const y =
        surfaceTop +
        8 +
        ((i * 31) % Math.max(28, stage.height * 0.78)) +
        Math.sin(i + state.drift * 0.012) * 3;
      const radius = i % 5 === 0 ? 1.7 : 1.05;
      context.beginPath();
      context.arc(x, y, radius, 0, Math.PI * 2);
      context.fill();
    }

    context.restore();
  }

  function drawPowderRim(surface, stage) {
    context.save();
    context.lineCap = "round";
    context.lineJoin = "round";
    context.shadowColor = "rgba(255, 255, 255, 0.42)";
    context.shadowBlur = 12;

    context.strokeStyle = `rgba(255, 255, 255, ${0.7 * stage.alpha})`;
    context.lineWidth = 12;
    context.beginPath();
    traceSurface(surface, -1.5);
    context.stroke();

    context.shadowBlur = 0;
    context.strokeStyle = `rgba(188, 221, 240, ${0.18 * stage.alpha})`;
    context.lineWidth = 2;
    context.beginPath();
    traceSurface(surface, 9);
    context.stroke();

    context.strokeStyle = `rgba(255, 255, 255, ${0.66 * stage.alpha})`;
    context.lineWidth = 3.5;
    for (let i = 2; i < surface.length - 4; i += 5) {
      const point = surface[i];
      const seed = i * 19;
      if (randomUnit(seed) < 0.44) continue;

      const width = 18 + randomUnit(seed + 3) * 26;
      const rise = 2 + randomUnit(seed + 7) * 4;
      context.beginPath();
      context.moveTo(point.x - width * 0.5, point.y + 2);
      context.quadraticCurveTo(point.x, point.y - rise, point.x + width * 0.5, point.y + 2);
      context.stroke();
    }

    context.fillStyle = `rgba(255, 255, 255, ${0.72 * stage.alpha})`;
    for (let i = 0; i < 42; i += 1) {
      const seed = i * 41;
      const point = surface[Math.floor(randomUnit(seed) * surface.length)];
      if (!point) continue;
      const x = point.x + (randomUnit(seed + 5) - 0.5) * 22;
      const y = point.y + randomUnit(seed + 9) * 13 - 4;
      const radius = 0.8 + randomUnit(seed + 13) * 1.15;
      context.beginPath();
      context.arc(x, y, radius, 0, Math.PI * 2);
      context.fill();
    }

    context.restore();
  }

  function drawRidges(surface) {
    context.save();
    context.strokeStyle = "rgba(210, 231, 246, 0.2)";
    context.lineWidth = 1;

    for (let row = 0; row < 4; row += 1) {
      context.globalAlpha = 0.18 - row * 0.03;
      context.beginPath();
      const ridge = surface.map((point, index) => ({
        x: point.x,
        y: point.y + 18 + row * 19 + Math.sin(index * 1.7 + row) * 1.4,
      }));
      traceSurface(ridge);
      context.stroke();
    }

    context.restore();
  }

  function draw() {
    const stage = stageAt(state.displayedStage);
    const surface = buildSurface(stage);
    const surfaceTop = Math.min(...surface.map((point) => point.y));

    context.clearRect(0, 0, state.width, state.height);

    const glow = context.createLinearGradient(0, surfaceTop - 26, 0, state.height);
    glow.addColorStop(0, "rgba(255, 255, 255, 0)");
    glow.addColorStop(0.44, `rgba(255, 255, 255, ${0.28 * stage.alpha})`);
    glow.addColorStop(1, `rgba(250, 253, 255, ${0.42 * stage.alpha})`);
    context.fillStyle = glow;
    context.fillRect(0, Math.max(0, surfaceTop - 40), state.width, state.height - surfaceTop + 40);

    context.beginPath();
    traceSurface(surface);
    context.lineTo(state.width + 40, state.height + 8);
    context.lineTo(-40, state.height + 8);
    context.closePath();

    const fill = context.createLinearGradient(0, surfaceTop, 0, state.height);
    fill.addColorStop(0, `rgba(255, 255, 255, ${stage.alpha})`);
    fill.addColorStop(0.18, `rgba(253, 254, 255, ${0.995 * stage.alpha})`);
    fill.addColorStop(0.58, `rgba(249, 253, 255, ${0.985 * stage.alpha})`);
    fill.addColorStop(1, `rgba(238, 248, 253, ${0.965 * stage.alpha})`);
    context.fillStyle = fill;
    context.fill();

    context.save();
    context.clip();
    drawRidges(surface);
    drawSparkles(surfaceTop, stage);
    context.restore();

    context.strokeStyle = "rgba(255, 255, 255, 0.42)";
    context.lineWidth = 7;
    context.lineCap = "round";
    context.lineJoin = "round";
    context.shadowColor = "rgba(255, 255, 255, 0.46)";
    context.shadowBlur = 14;
    context.beginPath();
    traceSurface(surface);
    context.stroke();
    drawPowderRim(surface, stage);

    if (state.pointerInside && state.lastPointer) {
      context.save();
      context.globalAlpha = 0.22;
      context.strokeStyle = "rgba(156, 199, 229, 0.62)";
      context.lineWidth = 7;
      context.lineCap = "round";
      context.beginPath();
      context.moveTo(state.lastPointer.x - 32, state.lastPointer.y + 4);
      context.quadraticCurveTo(state.lastPointer.x, state.lastPointer.y - 10, state.lastPointer.x + 34, state.lastPointer.y + 4);
      context.stroke();
      context.restore();
    }
  }

  function retreatStage() {
    if (state.targetStage <= 0) return;
    const previousStage = state.targetStage;
    state.targetStage -= 1;
    state.currentStage = state.targetStage;
    state.lastGrowth = performance.now();
    window.dispatchEvent(
      new CustomEvent("hero-snow-stage-retreat", {
        detail: {
          previousStage,
          currentStage: state.targetStage,
        },
      }),
    );
  }

  function handlePointerMove(event) {
    const rect = bank.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const snow = stageAt(state.displayedStage);
    const activeTop = Math.max(topPadding - 14, state.height - snow.height - snow.crest - 28);
    const isInside = x >= 0 && x <= state.width && y >= activeTop && y <= state.height;

    state.pointerInside = isInside;
    bank.classList.toggle("is-shoveling", isInside);

    if (!isInside) {
      state.lastPointer = null;
      return;
    }

    if (state.lastPointer) {
      const distance = Math.hypot(x - state.lastPointer.x, y - state.lastPointer.y);
      if (distance > 14) {
        state.passes += distance / 54;
      }
    }

    state.lastPointer = { x, y };

    if (state.passes >= passesToRetreat) {
      state.passes = 0;
      retreatStage();
    }
  }

  function handlePointerLeave() {
    state.pointerInside = false;
    state.lastPointer = null;
    bank.classList.remove("is-shoveling");
  }

  function tick(now) {
    if (now - state.lastGrowth > growDelay && state.targetStage < stages.length - 1) {
      state.targetStage += 1;
      state.currentStage = state.targetStage;
      state.lastGrowth = now;
    }

    state.displayedStage = lerp(state.displayedStage, state.targetStage, 0.035);
    if (Math.abs(state.displayedStage - state.targetStage) < 0.01) {
      state.displayedStage = state.targetStage;
    }

    if (!prefersReducedMotion) {
      state.drift += 0.22;
    }

    draw();
    requestAnimationFrame(tick);
  }

  resize();
  requestAnimationFrame(tick);
  window.addEventListener("resize", resize);
  bank.addEventListener("pointermove", handlePointerMove);
  bank.addEventListener("pointerleave", handlePointerLeave);
})();
