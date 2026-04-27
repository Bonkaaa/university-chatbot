(function addRegisterAction() {
  const registerHref = "/register";

  function injectLink() {
    if (document.querySelector("[data-auth-register-link='true']")) {
      return;
    }

    const passwordInput = document.querySelector("input[type='password']");
    if (!passwordInput) {
      return;
    }

    const form = passwordInput.closest("form");
    if (!form) {
      return;
    }

    const wrapper = document.createElement("div");
    wrapper.className = "auth-register-container";

    const text = document.createElement("span");
    text.textContent = "Chưa có tài khoản ?";

    const link = document.createElement("a");
    link.href = registerHref;
    link.textContent = "Tạo tài khoản ngay";
    link.setAttribute("data-auth-register-link", "true");
    link.className = "auth-register-link";

    wrapper.appendChild(text);
    wrapper.appendChild(link);
    form.appendChild(wrapper);
  }

  const observer = new MutationObserver(injectLink);
  observer.observe(document.documentElement, { childList: true, subtree: true });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", injectLink);
  } else {
    injectLink();
  }
})();
