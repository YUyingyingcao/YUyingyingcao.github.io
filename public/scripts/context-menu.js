(() => {
  const menu = document.createElement("div");
  menu.className = "custom-context-menu";
  menu.setAttribute("aria-hidden", "true");
  menu.innerHTML = `
    <button type="button" data-action="refresh"><span>↻</span>刷新页面</button>
    <button type="button" data-action="copy-selection"><span>⧉</span>复制选中</button>
    <button type="button" data-action="copy-link"><span>🔗</span>复制链接</button>
    <button type="button" data-action="top"><span>↑</span>回到顶部</button>
  `;
  document.body.append(menu);

  const isEditable = (target) => {
    if (!(target instanceof Element)) return false;
    return Boolean(target.closest("input, textarea, select, [contenteditable='true']"));
  };

  function closeMenu() {
    menu.classList.remove("is-open");
    menu.setAttribute("aria-hidden", "true");
  }

  function openMenu(event) {
    if (isEditable(event.target)) return;
    event.preventDefault();

    const menuWidth = 196;
    const menuHeight = 184;
    const x = Math.min(event.clientX, window.innerWidth - menuWidth - 12);
    const y = Math.min(event.clientY, window.innerHeight - menuHeight - 12);

    menu.style.setProperty("--menu-x", `${Math.max(12, x)}px`);
    menu.style.setProperty("--menu-y", `${Math.max(12, y)}px`);
    menu.classList.add("is-open");
    menu.setAttribute("aria-hidden", "false");
  }

  async function copyText(text) {
    if (!text) return false;
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      const textarea = document.createElement("textarea");
      textarea.value = text;
      textarea.setAttribute("readonly", "");
      textarea.style.position = "fixed";
      textarea.style.opacity = "0";
      document.body.append(textarea);
      textarea.select();
      const ok = document.execCommand("copy");
      textarea.remove();
      return ok;
    }
  }

  function flash(button, label) {
    const original = button.innerHTML;
    button.innerHTML = `<span>✓</span>${label}`;
    window.setTimeout(() => {
      button.innerHTML = original;
      closeMenu();
    }, 520);
  }

  document.addEventListener("contextmenu", openMenu);
  document.addEventListener("click", (event) => {
    if (!menu.contains(event.target)) closeMenu();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeMenu();
  });
  window.addEventListener("scroll", closeMenu, { passive: true });

  menu.addEventListener("click", async (event) => {
    const button = event.target.closest("button[data-action]");
    if (!button) return;

    const action = button.dataset.action;
    if (action === "refresh") {
      window.location.reload();
      return;
    }

    if (action === "copy-selection") {
      const selected = window.getSelection().toString().trim();
      const ok = await copyText(selected || document.title);
      flash(button, ok ? "已复制" : "复制失败");
      return;
    }

    if (action === "copy-link") {
      const ok = await copyText(window.location.href);
      flash(button, ok ? "链接已复制" : "复制失败");
      return;
    }

    if (action === "top") {
      window.scrollTo({ top: 0, behavior: "smooth" });
      closeMenu();
    }
  });
})();
