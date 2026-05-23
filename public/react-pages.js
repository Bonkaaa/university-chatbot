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
     Mini SVG Area Chart
  ────────────────────────────── */
  function AreaChart({ data, color = "#e8315c", height = 120 }) {
    if (!data || data.length === 0) return null;
    const W = 600, H = height;
    const PAD = { top: 12, right: 8, bottom: 28, left: 32 };
    const innerW = W - PAD.left - PAD.right;
    const innerH = H - PAD.top - PAD.bottom;
    const maxVal = Math.max(...data.map(d => d.count), 1);
    const xStep = innerW / (data.length - 1);

    const pts = data.map((d, i) => ({
      x: PAD.left + i * xStep,
      y: PAD.top + innerH - (d.count / maxVal) * innerH,
      count: d.count,
      hour: d.hour,
    }));

    const linePath = pts.map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ");
    const areaPath = linePath
      + ` L${pts[pts.length-1].x.toFixed(1)},${(PAD.top + innerH).toFixed(1)}`
      + ` L${pts[0].x.toFixed(1)},${(PAD.top + innerH).toFixed(1)} Z`;

    // X-axis labels: every 3 hours
    const xLabels = data.filter(d => d.hour % 3 === 0);

    // Y-axis: 3 ticks
    const yTicks = [0, Math.round(maxVal / 2), maxVal];

    const gradId = "areaGrad";

    return e("svg", {
      viewBox: `0 0 ${W} ${H}`,
      style: { width: "100%", height: H, overflow: "visible" },
      xmlns: "http://www.w3.org/2000/svg",
    },
      e("defs", null,
        e("linearGradient", { id: gradId, x1: "0", y1: "0", x2: "0", y2: "1" },
          e("stop", { offset: "0%",   stopColor: color, stopOpacity: "0.35" }),
          e("stop", { offset: "100%", stopColor: color, stopOpacity: "0.02" })
        )
      ),
      /* grid lines */
      yTicks.map(v =>
        e("line", {
          key: v,
          x1: PAD.left, x2: W - PAD.right,
          y1: PAD.top + innerH - (v / maxVal) * innerH,
          y2: PAD.top + innerH - (v / maxVal) * innerH,
          stroke: "rgba(255,255,255,0.07)", strokeDasharray: "4 3",
        })
      ),
      /* area fill */
      e("path", { d: areaPath, fill: `url(#${gradId})` }),
      /* line */
      e("path", { d: linePath, fill: "none", stroke: color, strokeWidth: "2", strokeLinejoin: "round", strokeLinecap: "round" }),
      /* dots on non-zero */
      pts.filter(p => p.count > 0).map(p =>
        e("circle", { key: p.hour, cx: p.x, cy: p.y, r: 3, fill: color, stroke: "#161616", strokeWidth: 1.5 })
      ),
      /* x labels */
      xLabels.map(d => {
        const px = PAD.left + d.hour * xStep;
        return e("text", {
          key: d.hour,
          x: px, y: H - 4,
          textAnchor: "middle",
          fontSize: 10,
          fill: "rgba(255,255,255,0.35)",
        }, `${String(d.hour).padStart(2,"0")}h`);
      }),
      /* y labels */
      yTicks.map(v =>
        e("text", {
          key: v,
          x: PAD.left - 6,
          y: PAD.top + innerH - (v / maxVal) * innerH + 4,
          textAnchor: "end",
          fontSize: 10,
          fill: "rgba(255,255,255,0.35)",
        }, v)
      )
    );
  }

  /* ──────────────────────────────
     Stat Card helper
  ────────────────────────────── */
  function StatCard({ value, label, sub, accent, i }) {
    return e("div", { className: "card dash-stat-card", style: { "--i": i } },
      e("div", { className: "dash-stat-icon", style: { color: accent || "var(--accent)" } }, sub),
      e("div", { className: "stat", style: accent ? { background: `linear-gradient(135deg, #fff 30%, ${accent})`, WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" } : {} }, value ?? "…"),
      e("div", { className: "stat-label" }, label)
    );
  }

  /* ──────────────────────────────
     Admin Dashboard
  ────────────────────────────── */
  function AdminDashboard() {
    const [stats, setStats]       = React.useState(null);
    const [hourData, setHourData] = React.useState([]);
    const [lastUpdate, setLastUpdate] = React.useState(null);
    const [loading, setLoading]   = React.useState(true);

    const load = async () => {
      try {
        const data = await fetchJson("/api/admin/dashboard-stats");
        setStats(data);
        setHourData(data.messages_by_hour || []);
        setLastUpdate(new Date().toLocaleTimeString("vi-VN"));
      } catch (_) {
        setStats(null);
      } finally {
        setLoading(false);
      }
    };

    React.useEffect(() => {
      load();
      const id = setInterval(load, 30000); // refresh mỗi 30s
      return () => clearInterval(id);
    }, []);

    const fmt = (n) => (n == null ? "…" : Number(n).toLocaleString("vi-VN"));
    const fmtMs = (ms) => ms == null ? "…" : ms >= 1000 ? `${(ms/1000).toFixed(1)}s` : `${Math.round(ms)}ms`;

    const totalToday = hourData.reduce((s, d) => s + d.count, 0);
    const peakHour   = hourData.length ? hourData.reduce((a, b) => b.count > a.count ? b : a, hourData[0]) : null;

    return e(Wrap, { wide: true },

      /* ── Header ── */
      e("div", { className: "card dash-header-card" },
        e("div", { style: { display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "12px" } },
          e("div", null,
            e("h2", { style: { margin: 0 } }, "Admin Dashboard"),
            lastUpdate ? e("div", { style: { fontSize: "12px", color: "var(--text-muted)", marginTop: "4px" } }, `Cập nhật lúc ${lastUpdate} · tự làm mới mỗi 30s`) : null
          ),
          e("div", { className: "nav-links", style: { margin: 0 } },
            e("a", { href: "/admin/upload" }, "📄 Tài liệu"),
            e("a", { href: "/admin/users" }, "👥 Người dùng"),
            e("a", { href: "/?chat=1" }, "💬 Chat")
          )
        )
      ),

      /* ── Stats row 1: all-time ── */
      e("div", { style: { marginBottom: "8px", fontSize: "11px", fontWeight: 600, textTransform: "uppercase", letterSpacing: "1px", color: "var(--text-muted)", padding: "0 4px" } }, "Tổng quan"),
      e("div", { className: "grid4" },
        e(StatCard, { i: 0, value: fmt(stats?.total_users),         label: "Tổng người dùng",    sub: "👤", accent: "#38bdf8" }),
        e(StatCard, { i: 1, value: fmt(stats?.active_users),        label: "Đang hoạt động",     sub: "✅", accent: "#4ade80" }),
        e(StatCard, { i: 2, value: fmt(stats?.total_documents),     label: "Tài liệu",           sub: "📄", accent: "#fb923c" }),
        e(StatCard, { i: 3, value: fmt(stats?.total_conversations), label: "Tổng cuộc hội thoại",sub: "💬", accent: "#a78bfa" }),
      ),

      /* ── Stats row 2: today ── */
      e("div", { style: { marginBottom: "8px", marginTop: "16px", fontSize: "11px", fontWeight: 600, textTransform: "uppercase", letterSpacing: "1px", color: "var(--text-muted)", padding: "0 4px" } }, "Hôm nay"),
      e("div", { className: "grid4" },
        e(StatCard, { i: 0, value: fmt(stats?.messages_today),      label: "Tin nhắn gửi đến",   sub: "✉️", accent: "#e8315c" }),
        e(StatCard, { i: 1, value: fmt(stats?.conversations_today), label: "Cuộc hội thoại mới", sub: "🗨️", accent: "#f472b6" }),
        e(StatCard, { i: 2, value: fmt(stats?.new_users_today),     label: "User đăng ký mới",   sub: "🆕", accent: "#34d399" }),
        e(StatCard, { i: 3, value: fmt(stats?.docs_today),          label: "Tài liệu upload",    sub: "📥", accent: "#fbbf24" }),
      ),

      /* ── Stats row 3: performance ── */
      e("div", { style: { marginBottom: "8px", marginTop: "16px", fontSize: "11px", fontWeight: 600, textTransform: "uppercase", letterSpacing: "1px", color: "var(--text-muted)", padding: "0 4px" } }, "Hiệu suất"),
      e("div", { className: "grid2" },
        e(StatCard, { i: 0, value: fmtMs(stats?.avg_response_ms),    label: "Thời gian phản hồi TB",   sub: "⚡", accent: "#38bdf8" }),
        e(StatCard, { i: 1, value: stats?.avg_msg_per_conv != null ? Number(stats.avg_msg_per_conv).toFixed(1) : "…", label: "Tin nhắn TB / hội thoại", sub: "📊", accent: "#a78bfa" }),
      ),

      /* ── Live Chart ── */
      e("div", { className: "card", style: { marginTop: "4px" } },
        e("div", { style: { display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px", flexWrap: "wrap", gap: "8px" } },
          e("div", null,
            e("h3", { style: { margin: 0 } }, "Tin nhắn theo giờ hôm nay"),
            e("div", { style: { fontSize: "12px", color: "var(--text-muted)", marginTop: "3px" } },
              peakHour && peakHour.count > 0
                ? `Giờ cao điểm: ${String(peakHour.hour).padStart(2,"0")}:00 — ${peakHour.count} tin nhắn`
                : "Chưa có dữ liệu hôm nay"
            )
          ),
          e("div", { style: { display: "flex", alignItems: "center", gap: "8px" } },
            e("span", { className: "badge", style: { background: "rgba(232,49,92,0.15)", border: "1px solid rgba(232,49,92,0.3)", color: "#e8315c", fontSize: "12px" } },
              `${totalToday} tin nhắn`
            ),
            loading ? e("span", { style: { fontSize: "12px", color: "var(--text-muted)" } }, "⟳") : null
          )
        ),
        e(AreaChart, { data: hourData, color: "#e8315c", height: 140 })
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

      /* Detail Modal */
      selected ? e("div", {
          className: "modal-backdrop",
          onClick: (ev) => { if (ev.target === ev.currentTarget) setSelected(null); }
        },
        e("div", { className: "modal" },
          e("div", { className: "modal-header" },
            e("h3", null, "Chi tiết tài liệu"),
            e("button", { className: "ghost modal-close", onClick: () => setSelected(null) }, "✕")
          ),
          e("div", { className: "modal-grid" },
            e("div", null,
              e("div", { className: "modal-field-label" }, "Loại"),
              e("div", { className: "modal-field-value" }, selected.file_type || "—")
            ),
            e("div", { style: { gridColumn: "1 / -1" } },
              e("div", { className: "modal-field-label" }, "Tên tài liệu"),
              e("div", { className: "modal-field-value" }, selected.title || selected.file_name || "—")
            ),
            e("div", null,
              e("div", { className: "modal-field-label" }, "Dung lượng"),
              e("div", { className: "modal-field-value" }, (selected.file_size || 0).toLocaleString() + "KB")
            ),
            e("div", null,
              e("div", { className: "modal-field-label" }, "Số chunks"),
              e("div", { className: "modal-field-value" }, selected.chunk_count ?? "—")
            ),
            e("div", null,
              e("div", { className: "modal-field-label" }, "Thời gian tải lên"),
              e("div", { className: "modal-field-value" }, selected.created_at ? new Date(selected.created_at).toLocaleString() : "—")
            ),
            e("div", null,
              e("div", { className: "modal-field-label" }, "Được đăng bởi"),
              e("div", { className: "modal-field-value" }, selected.uploader_name || "—")
            )
          ),
          e("div", { className: "modal-footer" },
            e("button", { className: "ghost", onClick: () => setSelected(null), style: { fontSize: "13px" } }, "Đóng")
          )
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