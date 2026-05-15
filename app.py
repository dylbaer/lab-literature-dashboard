import streamlit as st
import requests
import feedparser
from datetime import datetime, timedelta
import time
import re
import html
import pandas as pd

# --- PAGE CONFIGURATION & STATE INIT ---
st.set_page_config(
    page_title="Lab Intelligence Terminal", 
    page_icon="🧬", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

if 'current_view' not in st.session_state:
    st.session_state.current_view = "🏠 Home"
if 'saved_items' not in st.session_state:
    st.session_state.saved_items = []

def change_view(view_name):
    st.session_state.current_view = view_name

def save_item(title, link, item_type, date_str):
    item = {"title": title, "link": link, "type": item_type, "date": date_str}
    if item not in st.session_state.saved_items:
        st.session_state.saved_items.append(item)
        st.toast(f"Saved: {title[:40]}...", icon="⭐")

# --- ADVANCED UI/UX & BALANCED PASTEL GLASSMORPHISM CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    @keyframes mesh {
        0% { background-position: 0% 0%; }
        50% { background-position: 100% 100%; }
        100% { background-position: 0% 0%; }
    }
    .stApp {
        background-color: #F3F0F8; 
        background-image: 
            radial-gradient(at 15% 25%, rgba(216, 180, 254, 0.25) 0px, transparent 60%),
            radial-gradient(at 85% 15%, rgba(249, 168, 212, 0.25) 0px, transparent 60%),
            radial-gradient(at 35% 85%, rgba(196, 181, 253, 0.2) 0px, transparent 60%),
            radial-gradient(at 85% 85%, rgba(253, 226, 243, 0.25) 0px, transparent 60%);
        background-size: 200% 200%;
        animation: mesh 25s ease infinite;
        background-attachment: fixed;
    }
    
    /* --- HERO BANNER --- */
    @keyframes borderGlow {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    .hero-wrapper {
        position: relative; margin-bottom: 30px; border-radius: 26px; padding: 2px;
        background: linear-gradient(90deg, #F9A8D4, #D8B4FE, #FBCFE8, #C4B5FD);
        background-size: 300% 300%; animation: borderGlow 6s ease infinite;
        box-shadow: 0 20px 50px -10px rgba(196, 181, 253, 0.35); overflow: hidden;
    }
    .hero-banner {
        position: relative; background: rgba(255, 255, 255, 0.15); 
        backdrop-filter: blur(45px) saturate(180%); -webkit-backdrop-filter: blur(45px) saturate(180%);
        padding: 50px 40px; border-radius: 24px; text-align: center; z-index: 2;
        border: 1px solid rgba(255, 255, 255, 0.4);
    }
    .hero-title {
        font-size: 3.1rem; font-weight: 800; margin-bottom: 10px; letter-spacing: -0.04em; color: #2D3748;
        text-shadow: 0 2px 10px rgba(255,255,255,0.9); transition: transform 0.2s; display: inline-block;
    }
    .hero-title:hover { transform: scale(1.01); color: #6B46C1; }
    .hero-subtitle { font-size: 1.2rem; font-weight: 500; color: #4A5568; max-width: 800px; margin: 0 auto; }
    
    .creator-badge {
        display: inline-block; margin-top: 20px; padding: 6px 20px; background: rgba(255, 255, 255, 0.5);
        border: 1px solid rgba(216, 180, 254, 0.6); border-radius: 30px; font-size: 0.9rem; color: #4A5568;
        font-weight: 500; backdrop-filter: blur(10px);
    }
    .creator-badge span { color: #9F7AEA; font-weight: 800; }

    /* Center Literature Sub-Tabs */
    div[data-baseweb="tab-list"] { justify-content: center !important; gap: 10px; flex-wrap: wrap; margin-bottom: 20px; }
    div[data-baseweb="tab"] { font-size: 1.0rem !important; font-weight: 600 !important; color: #718096 !important; }
    div[data-baseweb="tab"][aria-selected="true"] { color: #2D3748 !important; }
    
    /* Subtle Micro-Save Button */
    div[data-testid="stButton"] button {
        background: transparent !important; border: none !important; border-radius: 4px !important;
        color: #A0AEC0 !important; font-weight: 500 !important; padding: 0px 8px !important; font-size: 0.8rem !important;
        box-shadow: none !important; transition: all 0.2s; height: auto !important; min-height: 0 !important;
    }
    div[data-testid="stButton"] button:hover {
        color: #9F7AEA !important; transform: scale(1.05); background: transparent !important;
    }
    
    /* Portal Routing Buttons on Home Page */
    .portal-btn-container button {
        width: 100%; padding: 15px; border-radius: 12px; background: rgba(255,255,255,0.7);
        border: 1px solid rgba(216,180,254,0.5); font-weight: 700; color: #4A5568; transition: all 0.2s;
    }
    .portal-btn-container button:hover {
        background: white; border-color: #9F7AEA; box-shadow: 0 4px 15px rgba(216,180,254,0.3); transform: translateY(-2px);
    }

    /* 7-Day Summary Grid Cards */
    .summary-card {
        background: rgba(255,255,255,0.85); border-left: 5px solid #D8B4FE;
        padding: 25px; border-radius: 12px; color: #2D3748; height: 100%;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03); margin-bottom: 20px; display: flex; flex-direction: column;
    }
    .summary-card h4 { margin-top: 0; color: #1E293B; font-weight: 800; font-size: 1.1rem; border-bottom: 1px solid #E2E8F0; padding-bottom: 10px; margin-bottom: 15px;}
    .summary-card p { font-size: 0.95rem; line-height: 1.6; }
    .summary-card ul { padding-left: 20px; font-size: 0.9rem; color: #4A5568; flex-grow: 1; }
    .summary-card li { margin-bottom: 12px; line-height: 1.5; }
    .summary-card a { color: #9F7AEA; font-weight: 600; text-decoration: none; }
    .summary-card a:hover { text-decoration: underline; }
    
    /* Custom Pipeline Tracker & Funding Chart */
    .pipeline-grid {
        display: grid; grid-template-columns: 2.5fr 1.5fr 1.5fr 4fr; gap: 15px; align-items: center;
        background: rgba(255,255,255,0.9); padding: 15px; border-radius: 8px; margin-bottom: 10px;
        border: 1px solid rgba(0,0,0,0.05); box-shadow: 0 2px 5px rgba(0,0,0,0.02);
    }
    .pipeline-header { font-weight: 700; color: #4A5568; font-size: 0.85rem; text-transform: uppercase; border-bottom: 2px solid #E2E8F0; padding-bottom: 10px; margin-bottom: 10px;}
    .pipeline-col { font-size: 0.95rem; color: #2D3748; font-weight: 500; }
    .pipeline-subtext { font-size: 0.8rem; color: #718096; }
    
    .phase-container {
        display: grid; grid-template-columns: repeat(5, 1fr); gap: 2px;
        background: #EDF2F7; border-radius: 20px; overflow: hidden; height: 14px; position: relative;
    }
    .phase-fill {
        background: linear-gradient(90deg, #D8B4FE, #9F7AEA); height: 100%; border-radius: 20px;
        position: absolute; left: 0; top: 0; transition: width 0.5s ease;
    }
    
    /* Horizontal Funding Bar Chart */
    .funding-row { display: flex; align-items: center; margin-bottom: 12px; }
    .funding-label { width: 170px; font-weight: 600; font-size: 0.9rem; color: #4A5568; }
    .funding-bar-container { flex-grow: 1; background: #EDF2F7; border-radius: 8px; height: 18px; position: relative; margin: 0 15px; }
    .funding-bar { background: linear-gradient(90deg, #34D399, #10B981); height: 100%; border-radius: 8px; }
    .funding-value { width: 80px; text-align: right; font-weight: 700; font-size: 0.95rem; color: #1E293B; }
    </style>
""", unsafe_allow_html=True)

# --- UTILITY FUNCTIONS ---

def strip_tags(text):
    if not text: return "N/A"
    clean = re.sub(r'<[^>]+>', '', html.unescape(str(text)))
    return html.escape(clean.strip())

def safe_text(text): return html.escape(str(text)) if text else "N/A"

def extract_conclusion(abstract_text):
    if not abstract_text or len(abstract_text) < 50: return "No abstract available."
    clean_text = re.sub(r'<[^>]+>', '', abstract_text)
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', clean_text) if len(s.strip()) > 10]
    return " ".join(sentences[-2:]) if len(sentences) > 3 else clean_text

def get_journal_name(paper_data):
    raw = paper_data.get('journalTitle') or paper_data.get('journalInfo', {}).get('journal', {}).get('title') or paper_data.get('bookOrReportDetails', {}).get('publisher')
    return raw if raw else "Unknown Publisher"

def get_card_theme(journal_name, is_preprint):
    j = journal_name.lower()
    if is_preprint or "rxiv" in j: return {"bg": "rgba(255, 251, 235, 0.65)", "solid": "#D97706", "text": "#92400E", "label": "PREPRINT"}
    elif "nature" in j: return {"bg": "rgba(236, 253, 245, 0.65)", "solid": "#059669", "text": "#064E3B", "label": "NATURE"}
    elif "cell" in j: return {"bg": "rgba(254, 242, 242, 0.65)", "solid": "#DC2626", "text": "#7F1D1D", "label": "CELL PRESS"}
    elif "science" in j: return {"bg": "rgba(240, 249, 255, 0.65)", "solid": "#0284C7", "text": "#0C4A6E", "label": "SCIENCE"}
    elif "new england" in j or "nejm" in j: return {"bg": "rgba(238, 242, 255, 0.65)", "solid": "#4F46E5", "text": "#312E81", "label": "CLINICAL"}
    else: return {"bg": "rgba(255, 255, 255, 0.8)", "solid": "#64748B", "text": "#1E293B", "label": "PEER-REVIEWED"}

# --- ROBUST DATA FETCHING ---

@st.cache_data(ttl=10800, show_spinner=False)
def fetch_papers(topic_query, days_back=30, oa_only=False):
    date_from = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    date_to = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
    oa_flag = " AND (OPEN_ACCESS:y)" if oa_only else ""
    full_query = f'({topic_query}){oa_flag} AND FIRST_PDATE:[{date_from} TO {date_to}] sort_date:y'
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    try:
        response = requests.get(url, params={'query': full_query, 'format': 'json', 'resultType': 'core', 'pageSize': 150}, timeout=15)
        response.raise_for_status()
        return sorted(response.json().get('resultList', {}).get('result', []), key=lambda x: x.get('firstPublicationDate', '1900-01-01'), reverse=True)
    except: return []

@st.cache_data(ttl=10800, show_spinner=False)
def fetch_news(rss_urls):
    news_items = []
    for source, url in rss_urls.items():
        try:
            parsed = feedparser.parse(url)
            for entry in parsed.entries[:15]:
                dt = datetime.now()
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try: dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                    except: pass 
                news_items.append({
                    'source': source, 'title': strip_tags(entry.get('title', 'Untitled')),
                    'link': entry.get('link', '#'), 'published_str': dt.strftime('%Y-%m-%d'), 'date_obj': dt
                })
        except: pass 
    return sorted(news_items, key=lambda x: x['date_obj'], reverse=True)

# --- EXHAUSTIVE TARGETED QUERIES (Surgical Precision Upgrades) ---
queries = {
    "SynBio": '("synthetic biology" OR "synthetic genome" OR "programmable biology")',
    "Logic": '("synthetic gene circuit" OR "genetic circuit" OR "boolean logic gate" OR "logic-gated" OR "multi-input circuit" OR "synthetic logic") AND ("gene therapy" OR "adeno-associated virus" OR "AAV vector" OR "cancer" OR "cell therapy" OR "HCC" OR "CRC" OR "oncology")',
    "AAV": '(("adeno-associated virus" OR "AAV") AND ("capsid" OR "vector" OR "gene therapy" OR "transduction" OR "delivery")) NOT ("vasculitis" OR "ANCA" OR "sepsis" OR "macrophage" OR "pulmonary" OR "injury")',
    "CMC": '("adeno-associated virus" OR "lentivirus" OR "viral vector" OR "AAV") AND ("CMC" OR "manufacturing" OR "bioprocessing" OR "GMP" OR "scale-up" OR "downstream processing") NOT ("vasculitis" OR "ANCA")',
    "NonViral": '("LNP" OR "lipid nanoparticle" OR "polymeric nanoparticle" OR "non-viral delivery" OR "liposome" OR "VLP" OR "polyplex")',
    "ViralBroad": '("viral vector" OR "lentivirus" OR "adenovirus" OR "retrovirus" OR "baculovirus") NOT ("vasculitis" OR "ANCA")',
    "HCC": '("hepatocellular carcinoma" OR "HCC") AND ("immunotherapy" OR "gene therapy" OR "CAR-T" OR "AAV" OR "tumor") NOT ("Hepatitis C" OR "HCV")',
    "Immunotherapy": '("immunotherapy" OR "CAR-T" OR "gene therapy" OR "T-cell therapy") AND ("solid tumor" OR "oncology" OR "cancer")'
}

vc_funding_feeds = { 
    "Gene & Cell Therapy VC Deals": "https://news.google.com/rss/search?q=(%22Series+A%22+OR+%22Series+B%22+OR+%22Series+C%22+OR+%22Series+D%22+OR+%22seed+round%22+OR+%22venture+capital%22)+AND+(%22gene+therapy%22+OR+%22cell+therapy%22)&hl=en-US&gl=US&ceid=US:en" 
}
competitor_news_feeds = { 
    "Competitor Radar": "https://news.google.com/rss/search?q=(%22Strand+Therapeutics%22+OR+%22Senti+Biosciences%22+OR+%22Trogenix%22+OR+%22Siren+Biotechnology%22+OR+%22ArsenalBio%22+OR+%22Lyell+Immunopharma%22+OR+%22Obsidian+Therapeutics%22+OR+%22Outpace+Bio%22)&hl=en-US&gl=US&ceid=US:en" 
}

# --- CURATED COMPETITOR PIPELINE DATABASE ---
pipeline_data = [
    {"Company": "Lyell Immunopharma", "Asset": "LYL797", "Modality": "Reprogrammed CAR-T", "Indication": "TNBC / NSCLC", "Width": "50%"}, 
    {"Company": "Lyell Immunopharma", "Asset": "LYL119", "Modality": "Reprogrammed CAR-T", "Indication": "Solid Tumors", "Width": "50%"}, 
    {"Company": "ArsenalBio", "Asset": "AB-1015", "Modality": "Logic-Gated CAR-T", "Indication": "Ovarian Cancer", "Width": "50%"}, 
    {"Company": "ArsenalBio", "Asset": "AB-2100", "Modality": "Logic-Gated CAR-T", "Indication": "ccRCC", "Width": "50%"},
    {"Company": "Obsidian Therapeutics", "Asset": "OBX-115", "Modality": "Regulatable TIL (cytoDRiVE)", "Indication": "Melanoma", "Width": "70%"},
    {"Company": "Senti Biosciences", "Asset": "SENTI-202", "Modality": "Logic-Gated CAR-NK (OR+NOT)", "Indication": "AML", "Width": "50%"}, 
    {"Company": "Senti Biosciences", "Asset": "SENTI-301A", "Modality": "Logic-Gated CAR-NK", "Indication": "HCC", "Width": "30%"}, 
    {"Company": "Strand Therapeutics", "Asset": "STX-001", "Modality": "Programmable mRNA", "Indication": "Solid Tumors", "Width": "50%"}, 
    {"Company": "Strand Therapeutics", "Asset": "STX-003", "Modality": "Systemic Programmable mRNA", "Indication": "Solid Tumors", "Width": "40%"}, 
    {"Company": "Strand Therapeutics", "Asset": "STX-005", "Modality": "In vivo CAR-T mRNA", "Indication": "Autoimmune Cancers", "Width": "10%"}, 
    {"Company": "Siren Biotechnology", "Asset": "SRN-101", "Modality": "Universal AAV Immuno-Gene", "Indication": "High-Grade Glioma", "Width": "50%"}, 
    {"Company": "Siren Biotechnology", "Asset": "Undisclosed", "Modality": "Universal AAV Immuno-Gene", "Indication": "Solid Tumors", "Width": "25%"}, 
    {"Company": "Outpace Bio", "Asset": "OPB-101", "Modality": "Engineered Cytokine CAR-T", "Indication": "Solid Tumors", "Width": "30%"},
    {"Company": "Trogenix", "Asset": "Lead Asset", "Modality": "SSE Vector (HSV-TK/IL-12)", "Indication": "Glioblastoma", "Width": "50%"}, 
    {"Company": "Trogenix", "Asset": "Undisclosed", "Modality": "SSE Vector", "Indication": "Colorectal Cancer", "Width": "30%"}, 
    {"Company": "Trogenix", "Asset": "Undisclosed", "Modality": "SSE Vector", "Indication": "HCC", "Width": "30%"}, 
    {"Company": "Trogenix", "Asset": "Undisclosed", "Modality": "SSE Vector", "Indication": "Fibrosis", "Width": "10%"}
]

funding_data = [
    {"Company": "Lyell Immunopharma", "Amount": 425, "Percentage": "100%"},
    {"Company": "ArsenalBio", "Amount": 325, "Percentage": "76%"}, 
    {"Company": "Obsidian Therapeutics", "Amount": 275, "Percentage": "64%"},
    {"Company": "Senti Biosciences", "Amount": 205, "Percentage": "48%"},
    {"Company": "Outpace Bio", "Amount": 144, "Percentage": "34%"},
    {"Company": "Strand Therapeutics", "Amount": 97, "Percentage": "23%"},
    {"Company": "Trogenix", "Amount": 95, "Percentage": "22%"}, 
    {"Company": "Siren Biotechnology", "Amount": 20, "Percentage": "5%"} 
]

# Macro Investment Trend Data
macro_funding_data = pd.DataFrame({
    "Year": ["2020", "2021", "2022", "2023", "2024", "2025", "2026 (YTD)"],
    "Capital Deployed ($B)": [19.5, 22.8, 12.1, 9.5, 11.0, 13.2, 4.2]
}).set_index("Year")

# --- DYNAMIC HERO UI INJECTION ---
st.markdown("""
<div class="hero-wrapper">
    <div class="hero-banner">
        <a href="?" target="_self" style="text-decoration: none; color: inherit;">
            <div class="hero-title">Lab Intelligence Terminal</div>
        </a>
        <div class="hero-subtitle">Real-time curation of literature, competitive intelligence, and industry finance.</div>
        <div class="creator-badge">made by <span>Dylan</span></div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR & ROUTING INTERFACE ---
view_options = ["🏠 Home", "📚 Literature", "💰 VC Finance", "🤺 Competitor Pipeline", "⭐ Saved"]
with st.sidebar:
    st.markdown("### ⚙️ Filters & Parameters")
    selected_view = st.radio("Navigation (Internal)", view_options, index=view_options.index(st.session_state.current_view), label_visibility="collapsed")
    if selected_view != st.session_state.current_view:
        st.session_state.current_view = selected_view
        st.rerun()

    st.markdown("---")
    days_to_fetch = st.slider("Literature Lookback (Days)", min_value=1, max_value=30, value=7, step=1) 
    literature_filter = st.radio("Source Filter:", ["All", "Peer-Reviewed", "Preprints"], horizontal=True)
    open_access_only = st.checkbox("🔓 Open Access Only")
    
    st.markdown("#### Journal Isolation")
    selected_journals = st.multiselect("Isolate target publications:", ["Nature", "Cell", "Science", "New England Journal of Medicine", "Nature Biotechnology", "Nature Medicine", "Hepatology", "ACS Synthetic Biology", "bioRxiv", "medRxiv"], default=[])
    
    st.markdown("---")
    if st.button("🔄 Force Data Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# --- RENDERING LOGIC ---
def render_paper_card(p, context="global"):
    title = safe_text(p.get('title', 'Unknown Title'))
    raw_journal = safe_text(get_journal_name(p))
    is_preprint = p.get('pubType', '') == 'preprint' or p.get('source') == 'PPR' or "rxiv" in raw_journal.lower()
    theme = get_card_theme(raw_journal, is_preprint)
    date = safe_text(p.get('firstPublicationDate', 'Unknown Date'))
    authors = safe_text(p.get('authorString', 'Unknown Authors'))
    doi = p.get('doi', '')
    pmid = p.get('pmid', '')
    raw_abstract = p.get('abstractText', 'No abstract available.')
    citations = p.get('citedByCount', 0)
    
    link = f"https://doi.org/{doi}" if doi else f"https://europepmc.org/article/MED/{pmid}" if pmid else "#"
    clean_abstract = safe_text(re.sub(r'<[^>]+>', '', raw_abstract))
    conclusion = safe_text(extract_conclusion(raw_abstract))
    
    safe_title_hash = re.sub(r'[^a-zA-Z0-9]', '', title)[:20]
    uid = f"{context}_{doi if doi else pmid}_{safe_title_hash}"

    html_card = f"""
    <div style="background: {theme['bg']}; backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,1); border-left: 6px solid {theme['solid']}; border-radius: 12px; padding: 20px; margin-bottom: 5px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03); position: relative;">
        <div style="font-size: 0.75rem; font-weight: 800; color: {theme['solid']}; text-transform: uppercase; margin-bottom: 8px;">{raw_journal} • {theme['label']}</div>
        <a href="{link}" target="_blank" style="font-size: 1.25rem; font-weight: 700; color: #1E293B; text-decoration: none; display: block; margin-bottom: 8px; line-height: 1.3;">{title}</a>
        <div style="font-size: 0.9rem; color: #4A5568; margin-bottom: 12px;"><strong>{date}</strong> &nbsp;|&nbsp; 📊 Citations: {citations} &nbsp;|&nbsp; <i>{authors}</i></div>
        <details style="cursor: pointer; outline: none; background: rgba(255,255,255,0.7); padding: 10px; border-radius: 8px; border: 1px solid rgba(0,0,0,0.04);">
            <summary style="font-size: 0.9rem; font-weight: 700; color: {theme['solid']};">▶ View Abstract & Conclusion</summary>
            <div style="margin-top: 10px; font-size: 0.9rem; color: #4A5568; line-height: 1.6; padding-top: 10px; border-top: 1px solid rgba(0,0,0,0.06);">
                <p>{clean_abstract}</p>
                <div style="background: {theme['bg']}; border-left: 3px solid {theme['solid']}; padding: 10px; border-radius: 0 6px 6px 0;">
                    <strong style="color: {theme['text']}; font-size: 0.8rem; text-transform: uppercase;">Extracted Conclusion</strong><br>{conclusion}
                </div>
            </div>
        </details>
    </div>
    """
    st.markdown(html_card.replace('\n', ''), unsafe_allow_html=True)
    
    c1, c2 = st.columns([9.2, 0.8])
    with c2:
        if st.button("⭐ Save", key=f"save_p_{uid}"):
            save_item(title, link, "Paper", date)
    st.markdown("<div style='margin-bottom: 5px;'></div>", unsafe_allow_html=True)

def filter_papers_by_ui(all_papers):
    filtered = []
    for p in all_papers:
        raw_journal = get_journal_name(p).lower()
        is_preprint = p.get('pubType', '') == 'preprint' or p.get('source') == 'PPR' or "rxiv" in raw_journal
        if literature_filter == "Peer-Reviewed" and is_preprint: continue
        if literature_filter == "Preprints" and not is_preprint: continue
        if selected_journals and not any(t.lower() in raw_journal for t in selected_journals): continue
        filtered.append(p)
    return filtered

def build_7day_summary(topic_icon, topic_name, papers):
    if not papers: 
        return f"<div class='summary-card'><h4>{topic_icon} {topic_name}</h4><p>No new relevant publications detected in the last 7 days.</p></div>"
    
    html = f"""
    <div class='summary-card'>
        <h4>{topic_icon} {topic_name}</h4>
        <p><strong>{len(papers)} new publications</strong> were indexed this week. Key highlights include:</p>
        <ul>
    """
    
    for p in papers[:3]:
        link = f"https://doi.org/{p.get('doi')}" if p.get('doi') else f"https://europepmc.org/article/MED/{p.get('pmid')}" if p.get('pmid') else "#"
        raw_abstract = p.get('abstractText', '')
        conclusion = safe_text(extract_conclusion(raw_abstract))
        if len(conclusion) > 180: conclusion = conclusion[:177] + "..."
        
        html += f"<li><strong><a href='{link}' target='_blank'>{safe_text(p.get('title'))}</a></strong><br><em>Finding:</em> {conclusion}</li>"
        
    html += "</ul></div>"
    return html

# --- VIEW ROUTING ---

if st.session_state.current_view == "🏠 Home":
    # Quick Portal Navigation
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📚 Literature", use_container_width=True): change_view("📚 Literature"); st.rerun()
    with col2:
        if st.button("💰 VC Finance", use_container_width=True): change_view("💰 VC Finance"); st.rerun()
    with col3:
        if st.button("🤺 Competitor Pipeline", use_container_width=True): change_view("🤺 Competitor Pipeline"); st.rerun()
        
    st.markdown("<br><h3>🗓️ 7-Day Intelligence Summary</h3>", unsafe_allow_html=True)
    
    cutoff_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    with st.spinner("Synthesizing Weekly Intelligence..."):
        circuits_papers = [p for p in fetch_papers(queries["Logic"], days_back=7, oa_only=open_access_only) if p.get('firstPublicationDate', '') >= cutoff_date]
        aav_papers = [p for p in fetch_papers(queries["AAV"], days_back=7, oa_only=open_access_only) if p.get('firstPublicationDate', '') >= cutoff_date]
        hcc_papers = [p for p in fetch_papers(queries["HCC"], days_back=7, oa_only=open_access_only) if p.get('firstPublicationDate', '') >= cutoff_date]
        immuno_papers = [p for p in fetch_papers(queries["Immunotherapy"], days_back=7, oa_only=open_access_only) if p.get('firstPublicationDate', '') >= cutoff_date]

    # 2x2 Grid for 7-Day Summaries
    r1c1, r1c2 = st.columns(2)
    with r1c1: st.markdown(build_7day_summary("🧮", "Genetic Circuits", circuits_papers), unsafe_allow_html=True)
    with r1c2: st.markdown(build_7day_summary("🦠", "AAV Engineering", aav_papers), unsafe_allow_html=True)
    
    r2c1, r2c2 = st.columns(2)
    with r2c1: st.markdown(build_7day_summary("🎯", "Hepatocellular Carcinoma", hcc_papers), unsafe_allow_html=True)
    with r2c2: st.markdown(build_7day_summary("🛡️", "Immunotherapy", immuno_papers), unsafe_allow_html=True)

elif st.session_state.current_view == "📚 Literature":
    st.markdown("### 📚 Literature")
    
    lit_tabs = st.tabs(["🧬 SynBio", "🧮 Genetic Circuits", "🦠 AAV Eng", "🏭 CMC & Mfg", "💉 Non-Viral", "🔬 Viral Delivery", "🎯 HCC"])
    
    tab_mapping = [
        (lit_tabs[0], queries["SynBio"], "synbio"),
        (lit_tabs[1], queries["Logic"], "logic"),
        (lit_tabs[2], queries["AAV"], "aav"),
        (lit_tabs[3], queries["CMC"], "cmc"),
        (lit_tabs[4], queries["NonViral"], "nonviral"),
        (lit_tabs[5], queries["ViralBroad"], "viral"),
        (lit_tabs[6], queries["HCC"], "hcc")
    ]
    
    for tab, query, context_id in tab_mapping:
        with tab:
            with st.spinner('Querying Database...'):
                raw_papers = fetch_papers(query, days_to_fetch, open_access_only)
                filtered_papers = filter_papers_by_ui(raw_papers)
                if not filtered_papers:
                    st.info("No publications met the criteria.")
                else:
                    for p in filtered_papers[:30]:
                        render_paper_card(p, context=context_id)

elif st.session_state.current_view == "💰 VC Finance":
    st.markdown("### 💰 Financial Intelligence")
    st.write("Tracking Seed, Series A-D, and venture capital raises strictly in the Gene and Cell Therapy sector.")
    
    with st.spinner("Aggregating Financial News..."):
        vc_news = fetch_news(vc_funding_feeds)
        if not vc_news: st.info("No recent funding news.")
        for item in vc_news:
            html_card = f"""
            <div style="background: rgba(255,255,255,0.85); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,1); border-left: 6px solid #10B981; border-radius: 12px; padding: 20px; margin-bottom: 5px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);">
                <div style="font-size: 0.8rem; font-weight: 800; color: #10B981; text-transform: uppercase; margin-bottom: 8px;">INDUSTRY FUNDING</div>
                <a href="{item['link']}" target="_blank" style="font-size: 1.2rem; font-weight: 700; color: #0f172a; text-decoration: none; display: block; margin-bottom: 8px; line-height: 1.4;">{item['title']}</a>
                <div style="font-size: 0.9rem; color: #64748b;">Published: {item['published_str']}</div>
            </div>
            """
            st.markdown(html_card.replace('\n', ''), unsafe_allow_html=True)
            c1, c2 = st.columns([9.2, 0.8])
            with c2:
                safe_hash = re.sub(r'[^a-zA-Z0-9]', '', item['title'])[:15]
                if st.button("⭐ Save", key=f"save_n_{safe_hash}"): save_item(item['title'], item['link'], "Finance", item['published_str'])
            st.markdown("<div style='margin-bottom: 5px;'></div>", unsafe_allow_html=True)
            
    st.markdown("<br><hr style='border: 0; height: 1px; background: rgba(0,0,0,0.1); margin: 30px 0;'><br>", unsafe_allow_html=True)
    st.markdown("#### 📈 Macro Investment Trend: Gene & Cell Therapy")
    st.write("Historical and projected venture capital deployment tracking overall VC appetite in the CGT sector ($ Billions).")
    st.area_chart(macro_funding_data, color="#9F7AEA")

elif st.session_state.current_view == "🤺 Competitor Pipeline":
    st.markdown("### 🤺 Competitor Entity Pipeline")
    st.write("A curated visual representation of clinical and preclinical assets developed by rival organizations focusing on logic gating, cell therapy, and precision oncology.")
    
    st.markdown("""
        <div class='pipeline-grid pipeline-header'>
            <div>COMPANY & ASSET</div>
            <div>MODALITY</div>
            <div>INDICATION</div>
            <div>
                <span style='margin-left: 5%;'>DISC.</span> 
                <span style='margin-left: 9%;'>PRECLINICAL</span> 
                <span style='margin-left: 8%;'>PHASE 1</span> 
                <span style='margin-left: 10%;'>PHASE 2</span> 
                <span style='margin-left: 10%;'>PHASE 3</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    for row in pipeline_data:
        pipeline_html = f"""
        <div class="pipeline-grid">
            <div>
                <div class="pipeline-col" style="font-weight: 800;">{row['Company']}</div>
                <div class="pipeline-subtext" style="color: #9F7AEA; font-weight: 600;">{row['Asset']}</div>
            </div>
            <div class="pipeline-subtext">{row['Modality']}</div>
            <div class="pipeline-subtext">{row['Indication']}</div>
            <div>
                <div class="phase-container">
                    <div class="phase-fill" style="width: {row['Width']};"></div>
                </div>
            </div>
        </div>
        """
        st.markdown(pipeline_html.replace('\n', ''), unsafe_allow_html=True)
        
    st.markdown("<p style='font-size:0.8rem; color:#A0AEC0;'>* Data is manually curated based on publicly available PR and corporate website pipelines.</p><br>", unsafe_allow_html=True)
    
    st.markdown("### 💰 Disclosed Entity Funding ($M)")
    
    for f in funding_data:
        bar_html = f"""
        <div class="funding-row">
            <div class="funding-label">{f['Company']}</div>
            <div class="funding-bar-container">
                <div class="funding-bar" style="width: {f['Percentage']};"></div>
            </div>
            <div class="funding-value">${f['Amount']}M</div>
        </div>
        """
        st.markdown(bar_html, unsafe_allow_html=True)
        
    st.markdown("<h3>📰 Recent Competitor News</h3>", unsafe_allow_html=True)
    with st.spinner("Fetching Competitor News..."):
        comp_news = fetch_news(competitor_news_feeds)
        if not comp_news: st.info("No recent news for targeted competitors.")
        for item in comp_news[:5]:
            html_card = f"""
            <div style="background: rgba(255,255,255,0.85); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,1); border-left: 6px solid #9F7AEA; border-radius: 12px; padding: 20px; margin-bottom: 10px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);">
                <div style="font-size: 0.8rem; font-weight: 800; color: #9F7AEA; text-transform: uppercase; margin-bottom: 8px;">COMPETITOR RADAR • {item['source']}</div>
                <a href="{item['link']}" target="_blank" style="font-size: 1.15rem; font-weight: 700; color: #1E293B; text-decoration: none; display: block; margin-bottom: 8px; line-height: 1.4;">{item['title']}</a>
                <div style="font-size: 0.85rem; color: #64748B;">Published: {item['published_str']}</div>
            </div>
            """
            st.markdown(html_card.replace('\n', ''), unsafe_allow_html=True)

elif st.session_state.current_view == "⭐ Saved":
    st.markdown("### ⭐ Your Saved Reading List")
    st.write("Items saved during this session.")
    
    if not st.session_state.saved_items:
        st.info("You haven't saved any items yet. Click the ⭐ Save button on any card to build your reading list.")
    else:
        if st.button("🗑️ Clear Saved Items"):
            st.session_state.saved_items = []
            st.rerun()
            
        for idx, item in enumerate(reversed(st.session_state.saved_items)):
            color = "#0284C7" if item['type'] == 'Paper' else "#10B981" if item['type'] == 'Finance' else "#D97706"
            html_card = f"""
            <div style="background: rgba(255,255,255,0.9); border: 1px solid rgba(0,0,0,0.1); border-left: 6px solid {color}; border-radius: 8px; padding: 15px; margin-bottom: 10px;">
                <div style="font-size: 0.75rem; font-weight: 800; color: {color}; text-transform: uppercase; margin-bottom: 5px;">{item['type']}</div>
                <a href="{item['link']}" target="_blank" style="font-size: 1.1rem; font-weight: 600; color: #1E293B; text-decoration: none;">{item['title']}</a>
                <div style="font-size: 0.85rem; color: #64748B; margin-top: 5px;">{item['date']}</div>
            </div>
            """
            st.markdown(html_card.replace('\n', ''), unsafe_allow_html=True)
