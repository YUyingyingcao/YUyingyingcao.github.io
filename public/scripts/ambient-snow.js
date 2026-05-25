(() => {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  if (document.querySelector("[data-ambient-snow]")) return;

  const canvas = document.createElement("canvas");
  canvas.className = "ambient-snow";
  canvas.dataset.ambientSnow = "true";
  canvas.setAttribute("aria-hidden", "true");
  document.body.append(canvas);

  const context = canvas.getContext("2d", { alpha: true });
  const flakes = [];
  const density = 0.000085;
  let width = 0;
  let height = 0;
  let dpr = 1;
  let lastTime = performance.now();

  const random = (min, max) => min + Math.random() * (max - min);

  function makeFlake(initial = false) {
    const large = Math.random() > 0.82;
    const radius = large ? random(2.1, 3.8) : random(0.7, 2.2);
    return {
      x: random(-width * 0.08, width * 1.08),
      y: initial ? random(-height, height) : random(-height * 0.16, -12),
      radius,
      alpha: large ? random(0.66, 0.94) : random(0.38, 0.78),
      speed: large ? random(18, 36) : random(10, 26),
      drift: random(-10, 16),
      phase: random(0, Math.PI * 2),
      spin: random(0.35, 0.9),
    };
  }

  function resize() {
    width = window.innerWidth;
    height = window.innerHeight;
    dpr = Math.min(2, window.devicePixelRatio || 1);
    canvas.width = Math.max(1, Math.round(width * dpr));
    canvas.height = Math.max(1, Math.round(height * dpr));
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    context.setTransform(dpr, 0, 0, dpr, 0, 0);

    const targetCount = Math.round(Math.min(150, Math.max(58, width * height * density)));
    while (flakes.length < targetCount) flakes.push(makeFlake(true));
    while (flakes.length > targetCount) flakes.pop();
  }

  function drawFlake(flake, time) {
    const shimmer = 0.82 + Math.sin(time * flake.spin + flake.phase) * 0.18;
    const alpha = flake.alpha * shimmer;
    const glow = context.createRadialGradient(
      flake.x,
      flake.y,
      0,
      flake.x,
      flake.y,
      flake.radius * 2.2,
    );

    glow.addColorStop(0, `rgba(255, 255, 255, ${alpha})`);
    glow.addColorStop(0.48, `rgba(255, 255, 255, ${alpha * 0.82})`);
    glow.addColorStop(1, "rgba(255, 255, 255, 0)");
    context.fillStyle = glow;
    context.beginPath();
    context.arc(flake.x, flake.y, flake.radius * 2.2, 0, Math.PI * 2);
    context.fill();
  }

  function tick(now) {
    const delta = Math.min(0.05, (now - lastTime) / 1000);
    lastTime = now;
    const time = now / 1000;

    context.clearRect(0, 0, width, height);

    for (const flake of flakes) {
      flake.phase += delta * flake.spin;
      flake.y += flake.speed * delta;
      flake.x += (flake.drift + Math.sin(time * 0.55 + flake.phase) * 10) * delta;

      if (flake.y - flake.radius > height + 10 || flake.x < -width * 0.12 || flake.x > width * 1.12) {
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
