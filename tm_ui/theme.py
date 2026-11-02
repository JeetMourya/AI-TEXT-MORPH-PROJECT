"""TextMorph visual theme and branding."""

PROJECT_FULL = "Design, Development, and Implementation of an AI-Based Advanced Text Summarization and Paraphrasing System"
DEVELOPERS = ("Jeet Mourya", "Karan")


def get_css(dark=True):
    bg = "#0b1020" if dark else "#f5f7fb"
    panel = "#121a2d" if dark else "#ffffff"
    text = "#edf2ff" if dark else "#172033"
    muted = "#9aa9c2" if dark else "#64748b"
    border = "rgba(148,163,184,.2)"
    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
    :root{{--tm-bg:{bg};--tm-panel:{panel};--tm-text:{text};--tm-muted:{muted};--tm-line:{border};}}
    html,body,[class*='css']{{font-family:'DM Sans',sans-serif;}}
    .stApp{{background:radial-gradient(ellipse at 12% 0%,rgba(104,85,255,.14),transparent 35%),var(--tm-bg);color:var(--tm-text);}}
    [data-testid='stHeader']{{background:transparent;}} [data-testid='stSidebar']{{background:var(--tm-panel);border-right:1px solid var(--tm-line);}}
    .block-container{{max-width:1440px;padding-top:2rem;padding-bottom:3rem;}}
    h1,h2,h3{{font-family:'Manrope',sans-serif!important;color:var(--tm-text)!important;letter-spacing:-.025em;}}
    p,label,.stCaption{{color:var(--tm-muted);}}
    .tm-hero{{padding:25px 28px;border:1px solid rgba(139,124,255,.3);border-radius:22px;background:linear-gradient(115deg,rgba(93,78,194,.3),rgba(29,163,164,.12)),var(--tm-panel);margin-bottom:20px;}}
    .tm-hero h1{{color:#fff!important;font-size:2.5rem;margin:4px 0;}}
    .tm-hero p{{color:#c3cde0;margin:0;}}
    .tm-page-title{{font-family:'Manrope',sans-serif;font-size:1.9rem;font-weight:800;color:var(--tm-text);letter-spacing:-.04em;}}
    .tm-page-desc{{color:var(--tm-muted);font-size:.92rem;margin:4px 0 18px;line-height:1.55;}}
    .tm-section-title{{font-family:'Manrope',sans-serif;font-size:1.05rem;font-weight:800;color:var(--tm-text);margin:4px 0 12px;}}
    .tm-card{{background:var(--tm-panel);border:1px solid var(--tm-line);border-radius:17px;padding:14px;}}
    [data-testid='stVerticalBlockBorderWrapper']{{border-color:var(--tm-line)!important;border-radius:17px!important;}}
    div[data-testid='stTextArea'] textarea{{background:{'#0d1526' if dark else '#ffffff'}!important;color:var(--tm-text)!important;border:1px solid var(--tm-line)!important;border-radius:12px!important;line-height:1.6!important;}}
    .stButton>button,.stDownloadButton>button{{border-radius:10px!important;min-height:2.65rem;font-weight:700!important;border:1px solid var(--tm-line)!important;}}
    .stButton>button[kind='primary']{{background:linear-gradient(100deg,#7968f5,#5a9ce8)!important;color:white!important;border:0!important;}}
    div[data-testid='stMetric']{{background:rgba(127,127,127,.07);border:1px solid var(--tm-line);padding:10px 12px;border-radius:12px;}}
    .tm-side-label{{font-size:.72rem;text-transform:uppercase;letter-spacing:.12em;font-weight:800;color:var(--tm-muted);margin:12px 0 5px;}}
    .tm-brand{{font-family:'Manrope',sans-serif;font-weight:800;font-size:1.2rem;color:var(--tm-text);padding:8px 0 20px;}}
    .tm-brand span{{display:inline-flex;width:30px;height:30px;align-items:center;justify-content:center;border-radius:9px;background:linear-gradient(135deg,#8b7cff,#4fcac5);color:white;margin-right:8px;}}
    .tm-table-wrap{{overflow-x:auto;}} .tm-table{{width:100%;border-collapse:collapse;font-size:12px;}}
    .tm-table th,.tm-table td{{padding:9px;text-align:left;border-bottom:1px solid var(--tm-line);}}
    .tm-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px;margin:14px 0;}}
    .tm-info-card{{background:var(--tm-panel);border:1px solid var(--tm-line);border-radius:14px;padding:16px;}}
    .tm-info-card h4{{color:var(--tm-text);margin:0 0 8px;}} .tm-info-card p,.tm-info-card li{{color:var(--tm-muted);font-size:.87rem;line-height:1.5;}}
    .tm-footer{{text-align:center;color:var(--tm-muted);font-size:.8rem;padding:22px 0;border-top:1px solid var(--tm-line);margin-top:28px;}}
    </style>"""


def header_html():
    return "<div class='tm-hero'><div style='font-size:.72rem;font-weight:800;letter-spacing:.15em;color:#c5c9ff'>✦ TEXTMORPH STUDIO</div><h1>TextMorph</h1><p>AI-powered text summarization and paraphrasing workspace</p></div>"


def sidebar_brand_html():
    return "<div class='tm-brand'><span>✦</span>TEXTMORPH</div>"


def sidebar_footer_html():
    return "<div style='padding-top:20px;color:var(--tm-muted);font-size:11px;line-height:1.6'>AI writing workspace<br>Built with Python &amp; Streamlit</div>"


def footer_html():
    return "<div class='tm-footer'><b>✦ TextMorph</b><br>AI-based text summarization &amp; paraphrasing · Built with Streamlit</div>"


def empty_state_html(title, message):
    from .helpers import empty_state_html as render
    return render(title, message)
