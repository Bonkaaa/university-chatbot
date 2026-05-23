// (function () {
//   const e = React.createElement;
//   const root = ReactDOM.createRoot(document.getElementById("app"));
//   const page = document.body.dataset.page;

//   function useNotice() {
//     const [msg, setMsg] = React.useState("");
//     return { msg, setMsg };
//   }
//   async function fetchJson(url, options) {
//     const res = await fetch(url, options);
//     let data = {};
//     try { data = await res.json(); } catch (_) {}
//     if (!res.ok) {
//       throw new Error(data.message || "Có lỗi xảy ra.");
//     }
//     return data;
//   }

//   function Wrap(props) {
//     return e("div", { className: "wrap" }, props.children);
//   }

//   function RegisterPage() {
//     const [email, setEmail] = React.useState("");
//     const [displayName, setDisplayName] = React.useState("");
//     const [password, setPassword] = React.useState("");
//     const { msg, setMsg } = useNotice();
//     const onSubmit = async (ev) => {
//       ev.preventDefault();
//       const form = new FormData();
//       form.append("email", email);
//       form.append("display_name", displayName);
//       form.append("password", password);
//       const data = await fetchJson("/register", { method: "POST", body: form });
//       setMsg(data.message || "Xử lý xong.");
//     };
//     return e(Wrap, null, e("div", { className: "card" },
//       e("h2", null, "Đăng ký tài khoản"),
//       msg ? e("div", { className: "msg" }, msg) : null,
//       e("form", { onSubmit },
//         e("div", { className: "row" }, e("input", { value: email, onChange: (v) => setEmail(v.target.value), placeholder: "Email", type: "email", required: true })),
//         e("div", { className: "row" }, e("input", { value: displayName, onChange: (v) => setDisplayName(v.target.value), placeholder: "Tên hiển thị", required: true })),
//         e("div", { className: "row" }, e("input", { value: password, onChange: (v) => setPassword(v.target.value), placeholder: "Mật khẩu", type: "password", required: true })),
//         e("button", { type: "submit" }, "Tạo tài khoản")
//       ),
//       e("p", null, e("a", { href: "/" }, "Quay lại đăng nhập"))
//     ));
//   }

//   function ProfilePage() {
//     const [u, setU] = React.useState(null);
//     const [displayName, setDisplayName] = React.useState("");
//     const { msg, setMsg } = useNotice();
//     React.useEffect(() => {
//       fetchJson("/api/profile")
//         .then((d) => { setU(d); setDisplayName(d.display_name || ""); })
//         .catch((err) => setMsg(err.message));
//     }, []);
//     const save = async (ev) => {
//       ev.preventDefault();
//       try {
//         const data = await fetchJson("/api/profile", { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ display_name: displayName }) });
//         setMsg(data.message || "Đã lưu.");
//       } catch (err) {
//         setMsg(err.message);
//       }
//     };
//     return e(Wrap, null, e("div", { className: "card" },
//       e("h2", null, "Thông tin tài khoản"),
//       msg ? e("div", { className: "msg" }, msg) : null,
//       !u ? e("p", null, "Đang tải...") : e("form", { onSubmit: save },
//         e("p", null, "Email: ", u.email),
//         e("input", { value: displayName, onChange: (v) => setDisplayName(v.target.value), required: true }),
//         e("div", { className: "row" }, e("button", { type: "submit" }, "Lưu")),
//         e("p", null, e("a", { href: "/change-password" }, "Đổi mật khẩu")),
//         e("p", null, e("a", { href: "/?chat=1" }, "Quay lại chat"))
//       )
//     ));
//   }

//   function ChangePasswordPage() {
//     const [currentPassword, setCurrentPassword] = React.useState("");
//     const [newPassword, setNewPassword] = React.useState("");
//     const { msg, setMsg } = useNotice();
//     const submit = async (ev) => {
//       ev.preventDefault();
//       const form = new FormData();
//       form.append("current_password", currentPassword);
//       form.append("new_password", newPassword);
//       try {
//         const data = await fetchJson("/api/change-password", { method: "POST", body: form });
//         setMsg(data.message || "Đã xử lý.");
//       } catch (err) {
//         setMsg(err.message);
//       }
//     };
//     return e(Wrap, null, e("div", { className: "card" },
//       e("h2", null, "Đổi mật khẩu"),
//       msg ? e("div", { className: "msg" }, msg) : null,
//       e("form", { onSubmit: submit },
//         e("input", { type: "password", value: currentPassword, onChange: (v) => setCurrentPassword(v.target.value), placeholder: "Mật khẩu hiện tại", required: true }),
//         e("input", { type: "password", value: newPassword, onChange: (v) => setNewPassword(v.target.value), placeholder: "Mật khẩu mới", required: true }),
//         e("button", { type: "submit" }, "Cập nhật")
//       )
//     ));
//   }

//   function AdminDashboard() {
//     const [stats, setStats] = React.useState(null);
//     React.useEffect(() => {
//       fetchJson("/api/admin/overview").then(setStats).catch(() => setStats({ total_users: "-", active_users: "-", total_documents: "-" }));
//     }, []);
//     return e(Wrap, null,
//       e("div", { className: "card" }, e("h2", null, "Admin Dashboard"),
//         e("div", { className: "row" },
//           e("a", { href: "/admin/upload" }, "Quản lý tài liệu"),
//           e("a", { href: "/admin/users" }, "Quản lý user"),
//           e("a", { href: "/?chat=1" }, "Vào chat")
//         )
//       ),
//       e("div", { className: "grid3" },
//         e("div", { className: "card" }, e("div", { className: "stat" }, stats ? stats.total_users : "..."), e("div", null, "Tổng user")),
//         e("div", { className: "card" }, e("div", { className: "stat" }, stats ? stats.active_users : "..."), e("div", null, "User hoạt động")),
//         e("div", { className: "card" }, e("div", { className: "stat" }, stats ? stats.total_documents : "..."), e("div", null, "Tài liệu"))
//       ),
//       stats && typeof stats.total_users === "undefined" ? e("div", { className: "card" }, e("p", null, "Không tải được số liệu dashboard.")) : null
//     );
//   }

//   function AdminDocuments() {
//     const [docs, setDocs] = React.useState([]);
//     const [query, setQuery] = React.useState("");
//     const [selected, setSelected] = React.useState(null);
//     const [uploadFile, setUploadFile] = React.useState(null);
//     const { msg, setMsg } = useNotice();
//     const load = async () => {
//       try {
//         const data = await fetchJson("/api/admin/documents?query=" + encodeURIComponent(query));
//         setDocs(Array.isArray(data) ? data : []);
//       } catch (err) {
//         setMsg(err.message);
//       }
//     };
//     React.useEffect(() => { load(); }, []);
//     const upload = async (ev) => {
//       ev.preventDefault();
//       if (!uploadFile) return;
//       const form = new FormData();
//       form.append("file", uploadFile);
//       try {
//         const data = await fetchJson("/admin/upload", { method: "POST", body: form });
//         setMsg(data.message || "Đã upload.");
//         load();
//       } catch (err) {
//         setMsg(err.message);
//       }
//     };
//     const delDoc = async (id) => {
//       try {
//         const data = await fetchJson("/api/admin/documents/" + id, { method: "DELETE" });
//         setMsg(data.message || "Đã xóa.");
//         setSelected(null);
//         load();
//       } catch (err) {
//         setMsg(err.message);
//       }
//     };
//     const detail = async (id) => {
//       try {
//         const data = await fetchJson("/api/admin/documents/" + id);
//         setSelected(data);
//       } catch (err) {
//         setMsg(err.message);
//       }
//     };
//     return e(Wrap, null,
//       e("div", { className: "card" },
//         e("h2", null, "Quản lý tài liệu"),
//         msg ? e("div", { className: "msg" }, msg) : null,
//         e("form", { className: "row", onSubmit: upload },
//           e("input", { type: "file", onChange: (v) => setUploadFile(v.target.files[0]), accept: ".pdf,.md,.docx" }),
//           e("button", { type: "submit" }, "Upload")
//         ),
//         e("div", { className: "row" },
//           e("input", { value: query, onChange: (v) => setQuery(v.target.value), placeholder: "Tìm tài liệu" }),
//           e("button", { onClick: load, type: "button" }, "Lọc")
//         ),
//         e("table", null, e("thead", null, e("tr", null, e("th", null, "Tên"), e("th", null, "Loại"), e("th", null, "Action"))),
//           e("tbody", null, docs.length === 0 ? e("tr", null, e("td", { colSpan: 3 }, "Chưa có tài liệu trong database.")) : docs.map((d) => e("tr", { key: d.id },
//             e("td", null, d.file_name),
//             e("td", null, d.file_type),
//             e("td", null,
//               e("button", { className: "ghost", onClick: () => detail(d.id), type: "button" }, "Chi tiết"),
//               " ",
//               e("button", { className: "danger", onClick: () => delDoc(d.id), type: "button" }, "Xóa")
//             )
//           ))))
//       ),
//       selected ? e("div", { className: "card" },
//         e("h3", null, "Chi tiết tài liệu"),
//         e("p", null, "ID: ", selected.id),
//         e("p", null, "Tiêu đề: ", selected.title),
//         e("p", null, "Dung lượng: ", selected.file_size, " bytes"),
//         e("p", null, "Chunks: ", selected.chunk_count)
//       ) : null
//     );
//   }

//   function AdminUsers() {
//     const [users, setUsers] = React.useState([]);
//     const [query, setQuery] = React.useState("");
//     const [role, setRole] = React.useState("");
//     const [active, setActive] = React.useState("all");
//     const { msg, setMsg } = useNotice();
//     const load = async () => {
//       const p = new URLSearchParams({ query, role, active });
//       try {
//         const data = await fetchJson("/api/admin/users?" + p.toString());
//         setUsers(Array.isArray(data) ? data : []);
//       } catch (err) {
//         setMsg(err.message);
//       }
//     };
//     React.useEffect(() => { load(); }, []);
//     const toggle = async (u) => {
//       try {
//         const data = await fetchJson("/api/admin/users/" + u.id + "/active", {
//           method: "PATCH",
//           headers: { "Content-Type": "application/json" },
//           body: JSON.stringify({ is_active: !u.is_active }),
//         });
//         setMsg(data.message || "Đã cập nhật.");
//         load();
//       } catch (err) {
//         setMsg(err.message);
//       }
//     };
//     return e(Wrap, null, e("div", { className: "card" },
//       e("h2", null, "Quản lý người dùng"),
//       msg ? e("div", { className: "msg" }, msg) : null,
//       e("div", { className: "row" },
//         e("input", { value: query, onChange: (v) => setQuery(v.target.value), placeholder: "Tìm theo email/tên" }),
//         e("select", { value: role, onChange: (v) => setRole(v.target.value) }, e("option", { value: "" }, "Mọi vai trò"), e("option", { value: "admin" }, "Admin"), e("option", { value: "user" }, "User")),
//         e("select", { value: active, onChange: (v) => setActive(v.target.value) }, e("option", { value: "all" }, "All"), e("option", { value: "active" }, "Active"), e("option", { value: "inactive" }, "Inactive")),
//         e("button", { type: "button", onClick: load }, "Lọc")
//       ),
//       e("table", null, e("thead", null, e("tr", null, e("th", null, "Email"), e("th", null, "Vai trò"), e("th", null, "Trạng thái"), e("th", null, "Action"))),
//         e("tbody", null, users.length === 0 ? e("tr", null, e("td", { colSpan: 4 }, "Không có user theo điều kiện lọc.")) : users.map((u) => e("tr", { key: u.id },
//           e("td", null, u.email),
//           e("td", null, u.role),
//           e("td", null, e("span", { className: "badge " + (u.is_active ? "ok" : "off") }, u.is_active ? "Active" : "Inactive")),
//           e("td", null, e("button", { type: "button", className: u.is_active ? "danger" : "ghost", onClick: () => toggle(u) }, u.is_active ? "Deactivate" : "Activate"))
//         ))))
//     ));
//   }

//   const map = {
//     register: RegisterPage,
//     profile: ProfilePage,
//     "change-password": ChangePasswordPage,
//     "admin-dashboard": AdminDashboard,
//     "admin-documents": AdminDocuments,
//     "admin-users": AdminUsers,
//   };
//   const Comp = map[page] || (() => e(Wrap, null, e("div", { className: "card" }, e("h2", null, "Page not found"))));
//   root.render(e(Comp));
// })();

(function () {
  const e = React.createElement;
  const root = ReactDOM.createRoot(document.getElementById("app"));
  const page = document.body.dataset.page;

  function useNotice() {
    const [msg, setMsg] = React.useState("");
    return { msg, setMsg };
  }

  async function fetchJson(url, options) {
    const res = await fetch(url, options);
    let data = {};
    try { data = await res.json(); } catch (_) {}
    if (!res.ok) throw new Error(data.message || "Có lỗi xảy ra.");
    return data;
  }

  /* ── Helpers ── */
  function Wrap(props) {
    return e("div", { className: props.wide ? "wrap-wide" : "wrap" }, props.children);
  }

  function Field({ label, children }) {
    return e("div", { className: "field" },
      label ? e("label", null, label) : null,
      children
    );
  }

  function Notice({ msg }) {
    if (!msg) return null;
    return e("div", { className: "msg" }, e("span", null, "ℹ"), e("span", null, msg));
  }

  /* ──────────────────────────────
     Register Page
  ────────────────────────────── */
  function RegisterPage() {
    const [email, setEmail] = React.useState("");
    const [displayName, setDisplayName] = React.useState("");
    const [password, setPassword] = React.useState("");
    const { msg, setMsg } = useNotice();

    const onSubmit = async (ev) => {
      ev.preventDefault();
      const form = new FormData();
      form.append("email", email);
      form.append("display_name", displayName);
      form.append("password", password);
      try {
        const data = await fetchJson("/register", { method: "POST", body: form });
        setMsg(data.message || "Xử lý xong.");
      } catch (err) { setMsg(err.message); }
    };

    return e(Wrap, null,
      e("div", { className: "card" },
        e("h2", null, "Đăng ký tài khoản"),
        e(Notice, { msg }),
        e("form", { onSubmit },
          e(Field, { label: "Email" },
            e("input", { value: email, onChange: v => setEmail(v.target.value), placeholder: "you@example.com", type: "email", required: true })
          ),
          e(Field, { label: "Tên hiển thị" },
            e("input", { value: displayName, onChange: v => setDisplayName(v.target.value), placeholder: "Nguyễn Văn A", required: true })
          ),
          e(Field, { label: "Mật khẩu" },
            e("input", { value: password, onChange: v => setPassword(v.target.value), placeholder: "Tối thiểu 8 ký tự", type: "password", required: true })
          ),
          e("div", { style: { marginTop: "8px" } },
            e("button", { type: "submit", style: { width: "100%", padding: "13px" } }, "Tạo tài khoản")
          )
        ),
        e("div", { className: "divider" }),
        e("p", { style: { margin: 0, fontSize: "14px", color: "var(--text-secondary)", textAlign: "center" } },
          "Đã có tài khoản? ", e("a", { href: "/" }, "Đăng nhập")
        )
      )
    );
  }

  /* ──────────────────────────────
     Profile Page
  ────────────────────────────── */
  function ProfilePage() {
    const [u, setU] = React.useState(null);
    const [displayName, setDisplayName] = React.useState("");
    const [saving, setSaving] = React.useState(false);
    const { msg, setMsg } = useNotice();

    React.useEffect(() => {
      fetchJson("/api/profile")
        .then(d => { setU(d); setDisplayName(d.display_name || ""); })
        .catch(err => setMsg(err.message));
    }, []);

    const initials = displayName
      ? displayName.split(" ").map(w => w[0]).slice(0, 2).join("").toUpperCase()
      : "?";

    const save = async (ev) => {
      ev.preventDefault();
      setSaving(true);
      try {
        const data = await fetchJson("/api/profile", {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ display_name: displayName })
        });
        setMsg(data.message || "Đã lưu thành công.");
        if (u) setU({ ...u, display_name: displayName });
      } catch (err) {
        setMsg(err.message);
      } finally { setSaving(false); }
    };

    return e(Wrap, null,
      e("div", { className: "card" },
        e("h2", null, "Thông tin tài khoản"),
        e(Notice, { msg }),
        !u
          ? e("p", { style: { color: "var(--text-secondary)" } }, "Đang tải...")
          : e("div", null,
              /* Avatar block */
              e("div", { className: "avatar-block" },
                e("div", { className: "avatar" }, initials),
                e("div", { className: "avatar-info" },
                  e("div", { style: { fontWeight: 600, fontSize: "15px" } }, displayName || "—"),
                  e("div", { className: "email" }, u.email)
                )
              ),

              /* Edit form */
              e("form", { onSubmit: save },
                e(Field, { label: "Tên hiển thị" },
                  e("input", {
                    value: displayName,
                    onChange: v => setDisplayName(v.target.value),
                    placeholder: "Nhập tên hiển thị",
                    required: true
                  })
                ),
                e(Field, { label: "Email" },
                  e("input", {
                    value: u.email,
                    disabled: true,
                    style: { opacity: 0.5, cursor: "not-allowed" }
                  })
                ),
                e("div", { style: { marginTop: "8px", display: "flex", gap: "10px" } },
                  e("button", { type: "submit", disabled: saving },
                    saving ? "Đang lưu..." : "Lưu thay đổi"
                  ),
                  e("a", { href: "/change-password" },
                    e("button", { type: "button", className: "ghost" }, "Đổi mật khẩu")
                  )
                )
              )
            )
      ),
      e("p", { style: { textAlign: "center", fontSize: "14px" } },
        e("a", { href: "/?chat=1" }, "← Quay lại chat")
      )
    );
  }

  /* ──────────────────────────────
     Change Password Page
  ────────────────────────────── */
  function ChangePasswordPage() {
    const [currentPassword, setCurrentPassword] = React.useState("");
    const [newPassword, setNewPassword] = React.useState("");
    const { msg, setMsg } = useNotice();

    const submit = async (ev) => {
      ev.preventDefault();
      const form = new FormData();
      form.append("current_password", currentPassword);
      form.append("new_password", newPassword);
      try {
        const data = await fetchJson("/api/change-password", { method: "POST", body: form });
        setMsg(data.message || "Đã cập nhật mật khẩu.");
        setCurrentPassword(""); setNewPassword("");
      } catch (err) { setMsg(err.message); }
    };

    return e(Wrap, null,
      e("div", { className: "card" },
        e("h2", null, "Đổi mật khẩu"),
        e(Notice, { msg }),
        e("form", { onSubmit: submit },
          e(Field, { label: "Mật khẩu hiện tại" },
            e("input", { type: "password", value: currentPassword, onChange: v => setCurrentPassword(v.target.value), placeholder: "••••••••", required: true })
          ),
          e(Field, { label: "Mật khẩu mới" },
            e("input", { type: "password", value: newPassword, onChange: v => setNewPassword(v.target.value), placeholder: "••••••••", required: true })
          ),
          e("div", { style: { marginTop: "8px" } },
            e("button", { type: "submit", style: { width: "100%" } }, "Cập nhật mật khẩu")
          )
        )
      ),
      e("p", { style: { textAlign: "center", fontSize: "14px" } },
        e("a", { href: "/profile" }, "← Quay lại hồ sơ")
      )
    );
  }

  /* ──────────────────────────────
     Admin Dashboard
  ────────────────────────────── */
  function AdminDashboard() {
    const [stats, setStats] = React.useState(null);
    React.useEffect(() => {
      fetchJson("/api/admin/overview")
        .then(setStats)
        .catch(() => setStats({ total_users: "-", active_users: "-", total_documents: "-" }));
    }, []);

    return e(Wrap, { wide: true },
      e("div", { className: "card" },
        e("h2", null, "Admin Dashboard"),
        e("div", { className: "nav-links" },
          e("a", { href: "/admin/upload" }, "📄 Quản lý tài liệu"),
          e("a", { href: "/admin/users" }, "👥 Quản lý user"),
          e("a", { href: "/?chat=1" }, "💬 Vào chat")
        )
      ),
      e("div", { className: "grid3" },
        e("div", { className: "card", style: { "--i": 0 } },
          e("div", { className: "stat" }, stats ? stats.total_users : "…"),
          e("div", { className: "stat-label" }, "Tổng người dùng")
        ),
        e("div", { className: "card", style: { "--i": 1 } },
          e("div", { className: "stat" }, stats ? stats.active_users : "…"),
          e("div", { className: "stat-label" }, "Đang hoạt động")
        ),
        e("div", { className: "card", style: { "--i": 2 } },
          e("div", { className: "stat" }, stats ? stats.total_documents : "…"),
          e("div", { className: "stat-label" }, "Tài liệu")
        )
      )
    );
  }

  /* ──────────────────────────────
     Admin Documents
  ────────────────────────────── */
  function AdminDocuments() {
    const [docs, setDocs] = React.useState([]);
    const [query, setQuery] = React.useState("");
    const [selected, setSelected] = React.useState(null);
    const [uploadFile, setUploadFile] = React.useState(null);
    const { msg, setMsg } = useNotice();

    const load = async () => {
      try {
        const data = await fetchJson("/api/admin/documents?query=" + encodeURIComponent(query));
        setDocs(Array.isArray(data) ? data : []);
      } catch (err) { setMsg(err.message); }
    };
    React.useEffect(() => { load(); }, []);

    const upload = async (ev) => {
      ev.preventDefault();
      if (!uploadFile) return;
      const form = new FormData();
      form.append("file", uploadFile);
      try {
        const data = await fetchJson("/admin/upload", { method: "POST", body: form });
        setMsg(data.message || "Đã upload thành công.");
        load();
      } catch (err) { setMsg(err.message); }
    };

    const delDoc = async (id) => {
      if (!confirm("Xóa tài liệu này?")) return;
      try {
        const data = await fetchJson("/api/admin/documents/" + id, { method: "DELETE" });
        setMsg(data.message || "Đã xóa.");
        setSelected(null); load();
      } catch (err) { setMsg(err.message); }
    };

    const detail = async (id) => {
      try {
        const data = await fetchJson("/api/admin/documents/" + id);
        setSelected(data);
      } catch (err) { setMsg(err.message); }
    };

    return e(Wrap, { wide: true },
      e("div", { className: "card" },
        e("h2", null, "Quản lý tài liệu"),
        e(Notice, { msg }),

        /* Upload */
        e("div", { style: { marginBottom: "20px" } },
          e("h3", null, "Tải lên tài liệu"),
          e("form", { className: "row", onSubmit: upload },
            e("input", { type: "file", onChange: v => setUploadFile(v.target.files[0]), accept: ".pdf,.md,.docx", style: { flex: "1 1 200px" } }),
            e("button", { type: "submit" }, "Upload")
          )
        ),

        e("div", { className: "divider" }),

        /* Search */
        e("div", { className: "row", style: { marginBottom: "16px" } },
          e("input", { value: query, onChange: v => setQuery(v.target.value), placeholder: "Tìm theo tên tài liệu…", style: { flex: "1" } }),
          e("button", { onClick: load, type: "button" }, "Lọc")
        ),

        /* Table */
        e("table", null,
          e("thead", null,
            e("tr", null, e("th", null, "Tên tài liệu"), e("th", null, "Loại"), e("th", null, "Thao tác"))
          ),
          e("tbody", null,
            docs.length === 0
              ? e("tr", null, e("td", { colSpan: 3, style: { textAlign: "center", color: "var(--text-muted)", padding: "28px" } }, "Chưa có tài liệu nào."))
              : docs.map(d => e("tr", { key: d.id },
                  e("td", null, d.title || d.file_name),
                  e("td", null, e("span", { className: "badge", style: { background: "rgba(255,255,255,0.06)", border: "1px solid var(--border)", color: "var(--text-secondary)" } }, d.file_type)),
                  e("td", null,
                    e("div", { style: { display: "flex", gap: "8px" } },
                      e("button", { className: "ghost", onClick: () => detail(d.id), type: "button", style: { padding: "6px 12px", fontSize: "13px" } }, "Chi tiết"),
                      e("button", { className: "danger", onClick: () => delDoc(d.id), type: "button", style: { padding: "6px 12px", fontSize: "13px" } }, "Xóa")
                    )
                  )
                ))
          )
        )
      ),

      /* Detail panel */
      selected ? e("div", { className: "card" },
        e("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" } },
          e("h3", { style: { margin: 0 } }, "Chi tiết tài liệu"),
          e("button", { className: "ghost", onClick: () => setSelected(null), style: { padding: "4px 10px", fontSize: "13px" } }, "✕")
        ),
        e("div", { style: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" } },
          e("div", null, e("div", { style: { fontSize: "12px", color: "var(--text-muted)", marginBottom: "4px" } }, "ID"), e("div", null, selected.id)),
          e("div", null, e("div", { style: { fontSize: "12px", color: "var(--text-muted)", marginBottom: "4px" } }, "Tiêu đề"), e("div", null, selected.title)),
          e("div", null, e("div", { style: { fontSize: "12px", color: "var(--text-muted)", marginBottom: "4px" } }, "Dung lượng"), e("div", null, (selected.file_size || 0).toLocaleString() + " KB")),
          e("div", null, e("div", { style: { fontSize: "12px", color: "var(--text-muted)", marginBottom: "4px" } }, "Loại tệp"), e("div", null, selected.file_type)),
          e("div", null, e("div", { style: { fontSize: "12px", color: "var(--text-muted)", marginBottom: "4px" } }, "Được upload bởi"), e("div", null, selected.uploader_name || "—")),
          e("div", null, e("div", { style: { fontSize: "12px", color: "var(--text-muted)", marginBottom: "4px" } }, "Thời gian upload"), e("div", null, new Date(selected.created_at).toLocaleString())),
        )
      ) : null
    );
  }

  /* ──────────────────────────────
     Admin Users
  ────────────────────────────── */
  function AdminUsers() {
    const [users, setUsers] = React.useState([]);
    const [query, setQuery] = React.useState("");
    const [role, setRole] = React.useState("");
    const [active, setActive] = React.useState("all");
    const { msg, setMsg } = useNotice();

    const load = async () => {
      const p = new URLSearchParams({ query, role, active });
      try {
        const data = await fetchJson("/api/admin/users?" + p.toString());
        setUsers(Array.isArray(data) ? data : []);
      } catch (err) { setMsg(err.message); }
    };
    React.useEffect(() => { load(); }, []);

    const toggle = async (u) => {
      try {
        const data = await fetchJson("/api/admin/users/" + u.id + "/active", {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ is_active: !u.is_active })
        });
        setMsg(data.message || "Đã cập nhật.");
        load();
      } catch (err) { setMsg(err.message); }
    };

    return e(Wrap, { wide: true },
      e("div", { className: "card" },
        e("h2", null, "Quản lý người dùng"),
        e(Notice, { msg }),

        e("div", { className: "row", style: { marginBottom: "16px" } },
          e("input", { value: query, onChange: v => setQuery(v.target.value), placeholder: "Tìm theo email / tên…", style: { flex: "1 1 180px" } }),
          e("select", { value: role, onChange: v => setRole(v.target.value), style: { flex: "0 1 140px" } },
            e("option", { value: "" }, "Mọi vai trò"),
            e("option", { value: "admin" }, "Quản trị viên"),
            e("option", { value: "user" }, "Nguời dùng")
          ),
          e("select", { value: active, onChange: v => setActive(v.target.value), style: { flex: "0 1 130px" } },
            e("option", { value: "all" }, "Tất cả"),
            e("option", { value: "active" }, "Hoạt động"),
            e("option", { value: "inactive" }, "Không hoạt động")
          ),
          e("button", { type: "button", onClick: load }, "Lọc")
        ),

        e("table", null,
          e("thead", null,
            e("tr", null, e("th", null, "Email"), e("th", null, "Vai trò"), e("th", null, "Trạng thái"), e("th", null, "Thao tác"))
          ),
          e("tbody", null,
            users.length === 0
              ? e("tr", null, e("td", { colSpan: 4, style: { textAlign: "center", color: "var(--text-muted)", padding: "28px" } }, "Không có user phù hợp."))
              : users.map(u => e("tr", { key: u.id },
                  e("td", null, u.email),
                  e("td", null, e("span", { style: { fontSize: "13px", color: "var(--text-secondary)" } }, u.role)),
                  e("td", null, e("span", { className: "badge " + (u.is_active ? "ok" : "off") }, u.is_active ? "Hoạt động" : "Ngừng hoạt động")),
                  e("td", null,
                    e("button", {
                      type: "button",
                      className: u.is_active ? "danger" : "ghost",
                      onClick: () => toggle(u),
                      style: { padding: "6px 12px", fontSize: "13px" }
                    }, u.is_active ? "Ngừng hoạt động" : "Kích hoạt")
                  )
                ))
          )
        )
      )
    );
  }

  /* ── Router ── */
  const map = {
    register: RegisterPage,
    profile: ProfilePage,
    "change-password": ChangePasswordPage,
    "admin-dashboard": AdminDashboard,
    "admin-documents": AdminDocuments,
    "admin-users": AdminUsers,
  };
  const Comp = map[page] || (() => e(Wrap, null, e("div", { className: "card" }, e("h2", null, "Trang không tồn tại"))));
  root.render(e(Comp));
})();