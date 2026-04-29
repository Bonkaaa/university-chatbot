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

// function getEmailFromSomewhere() {
//   // 1) Thử lấy từ global chainlit.user (cách Chainlit lưu user info)
//   try {
//     if (window?.chainlit?.user) {
//       const user = window.chainlit.user;
//       // Kiểm tra metadata.email (nơi backend lưu thông tin)
//       if (user.metadata?.email) return user.metadata.email;
//       if (user.email) return user.email;
//       if (user.identifier) {
//         // identifier có thể là user ID, thử parse
//         console.log("Found user.identifier:", user.identifier);
//       }
//     }
//   } catch (e) {
//     console.log("Error accessing chainlit.user:", e);
//   }

//   // 2) Thử lấy từ localStorage (Chainlit có thể lưu user info ở đây)
//   try {
//     const lsKeys = Object.keys(localStorage);
//     for (const k of lsKeys) {
//       const v = localStorage.getItem(k);
//       if (!v || v.length > 5000) continue; // Bỏ qua các value quá dài
      
//       // Tìm email trực tiếp
//       if (v.includes("@") && v.includes(".") && v.length < 200) {
//         const match = v.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/);
//         if (match) {
//           console.log("Found email in localStorage[" + k + "]:", match[0]);
//           return match[0];
//         }
//       }
      
//       // Thử parse JSON
//       try {
//         const obj = JSON.parse(v);
//         if (obj?.email) return obj.email;
//         if (obj?.user?.email) return obj.user.email;
//         if (obj?.user?.metadata?.email) return obj.user.metadata.email;
//         if (obj?.metadata?.email) return obj.metadata.email;
//       } catch {}
//     }
//   } catch (e) {
//     console.log("Error accessing localStorage:", e);
//   }

//   // 3) Thử từ cookies (username có thể được lưu ở đây)
//   try {
//     const cookies = document.cookie.split(";");
//     for (const cookie of cookies) {
//       const [name, value] = cookie.trim().split("=");
//       if ((name.toLowerCase().includes("email") || name.toLowerCase().includes("user")) && value) {
//         const decoded = decodeURIComponent(value);
//         if (decoded.includes("@")) {
//           const match = decoded.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/);
//           if (match) return match[0];
//         }
//       }
//     }
//   } catch (e) {
//     console.log("Error accessing cookies:", e);
//   }

//   console.log("Could not find email - localStorage keys:", Object.keys(localStorage));
//   console.log("window.chainlit:", window.chainlit);
//   return null;
// }

// function toValidUserId(value) {
//   if (value === null || value === undefined) return null;
//   const raw = String(value).trim().toLowerCase();
//   if (!raw || raw === "null" || raw === "undefined" || raw === "nan") return null;
//   const num = Number(raw);
//   if (!Number.isInteger(num) || num <= 0) return null;
//   return num;
// }

// function getUserIdFromSomewhere() {
//   // 1) Ưu tiên chainlit.user.metadata.user_id hoặc identifier
//   try {
//     const user = window?.chainlit?.user;
//     if (user) {
//       const fromMetadata = user?.metadata?.user_id;
//       const idFromMetadata = toValidUserId(fromMetadata);
//       if (idFromMetadata !== null) return idFromMetadata;
//       const idFromIdentifier = toValidUserId(user.identifier);
//       if (idFromIdentifier !== null) return idFromIdentifier;
//     }
//   } catch (e) {
//     console.log("Error accessing user_id from chainlit.user:", e);
//   }

//   // 2) Fallback: thử parse JSON trong localStorage
//   try {
//     const lsKeys = Object.keys(localStorage);
//     for (const k of lsKeys) {
//       const v = localStorage.getItem(k);
//       if (!v || v.length > 5000) continue;
//       try {
//         const obj = JSON.parse(v);
//         const candidate =
//           obj?.user_id ??
//           obj?.user?.id ??
//           obj?.user?.metadata?.user_id ??
//           obj?.metadata?.user_id ??
//           obj?.identifier;
//         const parsed = toValidUserId(candidate);
//         if (parsed !== null) return parsed;
//       } catch {}
//     }
//   } catch (e) {
//     console.log("Error accessing localStorage for user_id:", e);
//   }

//   return null;
// }

// function buildUserScopedUrl(path) {
//   const userId = getUserIdFromSomewhere();
//   if (userId !== null) {
//     return `${path}?user_id=${encodeURIComponent(String(userId))}`;
//   }

//   const email = getEmailFromSomewhere();
//   if (email) {
//     return `${path}?email=${encodeURIComponent(email)}`;
//   }

//   return path;
// }

// function goProfile() {
//   window.location.href = buildUserScopedUrl("/profile");
// }

// function goChangePassword() {
//   window.location.href = buildUserScopedUrl("/change-password");
// }

// // Ví dụ: gắn vào button của bạn (tùy bạn tạo button bằng cách nào)
// document.addEventListener("click", (e) => {
//   const t = e.target;
//   if (t?.id === "btnProfile") {
//     e.preventDefault();
//     goProfile();
//   }
//   if (t?.id === "btnChangePassword") {
//     e.preventDefault();
//     goChangePassword();
//   }
// });

// // Intercept header links để thêm email query param
// document.addEventListener("click", (e) => {
//   const link = e.target.closest("a");
//   if (!link) return;

//   const href = link.getAttribute("href");
//   if (!href) return;

//   const parsed = new URL(href, window.location.origin);
//   // Kiểm tra nếu là link /profile hoặc /change-password từ header
//   if (parsed.pathname === "/profile" || parsed.pathname === "/change-password") {
//     e.preventDefault();

//     const newUrl = buildUserScopedUrl(parsed.pathname);
//     console.log("Redirecting to:", newUrl);
//     window.location.href = newUrl;
//   }
// });
