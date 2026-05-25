(() => {
  const scrollbar = document.createElement("div");
  scrollbar.className = "snowman-scrollbar";
  scrollbar.setAttribute("aria-hidden", "true");
  scrollbar.innerHTML = `
    <div class="snowman-scrollbar__track">
      <div class="snowman-scrollbar__fill"></div>
    </div>
    <div class="snowman-scrollbar__thumb">
      <img src="/assets/ui/scrollbar-snowman-snowmanjpg-final.png" alt="" />
    </div>
  `;

  document.body.append(scrollbar);

  let movingTimer = 0;

  function updateScrollbar() {
    const scrollable = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
    const progress = Math.min(1, Math.max(0, window.scrollY / scrollable));
    const trackHeight = scrollbar.getBoundingClientRect().height - 42;
    const snowmanY = 22 + progress * trackHeight;

    scrollbar.style.setProperty("--scroll-percent", `${progress * 100}%`);
    scrollbar.style.setProperty("--snowman-y", `${snowmanY}px`);
  }

  function markMoving() {
    scrollbar.classList.add("is-moving");
    clearTimeout(movingTimer);
    movingTimer = window.setTimeout(() => {
      scrollbar.classList.remove("is-moving");
    }, 420);
  }

  updateScrollbar();
  window.addEventListener("scroll", () => {
    updateScrollbar();
    markMoving();
  }, { passive: true });
  window.addEventListener("resize", updateScrollbar);
})();
