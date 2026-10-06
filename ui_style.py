CSS = """
@import url('https://fonts.googleapis.com/css2?family=Prompt:wght@400;500;600;700&display=swap');

html, body, [class*="css"], .stApp, button, input, textarea {
  font-family: 'Prompt', 'Noto Sans Thai', 'Leelawadee UI', sans-serif !important;
}
.stApp { background: #F8FAFC; }
#MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }
.block-container { max-width: 1180px; padding-top: 0.5rem; padding-bottom: 3rem; }

/* ---------- header ---------- */
.lc-header { display:flex; align-items:center; gap:12px; padding:14px 4px 6px 4px; }
.lc-logo { font-size:1.6rem; font-weight:700; color:#1E3A8A; }
.lc-badge { background:#DBEAFE; color:#1E3A8A; font-size:.8rem; font-weight:600; padding:4px 10px; border-radius:8px; }

/* ---------- tabs (เป็นเมนูด้านบน) ---------- */
.stTabs [data-baseweb="tab-list"] { gap:8px; border-bottom:1px solid #E5E7EB; padding-bottom:6px; }
.stTabs [data-baseweb="tab"] { height:42px; padding:0 18px; border-radius:10px; color:#374151; font-weight:500; background:transparent; }
.stTabs [aria-selected="true"] { background:#DBEAFE; color:#1E3A8A; font-weight:600; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display:none; }

/* ---------- hero ---------- */
.lc-hero { background:linear-gradient(135deg,#1E3A8A 0%,#0F3D6B 100%); color:#fff; border-radius:24px; padding:32px 34px; margin:14px 0 18px 0; }
.lc-hero h1 { color:#fff; font-size:1.9rem; margin:0 0 10px 0; font-weight:700; padding:0; }
.lc-hero p { color:#DBEAFE; margin:0 0 18px 0; font-size:1rem; }
.lc-chip { display:inline-block; padding:8px 16px; border-radius:999px; font-size:.85rem; font-weight:500; margin:0 8px 6px 0; border:1px solid; }
.lc-chip.red { background:rgba(239,68,68,.18); border-color:#F87171; color:#FECACA; }
.lc-chip.yellow { background:rgba(250,204,21,.16); border-color:#FACC15; color:#FEF08A; }
.lc-chip.green { background:rgba(16,185,129,.18); border-color:#34D399; color:#A7F3D0; }

/* ---------- uploader ---------- */
[data-testid="stFileUploaderDropzone"] { border:2px dashed #93C5FD; background:#EFF6FF; border-radius:16px; padding:34px 20px; }
.lc-or { text-align:center; color:#6B7280; font-size:.9rem; margin:14px 0; }

/* ---------- sample cards ---------- */
.lc-sample { border-radius:14px; padding:14px 16px; border:1px solid; min-height:92px; margin-bottom:6px; }
.lc-sample b { font-size:1rem; }
.lc-sample div { color:#4B5563; font-size:.85rem; margin-top:4px; }
.lc-sample.red { background:#FFF5F5; border-color:#F87171; } .lc-sample.red b { color:#991B1B; }
.lc-sample.yellow { background:#FFFBEA; border-color:#FACC15; } .lc-sample.yellow b { color:#92400E; }
.lc-sample.green { background:#F0FDF4; border-color:#34D399; } .lc-sample.green b { color:#065F46; }

/* ---------- buttons ---------- */
.stButton > button[kind="primary"] { background:#1E3A8A; color:#fff; border:none; border-radius:12px; padding:14px 18px; font-weight:600; font-size:1.05rem; width:100%; }
.stButton > button[kind="primary"]:hover { background:#1D4ED8; color:#fff; }
.stButton > button[kind="secondary"] { border-radius:10px; border:1px solid #D1D5DB; width:100%; }

/* ---------- results ---------- */
.lc-stats { display:flex; gap:12px; margin:8px 0 16px 0; flex-wrap:wrap; }
.lc-stat { flex:1; min-width:150px; border-radius:14px; padding:14px 18px; border:1px solid; }
.lc-stat .n { font-size:1.8rem; font-weight:700; line-height:1.1; }
.lc-stat .t { font-size:.85rem; }
.lc-stat.red { background:#FFF5F5; border-color:#FCA5A5; color:#991B1B; }
.lc-stat.yellow { background:#FFFBEA; border-color:#FDE68A; color:#92400E; }
.lc-stat.green { background:#F0FDF4; border-color:#6EE7B7; color:#065F46; }
.lc-stat.gray { background:#F3F4F6; border-color:#D1D5DB; color:#4B5563; }

.lc-res { border-radius:14px; border:1px solid; margin:10px 0; background:#fff; overflow:hidden; }
.lc-res summary { cursor:pointer; padding:14px 18px; display:flex; align-items:center; gap:10px; list-style:none; font-size:1rem; }
.lc-res summary::-webkit-details-marker { display:none; }
.lc-res .ttl { flex:1; font-weight:600; color:#111827; }
.lc-res .pill { font-size:.78rem; font-weight:600; padding:3px 10px; border-radius:999px; }
.lc-res .body { padding:2px 20px 16px 20px; color:#1F2937; font-size:.95rem; line-height:1.6; }
.lc-res .sub { font-weight:600; margin-top:10px; font-size:.9rem; color:#374151; }
.lc-res ul { margin:4px 0 4px 20px; padding:0; }
.lc-res .ref { color:#6B7280; font-size:.82rem; margin-top:8px; }
.lc-res .orig { margin-top:10px; font-size:.85rem; color:#4B5563; }
.lc-res .orig summary { padding:4px 0; font-size:.85rem; color:#2563EB; }
.lc-res .origtxt { background:#F9FAFB; border-radius:8px; padding:10px 12px; color:#374151; }
.lc-res.red { border-color:#FCA5A5; background:#FFF8F8; } .lc-res.red .pill { background:#FEE2E2; color:#991B1B; }
.lc-res.yellow { border-color:#FDE68A; background:#FFFDF2; } .lc-res.yellow .pill { background:#FEF3C7; color:#92400E; }
.lc-res.green { border-color:#A7F3D0; background:#F6FEF9; } .lc-res.green .pill { background:#D1FAE5; color:#065F46; }
.lc-res.gray { border-color:#D1D5DB; background:#F9FAFB; } .lc-res.gray .pill { background:#E5E7EB; color:#4B5563; }

/* ---------- calculator ---------- */
.lc-calc { background:#F8FAFC; border:1px solid #E5E7EB; border-radius:16px; padding:20px 24px; margin-top:14px; }
.lc-calc h4 { margin:0 0 12px 0; color:#111827; }
.lc-row { display:flex; justify-content:space-between; padding:6px 0; color:#374151; }
.lc-row .v { font-weight:600; }
.lc-row .v.bad { color:#991B1B; } .lc-row .v.ok { color:#065F46; }
.lc-total { display:flex; justify-content:space-between; align-items:center; border-top:1px solid #E5E7EB; margin-top:10px; padding-top:14px; }
.lc-total .big { font-size:2rem; font-weight:700; color:#DC2626; }
.lc-total .big.ok { color:#059669; }
.lc-tip { background:#EFF6FF; border-radius:10px; padding:10px 14px; color:#1E3A8A; font-size:.88rem; margin-top:14px; }

/* ---------- criteria ---------- */
.lc-help { display:flex; justify-content:space-between; align-items:center; background:#FEE2E2; border:1px solid #FCA5A5; border-radius:16px; padding:18px 22px; margin:12px 0 18px 0; gap:16px; flex-wrap:wrap; }
.lc-help b { color:#991B1B; font-size:1.15rem; }
.lc-help div div { color:#7F1D1D; font-size:.9rem; }
.lc-call { background:#DC2626; color:#fff !important; text-decoration:none; padding:10px 22px; border-radius:10px; font-weight:600; }
.lc-rule { display:flex; gap:14px; align-items:flex-start; border:1px solid #E5E7EB; border-radius:12px; padding:14px 18px; margin:10px 0; background:#fff; }
.lc-rule .tag { font-size:.75rem; font-weight:600; padding:3px 10px; border-radius:8px; white-space:nowrap; }
.lc-rule .tag.ban { background:#FEE2E2; color:#991B1B; } .lc-rule .tag.right { background:#D1FAE5; color:#065F46; }
.lc-rule b { color:#111827; }
.lc-rule div div { color:#6B7280; font-size:.88rem; margin-top:2px; }
.lc-note { background:#FFFBEB; border:1px solid #FDE68A; border-radius:12px; padding:12px 16px; color:#78350F; font-size:.88rem; margin:12px 0; }
.lc-foot { color:#6B7280; font-size:.8rem; text-align:center; margin-top:28px; }

/* ---------- มือถือ / หน้าจอแคบ ---------- */
@media (max-width: 640px) {
  .block-container { padding-left: .75rem !important; padding-right: .75rem !important; padding-top: .25rem !important; }
  .stApp h2, .stApp h3 { font-size: 1.15rem !important; line-height: 1.4 !important; }
  .lc-header { padding: 8px 2px 4px 2px; gap: 8px; }
  .lc-logo { font-size: 1.25rem; }
  .lc-badge { font-size: .7rem; padding: 3px 8px; }
  .stTabs [data-baseweb="tab-list"] { gap: 2px; overflow-x: auto; flex-wrap: nowrap; }
  .stTabs [data-baseweb="tab"] { height: 38px; padding: 0 10px; font-size: .82rem; white-space: nowrap; }
  .lc-hero { padding: 20px 18px; border-radius: 18px; margin: 10px 0 14px 0; }
  .lc-hero h1 { font-size: 1.35rem; line-height: 1.35; }
  .lc-hero p { font-size: .88rem; margin-bottom: 12px; }
  .lc-chip { display: block; margin: 0 0 8px 0; padding: 8px 12px; font-size: .8rem; border-radius: 12px; }
  [data-testid="stFileUploaderDropzone"] { padding: 18px 12px; }
  .lc-sample { min-height: 0; padding: 12px 14px; }
  .lc-stats { gap: 8px; }
  .lc-stat { flex: 1 1 calc(50% - 8px); min-width: 0; padding: 10px 12px; }
  .lc-stat .n { font-size: 1.5rem; }
  .lc-res summary { padding: 12px; font-size: .92rem; gap: 8px; flex-wrap: wrap; }
  .lc-res .ttl { flex: 1 1 60%; min-width: 0; }
  .lc-res .body { padding: 2px 14px 14px 14px; font-size: .9rem; }
  .lc-calc { padding: 14px; }
  .lc-row { flex-direction: column; gap: 2px; padding: 8px 0; border-bottom: 1px solid #EEF2F7; }
  .lc-total { flex-direction: column; align-items: flex-start; gap: 6px; }
  .lc-total .big { font-size: 1.6rem; }
  .lc-help { padding: 14px; }
  .lc-call { width: 100%; text-align: center; box-sizing: border-box; }
  .lc-rule { flex-direction: column; gap: 8px; padding: 12px; }
  .lc-note { font-size: .82rem; }
  .lc-foot { font-size: .72rem; }
}
"""
