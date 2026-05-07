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

(function redirectAdminAfterLogin() {
  const redirectedFlag = "admin_redirected_after_login";

  function tryRedirect() {
    try{
      const user = window?.chainlit?.user;
      const role = user?.metadata?.role;

      if (role === "admin" && !sessionStorage.getItem(redirectedFlag)) {
        sessionStorage.setItem(redirectedFlag, "true");
        window.location.href = "/admin";
      }
    }
    catch (e) {
      console.error("Error during admin redirect:", e);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", tryRedirect);
  } else {
    tryRedirect();
  }
})();

function getCookie(name) {
  const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
  return match ? decodeURIComponent(match[2]) : null;
}

function parseJwt(token) {
  try {
    const payload = token.split(".")[1];
    return JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/")));
  } catch {
    return null;
  }
}

async function getRoleFromApi() {
  try {
    const res = await fetch("/api/me", {
      method: "GET",
      credentials: "include",
      cache: "no-store",
    });

    console.log("api/me status:", res.status);

    if (!res.ok) return null;
    const data = await res.json();
    console.log("api/me data:", data);
    return data?.role ? String(data.role).trim().toLowerCase() : null;
  } catch (e) {
    console.error("api/me error", e);
    return null;
  }
}

async function syncAdminLinkVisibility() {
  const adminLink = document.querySelector('a[href="/admin"]');
  if (!adminLink) return;

  const role = await getRoleFromApi();

  // Unknown role, keep the link hidden (or removed) until we can confirm it's admin. This prevents flashing the admin link for non-admin users on page load.
  if (!role) return;

  if (role === "admin") {
    // Assure the link is visible for admins. In case it was hidden by default or by previous checks.
    adminLink.style.display = "";
    if (adminLink.parentElement) adminLink.parentElement.style.display = "";
  } else {
    // Not admin, remove the link from DOM to prevent any access.
    const container = adminLink.closest("li") || adminLink.parentElement || adminLink;
    container.remove();
  }
}

(function watchAdminLink() {
  syncAdminLinkVisibility();
  window.addEventListener("load", syncAdminLinkVisibility);
  document.addEventListener("DOMContentLoaded", syncAdminLinkVisibility);

  const observer = new MutationObserver(syncAdminLinkVisibility);
  observer.observe(document.documentElement, { childList: true, subtree: true });
})();