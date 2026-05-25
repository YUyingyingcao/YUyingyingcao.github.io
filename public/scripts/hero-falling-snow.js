(() => {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  const stage = document.querySelector("[data-avatar-stage]");
  const canvas = document.querySelector("[data-hero-falling-snow]");
  if (!stage || !canvas) return;

  const context = canvas.getContext("2d", { alpha: true });
  const flakes = [];
  const gusts = [];
  const density = 0.00016;
  let width = 0;
  let height = 0;
  let dpr = 1;
  let lastTime = performance.now();

  const random = (min, max) => min + Math.random() * (max - min);
  const clamp = (value, min, max) => Math.min(max, Math.max(min, value));

  function makeFlake(initial = false) {
    const layer = Math.random();
    const near = layer > 0.78;
    const tiny = layer < 0.42;
    const radius = near ? random(2.4, 5.6) : tiny ? random(0.65, 1.45) : random(1.2, 2.7);
    return {
      x: random(-width * 0.12, width * 1.12),
      y: initial ? random(-height * 0.2, height * 1.04) : random(-height * 0.18, -20),
      radius,
      alpha: near ? random(0.62, 0.94) : tiny ? random(0.28, 0.58) : random(0.42, 0.78),
      speed: near ? random(42, 86) : tiny ? random(16, 34) : random(26, 58),
      drift: near ? random(-34, 18) : random(-18, 14),
      phase: random(0, Math.PI * 2),
      spin: random(0.45, 1.25),
      wobble: near ? random(16, 34) : random(7, 19),
      blur: near ? random(0.2, 0.8) : 0,
    };
  }

  function resize() {
    const rect = stage.getBoundingClientRect();
    width = Math.max(1, Math.round(rect.width));
    height = Math.max(1, Math.round(rect.height));
    dpr = Math.min(2, window.devicePixelRatio || 1);
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    context.setTransform(dpr, 0, 0, dpr, 0, 0);

    const targetCount = Math.round(clamp(width * height * density, 120, 290));
    while (flakes.length < targetCount) flakes.push(makeFlake(true));
    while (flakes.length > targetCount) flakes.pop();
  }

  function drawFlake(flake, time) {
    const shimmer = 0.84 + Math.sin(time * flake.spin + flake.phase) * 0.16;
    const alpha = flake.alpha * shimmer;

    context.save();
    if (flake.blur) {
      context.filter = `blur(${flake.blur}px)`;
    }

    const glow = context.createRadialGradient(
      flake.x,
      flake.y,
      0,
      flake.x,
      flake.y,
      flake.radius * 2.35,
    );
    glow.addColorStop(0, `rgba(255, 255, 255, ${alpha})`);
    glow.addColorStop(0.5, `rgba(246, 252, 255, ${alpha * 0.78})`);
    glow.addColorStop(1, "rgba(255, 255, 255, 0)");
    context.fillStyle = glow;
    context.beginPath();
    context.arc(flake.x, flake.y, flake.radius * 2.35, 0, Math.PI * 2);
    context.fill();
    context.restore();
  }

  function drawGust(gust) {
    context.save();
    context.globalAlpha = gust.alpha;
    context.strokeStyle = "rgba(244, 252, 255, 0.72)";
    context.lineWidth = gust.width;
    context.lineCap = "round";
    context.beginPath();
    context.moveTo(gust.x, gust.y);
    context.quadraticCurveTo(gust.x + gust.length * 0.42, gust.y - gust.lift, gust.x + gust.length, gust.y);
    context.stroke();
    context.restore();
  }

  function tick(now) {
    const delta = Math.min(0.04, (now - lastTime) / 1000);
    lastTime = now;
    const time = now / 1000;
    const stageRect = stage.getBoundingClientRect();
    const visible = stageRect.bottom > 0 && stageRect.top < window.innerHeight;

    context.clearRect(0, 0, width, height);
    if (!visible) {
      requestAnimationFrame(tick);
      return;
    }

    if (Math.random() < 0.018 && gusts.length < 5) {
      gusts.push({
        x: random(-width * 0.15, width * 0.72),
        y: random(height * 0.1, height * 0.82),
        length: random(width * 0.16, width * 0.36),
        lift: random(8, 24),
        speed: random(18, 42),
        alpha: random(0.06, 0.16),
        width: random(1, 2.4),
      });
    }

    for (let i = gusts.length - 1; i >= 0; i -= 1) {
      const gust = gusts[i];
      gust.x += gust.speed * delta;
      gust.alpha *= 0.992;
      drawGust(gust);
      if (gust.x > width + 80 || gust.alpha < 0.025) {
        gusts.splice(i, 1);
      }
    }

    for (const flake of flakes) {
      flake.phase += delta * flake.spin;
      flake.y += flake.speed * delta;
      flake.x += (flake.drift + Math.sin(time * 0.7 + flake.phase) * flake.wobble) * delta;

      if (flake.y - flake.radius > height + 16 || flake.x < -width * 0.18 || flake.x > width * 1.18) {
        Object.assign(flake, makeFlake(false));
      }

      drawFlake(flake, time);
    }

    requestAnimationFrame(tick);
  }

  resize();
  window.addEventListener("resize", resize);
  requestAnimationFrame(tick);
})();
