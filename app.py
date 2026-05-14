import streamlit as st
import requests
import feedparser
from datetime import datetime, timedelta
import time
import re
import html

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Lab Literature Dashboard", 
    page_icon="🧬", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- ADVANCED UI/UX & BALANCED PASTEL GLASSMORPHISM CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Harmonic Pastel Background for the App */
    @keyframes mesh {
        0% { background-position: 0% 0%; }
        50% { background-position: 100% 100%; }
        100% { background-position: 0% 0%; }
    }
    .stApp {
        background-color: #F3F0F8; /* Subtle Dusty Lavender Base */
        background-image: 
            radial-gradient(at 15% 25%, rgba(216, 180, 254, 0.25) 0px, transparent 60%), /* Richer Lavender */
            radial-gradient(at 85% 15%, rgba(249, 168, 212, 0.25) 0px, transparent 60%), /* Richer Pink */
            radial-gradient(at 35% 85%, rgba(196, 181, 253, 0.2) 0px, transparent 60%), /* Deep Periwinkle */
            radial-gradient(at 85% 85%, rgba(253, 226, 243, 0.25) 0px, transparent 60%); /* Soft Rose */
        background-size: 200% 200%;
        animation: mesh 25s ease infinite;
        background-attachment: fixed;
    }
    
    /* --- THE ELEVATED PASTEL GLASSMORPHISM HERO BANNER --- */
    
    @keyframes floatOrb1 {
        0% { transform: translate(0, 0) scale(1); }
        33% { transform: translate(40px, -40px) scale(1.05); }
        66% { transform: translate(-30px, 30px) scale(0.95); }
        100% { transform: translate(0, 0) scale(1); }
    }
    @keyframes floatOrb2 {
        0% { transform: translate(0, 0) scale(1); }
        33% { transform: translate(-50px, 40px) scale(1.1); }
        66% { transform: translate(30px, -30px) scale(0.9); }
        100% { transform: translate(0, 0) scale(1); }
    }
    @keyframes borderGlow {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes floatCard {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }
    @keyframes pulseGlow {
        0% { box-shadow: 0 0 15px rgba(216, 180, 254, 0.2); }
        50% { box-shadow: 0 0 25px rgba(249, 168, 212, 0.5); }
        100% { box-shadow: 0 0 15px rgba(216, 180, 254, 0.2); }
    }

    .hero-wrapper {
        position: relative;
        margin-bottom: 50px;
        border-radius: 26px;
        padding: 2px; /* The extreme glass edge */
        background: linear-gradient(90deg, #F9A8D4, #D8B4FE, #FBCFE8, #C4B5FD);
        background-size: 300% 300%;
        animation: borderGlow 6s ease infinite, floatCard 8s ease-in-out infinite;
        box-shadow: 0 25px 60px -10px rgba(196, 181, 253, 0.35), 0 10px 20px -5px rgba(249, 168, 212, 0.25);
        overflow: hidden;
    }

    /* Pastel glowing orbs behind the extreme glass */
    .hero-wrapper::before, .hero-wrapper::after {
        content: '';
        position: absolute;
        filter: blur(75px);
        z-index: 1;
        opacity: 0.95;
    }
    .hero-wrapper::before {
        width: 500px; height: 500px;
        background: #F9A8D4; /* Cotton Candy Pink */
        top: -150px; left: -100px;
        animation: floatOrb1 14s infinite ease-in-out;
    }
    .hero-wrapper::after {
        width: 600px; height: 600px;
        background: #C4B5FD; /* Bright Periwinkle/Lavender */
        bottom: -200px; right: -150px;
        animation: floatOrb2 16s infinite ease-in-out;
    }
    /* Inner orb for soft pastel mixing */
    .hero-inner-orb {
        position: absolute;
        width: 450px; height: 450px;
        background: #FDF2F8; /* Pale Pink White */
        top: 5%; left: 30%;
        filter: blur(65px);
        z-index: 1;
        animation: floatOrb1 22s infinite ease-in-out reverse;
    }

    /* The actual EXTREME FROSTED GLASS card */
    .hero-banner {
        position: relative;
        /* Balanced translucent base for natural refraction */
        background: rgba(255, 255, 255, 0.15); 
        backdrop-filter: blur(45px) saturate(180%);
        -webkit-backdrop-filter: blur(45px) saturate(180%);
        padding: 70px 40px;
        border-radius: 24px;
        text-align: center;
        z-index: 2;
        border: 1px solid rgba(255, 255, 255, 0.4);
        box-shadow: inset 0 2px 5px rgba(255,255,255,0.5), inset 0 -2px 5px rgba(216,180,254,0.1);
    }
    
    .hero-title {
        font-size: 3.3rem;
        font-weight: 800;
        margin-bottom: 12px;
        letter-spacing: -0.04em;
        color: #2D3748; /* Deep Amethyst Slate - perfectly legible, less harsh than pure black */
        text-shadow: 0 2px 10px rgba(255,255,255,0.9), 0 0 30px rgba(255, 255, 255, 0.5);
    }
    .hero-subtitle {
        font-size: 1.25rem;
        font-weight: 500;
        color: #4A5568;
        max-width: 750px;
        margin: 0 auto;
        line-height: 1.6;
    }
    
    /* Elegant "Made by" Badge - Ambient Pulse */
    .creator-badge {
        display: inline-block;
        margin-top: 30px;
        padding: 8px 24px;
        background: rgba(255, 255, 255, 0.5);
        border: 1px solid rgba(216, 180, 254, 0.6);
        border-radius: 30px;
        font-size: 0.95rem;
        color: #4A5568;
        font-weight: 500;
        letter-spacing: 0.5px;
        animation: pulseGlow 4s infinite alternate;
        backdrop-filter: blur(10px);
    }
    .creator-badge span {
        color: #9F7AEA; /* Deep Lavender Accent */
        font-weight: 800;
    }

    /* Center Tabs & Styling */
    div[data-baseweb="tab-list"] {
        justify-content: center !important;
        gap: 15px;
        flex-wrap: wrap;
    }
    div[data-baseweb="tab"] {
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        padding-bottom: 15px !important;
        color: #718096 !important;
    }
    div[data-baseweb="tab"][aria-selected="true"] {
        color: #2D3748 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- UTILITY FUNCTIONS ---

def strip_tags(text):
    if not text: return "N/A"
    decoded = html.unescape(str(text))
    clean = re.sub(r'<[^>]+>', '', decoded)
    return html.escape(clean.strip())

def safe_text(text):
    if not text: return "N/A"
    return html.escape(str(text))

def extract_conclusion(abstract_text):
    if not abstract_text or len(abstract_text) < 50:
        return "No sufficient abstract text to extract conclusions."
    clean_text = re.sub(r'<[^>]+>', '', abstract_text)
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', clean_text) if len(s.strip()) > 10]
    return " ".join(sentences[-2:]) if len(sentences) > 3 else clean_text

def get_journal_name(paper_data):
    raw = paper_data.get('journalTitle')
    if not raw: raw = paper_data.get('journalInfo', {}).get('journal', {}).get('title')
    if not raw: raw = paper_data.get('bookOrReportDetails', {}).get('publisher')
    return raw if raw else "Unknown Publisher"

def get_card_theme(journal_name, is_preprint):
    j_lower = journal_name.lower()
    if is_preprint or "rxiv" in j_lower:
        return {"bg": "rgba(255, 251, 235, 0.65)", "solid": "#D97706", "text": "#92400E", "label": "PREPRINT"}
    elif "nature" in j_lower:
        return {"bg": "rgba(236, 253, 245, 0.65)", "solid": "#059669", "text": "#064E3B", "label": "NATURE PORTFOLIO"}
    elif "cell" in j_lower:
        return {"bg": "rgba(254, 242, 242, 0.65)", "solid": "#DC2626", "text": "#7F1D1D", "label": "CELL PRESS"}
    elif "science" in j_lower:
        return {"bg": "rgba(240, 249, 255, 0.65)", "solid": "#0284C7", "text": "#0C4A6E", "label": "SCIENCE MAG"}
    elif "new england" in j_lower or "nejm" in j_lower:
        return {"bg": "rgba(238, 242, 255, 0.65)", "solid": "#4F46E5", "text": "#312E81", "label": "CLINICAL"}
    else:
        return {"bg": "rgba(255, 255, 255, 0.8)", "solid": "#64748B", "text": "#1E293B", "label": "PEER-REVIEWED"}

# --- ROBUST DATA FETCHING ---

@st.cache_data(ttl=43200, show_spinner=False)
def fetch_papers(topic_query, days_back=30, oa_only=False):
    date_from = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    date_to = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
    
    oa_flag = " AND (OPEN_ACCESS:y)" if oa_only else ""
    full_query = f'({topic_query}){oa_flag} AND FIRST_PDATE:[{date_from} TO {date_to}] sort_date:y'
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    
    params = {'query': full_query, 'format': 'json', 'resultType': 'core', 'pageSize': 150}
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        papers = response.json().get('resultList', {}).get('result', [])
        return sorted(papers, key=lambda x: x.get('firstPublicationDate', '1900-01-01'), reverse=True)
    except requests.exceptions.RequestException as e:
        st.error(f"API Connection Error: {e}")
        return []

@st.cache_data(ttl=43200, show_spinner=False)
def fetch_news():
    feeds = {
        "Fierce Biotech": "https://www.fiercebiotech.com/rss/xml",
        "Endpoints News": "https://endpts.com/feed/"
    }
    news_items = []
    for source, url in feeds.items():
        try:
            parsed = feedparser.parse(url)
            for entry in parsed.entries[:8]:
                dt = datetime.now()
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try: dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                    except: pass 
                news_items.append({
                    'source': source,
                    'title': strip_tags(entry.get('title', 'Untitled')),
                    'link': entry.get('link', '#'),
                    'published_str': dt.strftime('%b %d, %Y'),
                    'date_obj': dt
                })
        except: pass 
    return sorted(news_items, key=lambda x: x['date_obj'], reverse=True)

# --- EXPANDED HIGHLY TARGETED QUERIES ---
queries = {
    "SynBio": '("synthetic biology" OR "synthetic gene circuit" OR "genetic circuit" OR "synthetic genome")',
    "Logic": '("AND gate" OR "NOT gate" OR "OR gate" OR "boolean logic" OR "logic gate") AND ("synthetic biology" OR "cell" OR "gene" OR "cancer")',
    "AAV": '("AAV" OR "adeno-associated virus" OR "AAV capsid" OR "AAV engineering" OR "directed evolution AAV")',
    "CMC": '("AAV" OR "lentivirus" OR "viral vector") AND ("CMC" OR "manufacturing" OR "bioprocessing" OR "GMP" OR "scale-up" OR "downstream processing" OR "bioreactor")',
    "NonViral": '("LNP" OR "lipid nanoparticle" OR "polymeric nanoparticle" OR "non-viral delivery" OR "exosome" OR "liposome" OR "cell-penetrating peptide" OR "VLP" OR "virus-like particle" OR "gold nanoparticle" OR "polyplex")',
    "ViralBroad": '("viral vector" OR "lentivirus" OR "adenovirus" OR "retrovirus" OR "baculovirus")',
    "HCC": '("hepatocellular carcinoma" OR "HCC") AND ("immunotherapy" OR "CAR-T" OR "immune checkpoint" OR "T-cell therapy")'
}

# --- DYNAMIC HERO UI INJECTION (ANIMATED PASTEL GLASS) ---
st.markdown("""
<div class="hero-wrapper">
    <div class="hero-inner-orb"></div>
    <div class="hero-banner">
        <div class="hero-title">Lab Literature Dashboard</div>
        <div class="hero-subtitle">Real-time curation of relevant publications, preprints, and industry news.</div>
        <div class="creator-badge">made by <span>Dylan</span></div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.markdown("### ⚙️ Engine Parameters")
    
    literature_filter = st.radio("Source Filter:", ["All", "Peer-Reviewed Only", "Preprints Only"])
    
    st.markdown("#### Open Access")
    open_access_only = st.checkbox("🔓 Show Open Access Only", value=False, help="Only return papers with freely available full text.")
    
    st.markdown("#### Journal Isolation")
    selected_journals = st.multiselect(
        "Isolate target publications:",
        ["Nature", "Cell", "Science", "New England Journal of Medicine", 
         "Nature Biotechnology", "Nature Medicine", "Hepatology", 
         "ACS Synthetic Biology", "bioRxiv", "medRxiv"],
        default=[]
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    days_to_fetch = st.slider("Timeframe (Days)", min_value=1, max_value=30, value=7, step=1) 
    
    st.markdown("---")
    if st.button("🔄 Force Data Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# --- RENDERING LOGIC ---
def render_papers(all_papers, lit_type, target_journals):
    filtered_papers = []
    
    for p in all_papers:
        raw_journal = get_journal_name(p)
        j_lower = raw_journal.lower()
        is_preprint = p.get('pubType', '') == 'preprint' or p.get('source') == 'PPR' or "rxiv" in j_lower
        
        if lit_type == "Peer-Reviewed Only" and is_preprint: continue
        if lit_type == "Preprints Only" and not is_preprint: continue
        if target_journals:
            if not any(target.lower() in j_lower for target in target_journals): continue
            
        filtered_papers.append(p)

    if not filtered_papers:
        st.warning("No publications met the criteria. Try broadening your timeframe or clearing filters.")
        return

    for p in filtered_papers:
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
        is_oa = p.get('isOpenAccess', 'N') == 'Y'
        
        link = f"https://doi.org/{doi}" if doi else f"https://europepmc.org/article/MED/{pmid}" if pmid else "#"
        clean_abstract = safe_text(re.sub(r'<[^>]+>', '', raw_abstract))
        conclusion = safe_text(extract_conclusion(raw_abstract))

        badges_html = f"""<span style="background-color: {theme['solid']}; color: white; padding: 4px 12px; border-radius: 6px; font-weight: 800; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px; margin-right: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">{raw_journal}</span>"""
        if is_oa:
            badges_html += f"""<span style="background-color: #DEF7EC; color: #03543F; border: 1px solid #31C48D; padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 0.75rem; margin-right: 10px;">🔓 Open Access</span>"""

        html_card = f"""
        <div style="background: {theme['bg']}; backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,1); border-left: 8px solid {theme['solid']}; border-radius: 12px; padding: 25px; margin-bottom: 25px; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.04), 0 8px 10px -6px rgba(0, 0, 0, 0.02);">
            <div style="display: flex; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
                {badges_html}
            </div>
            <a href="{link}" target="_blank" style="font-size: 1.3rem; font-weight: 800; color: #1E293B; text-decoration: none; display: block; margin-bottom: 10px; line-height: 1.4;">
                {title}
            </a>
            <div style="font-size: 0.95rem; color: #4A5568; margin-bottom: 18px;">
                <strong>{date}</strong> &nbsp;|&nbsp; 📊 Citations: {citations} &nbsp;|&nbsp; <i>{authors}</i>
            </div>
            <details style="cursor: pointer; outline: none; background: rgba(255,255,255,0.95); padding: 12px 15px; border-radius: 8px; border: 1px solid rgba(0,0,0,0.06); box-shadow: inset 0 2px 4px rgba(0,0,0,0.01);">
                <summary style="font-size: 0.95rem; font-weight: 700; color: {theme['solid']}; user-select: none;">
                    ▶ View Abstract & Extracted Conclusion
                </summary>
                <div style="margin-top: 15px; font-size: 0.95rem; color: #4A5568; line-height: 1.7; padding-top: 15px; border-top: 1px solid rgba(0,0,0,0.06);">
                    <p style="margin-bottom: 15px;">{clean_abstract}</p>
                    <div style="background: {theme['bg']}; border-left: 4px solid {theme['solid']}; padding: 15px; border-radius: 0 8px 8px 0; border: 1px solid rgba(0,0,0,0.05); border-left-width: 4px;">
                        <strong style="color: {theme['text']}; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; display: block;">Extracted Conclusion</strong>
                        {conclusion}
                    </div>
                </div>
            </details>
        </div>
        """
        st.markdown(html_card.replace('\n', ''), unsafe_allow_html=True)

# --- EXPANDED TABBED NAVIGATION ---
tabs = st.tabs([
    "🧬 Synthetic Biology", 
    "🧮 Logic Circuits", 
    "🦠 AAV Engineering", 
    "🏭 CMC & Manufacturing", 
    "💉 Non-Viral Delivery", 
    "🔬 Viral Delivery", 
    "🎯 HCC", 
    "📈 Industry News"
])

tab_mapping = [
    (tabs[0], queries["SynBio"]),
    (tabs[1], queries["Logic"]),
    (tabs[2], queries["AAV"]),
    (tabs[3], queries["CMC"]),
    (tabs[4], queries["NonViral"]),
    (tabs[5], queries["ViralBroad"]),
    (tabs[6], queries["HCC"])
]

for tab, query in tab_mapping:
    with tab:
        with st.spinner('Querying EuropePMC...'):
            render_papers(fetch_papers(query, days_to_fetch, open_access_only), literature_filter, selected_journals)

with tabs[7]:
    with st.spinner('Aggregating RSS Feeds...'):
        news = fetch_news()
        if not news:
            st.info("No industry news available at this time.")
        else:
            for item in news:
                t = safe_text(item['title'])
                s = safe_text(item['source'])
                d = safe_text(item['published_str'])
                l = item['link']
                
                news_card = f"""
                <div style="background: rgba(255,255,255,0.85); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,1); border-left: 6px solid #D8B4FE; border-radius: 12px; padding: 20px; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);">
                    <div style="font-size: 0.8rem; font-weight: 800; color: #D8B4FE; text-transform: uppercase; margin-bottom: 8px; letter-spacing: 0.5px;">INDUSTRY NEWS • {s}</div>
                    <a href="{l}" target="_blank" style="font-size: 1.25rem; font-weight: 700; color: #1E293B; text-decoration: none; display: block; margin-bottom: 8px; line-height: 1.4;">{t}</a>
                    <div style="font-size: 0.9rem; color: #718096; font-weight: 500;">Published: {d}</div>
                </div>
                """
                st.markdown(news_card.replace('\n', ''), unsafe_allow_html=True)
