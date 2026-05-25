(() => {
  if (document.querySelector("[data-capsule-nav]")) return;

  const links = [
    { href: "/", icon: "❄️", label: "初雪", hint: "回到头图" },
    { href: "/blog", icon: "📖", label: "手札", hint: "博客日记" },
    { href: "/projects", icon: "🧸", label: "工房", hint: "灵感收纳" },
    { href: "/about", icon: "☃️", label: "关于", hint: "这个人" },
  ];

  const nav = document.createElement("nav");
  nav.className = "capsule-nav";
  nav.dataset.capsuleNav = "";
  nav.setAttribute("aria-label", "Yunity navigation");
  nav.innerHTML = `
    <button class="capsule-nav__toggle" type="button" aria-expanded="false" aria-controls="capsule-nav-panel">
      <span class="capsule-nav__flake" aria-hidden="true">
        <img src="/assets/ui/scrollbar-snowman-snowmanjpg-final.webp" alt="" />
      </span>
      <span class="capsule-nav__brand">雪境入口</span>
      <span class="capsule-nav__chevron" aria-hidden="true"></span>
    </button>
    <div class="capsule-nav__panel" id="capsule-nav-panel">
      ${links
        .map(
          (link) => `
            <a class="capsule-nav__link" href="${link.href}" data-nav-href="${link.href}">
              <span class="capsule-nav__icon" aria-hidden="true">${link.icon}</span>
              <span class="capsule-nav__text">
                <span>${link.label}</span>
                <small>${link.hint}</small>
              </span>
            </a>
          `,
        )
        .join("")}
    </div>
  `;

  document.body.prepend(nav);

  const toggle = nav.querySelector(".capsule-nav__toggle");
  const path = window.location.pathname.replace(/\/$/, "") || "/";
  nav.querySelectorAll("[data-nav-href]").forEach((link) => {
    const href = link.getAttribute("data-nav-href");
    const normalizedHref = href === "/" ? "/" : href.replace(/\/$/, "");
    if (path === normalizedHref) link.classList.add("is-active");
  });

  function setOpen(open) {
    nav.classList.toggle("is-open", open);
    toggle.setAttribute("aria-expanded", String(open));
  }

  function syncScrollState() {
    nav.classList.toggle("is-scrolled", window.scrollY > 24);
  }

  toggle.addEventListener("click", () => {
    setOpen(!nav.classList.contains("is-open"));
  });

  document.addEventListener("click", (event) => {
    if (!nav.contains(event.target)) setOpen(false);
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") setOpen(false);
  });

  nav.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => setOpen(false));
  });

  syncScrollState();
  window.addEventListener("scroll", syncScrollState, { passive: true });
})();
