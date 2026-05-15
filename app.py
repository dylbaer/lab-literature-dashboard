import streamlit as st
import requests
import feedparser
from datetime import datetime, timedelta
import time
import re
import html

# --- PAGE CONFIGURATION & STATE INIT ---
st.set_page_config(
    page_title="Lab Intelligence Terminal", 
    page_icon="🧬", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

if 'saved_items' not in st.session_state:
    st.session_state['saved_items'] = []

def save_item(title, link, item_type, date_str):
    item = {"title": title, "link": link, "type": item_type, "date": date_str}
    if item not in st.session_state['saved_items']:
        st.session_state['saved_items'].append(item)
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
        text-shadow: 0 2px 10px rgba(255,255,255,0.9);
    }
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
    
    /* Native Button Styling for "Star" */
    div.stButton > button {
        background: rgba(255,255,255,0.7); border: 1px solid rgba(216, 180, 254, 0.5); border-radius: 8px;
        color: #6B46C1; font-weight: 600; padding: 4px 15px; transition: all 0.2s;
    }
    div.stButton > button:hover { background: #FAF5FF; border-color: #9F7AEA; transform: translateY(-2px); box-shadow: 0 4px 6px rgba(159, 122, 234, 0.2); }
    
    /* 24h Summary Metric Cards */
    .metric-card {
        background: rgba(255,255,255,0.8); border: 1px solid rgba(255,255,255,1); border-left: 5px solid #D8B4FE;
        border-radius: 12px; padding: 15px; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.03); margin-bottom: 15px;
    }
    .metric-title { font-size: 0.85rem; font-weight: 700; color: #718096; text-transform: uppercase; }
    .metric-value { font-size: 2rem; font-weight: 800; color: #2D3748; margin-top: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- UTILITY FUNCTIONS ---

def strip_tags(text):
    if not text: return "N/A"
    clean = re.sub(r'<[^>]+>', '', html.unescape(str(text)))
    return html.escape(clean.strip())

def safe_text(text): return html.escape(str(text)) if text else "N/A"

def extract_conclusion(abstract_text):
    if not abstract_text or len(abstract_text) < 50: return "No sufficient abstract text."
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
            for entry in parsed.entries[:10]:
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

@st.cache_data(ttl=43200, show_spinner=False)
def fetch_clinical_trials(query_term):
    url = "https://clinicaltrials.gov/api/v2/studies"
    params = {"query.term": query_term, "pageSize": 20, "format": "json"}
    trials = []
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        studies = response.json().get('studies', [])
        for s in studies:
            protocol = s.get('protocolSection', {})
            id_mod = protocol.get('identificationModule', {})
            stat_mod = protocol.get('statusModule', {})
            sponsor_mod = protocol.get('sponsorCollaboratorsModule', {})
            design_mod = protocol.get('designModule', {})
            
            trials.append({
                'id': id_mod.get('nctId', 'Unknown'),
                'title': id_mod.get('briefTitle', 'Untitled Trial'),
                'status': stat_mod.get('overallStatus', 'Unknown Status'),
                'phases': ", ".join(design_mod.get('phases', ['Phase Unknown'])),
                'sponsor': sponsor_mod.get('leadSponsor', {}).get('name', 'Unknown Sponsor'),
                'date': stat_mod.get('statusDate', 'Recent')
            })
    except Exception as e: pass
    return trials

# --- EXHAUSTIVE TARGETED QUERIES ---
queries = {
    "SynBio": '("synthetic biology" OR "synthetic genome")',
    "Logic": '("synthetic gene circuit" OR "genetic circuit" OR "AND gate" OR "NOT gate" OR "OR gate" OR "boolean logic" OR "logic gate" OR "multi-input") AND ("gene therapy" OR "AAV" OR "cancer" OR "cell therapy" OR "HCC" OR "CRC")',
    "AAV": '("AAV" OR "adeno-associated virus" OR "AAV capsid" OR "directed evolution AAV")',
    "CMC": '("AAV" OR "lentivirus" OR "viral vector") AND ("CMC" OR "manufacturing" OR "bioprocessing" OR "GMP" OR "scale-up" OR "downstream processing" OR "bioreactor")',
    "NonViral": '("LNP" OR "lipid nanoparticle" OR "polymeric nanoparticle" OR "non-viral delivery" OR "liposome" OR "VLP" OR "polyplex")',
    "ViralBroad": '("viral vector" OR "lentivirus" OR "adenovirus" OR "retrovirus" OR "baculovirus")',
    "HCC_CRC": '("hepatocellular carcinoma" OR "HCC" OR "colorectal cancer" OR "CRC") AND ("immunotherapy" OR "CAR-T" OR "gene therapy")',
    "Competitors": '("Strand Therapeutics" OR "Senti Biosciences" OR "Trogenix" OR "Sirin" OR "Link Cell Therapies")'
}

general_news_feeds = { "Fierce Biotech": "https://www.fiercebiotech.com/rss/xml", "Endpoints News": "https://endpts.com/feed/" }
vc_funding_feeds = { "Gene & Cell Therapy VC Deals": "https://news.google.com/rss/search?q=(%22Series+A%22+OR+%22Series+B%22+OR+%22seed+funding%22+OR+%22venture+capital%22+OR+%22raised%22)+AND+(%22gene+therapy%22+OR+%22cell+therapy%22+OR+%22synthetic+biology%22)&hl=en-US&gl=US&ceid=US:en" }
competitor_news_feeds = { "Competitor Radar": "https://news.google.com/rss/search?q=(%22Strand+Therapeutics%22+OR+%22Senti+Biosciences%22+OR+%22Trogenix%22+OR+%22Link+Cell+Therapies%22)&hl=en-US&gl=US&ceid=US:en" }

# --- DYNAMIC HERO UI INJECTION ---
st.markdown("""
<div class="hero-wrapper">
    <div class="hero-banner">
        <div class="hero-title">Lab Intelligence Terminal</div>
        <div class="hero-subtitle">Real-time curation of literature, clinical trials, competitive intelligence, and industry finance.</div>
        <div class="creator-badge">made by <span>Dylan</span></div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- HIERARCHICAL SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("### 🧭 Main Navigation")
    current_view = st.radio("Select View:", [
        "🚀 24h Briefing", 
        "📚 Literature Database", 
        "🏥 Clinical Trials", 
        "💰 VC Finance", 
        "🤺 Competitor Matrix", 
        "⭐ Saved"
    ], label_visibility="collapsed")
    
    st.markdown("---")
    st.markdown("### ⚙️ Engine Parameters")
    days_to_fetch = st.slider("Lookback Window (Days)", min_value=1, max_value=30, value=7, step=1) 
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
    """Added context parameter to ensure Streamlit Button Keys are 100% unique across tabs."""
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
    
    # Create an absolutely unique key using context + alphanumeric title hash
    safe_title_hash = re.sub(r'[^a-zA-Z0-9]', '', title)[:20]
    uid = f"{context}_{doi if doi else pmid}_{safe_title_hash}"

    html_card = f"""
    <div style="background: {theme['bg']}; backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,1); border-left: 6px solid {theme['solid']}; border-radius: 12px; padding: 20px; margin-bottom: 5px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);">
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
    
    col1, col2 = st.columns([8.5, 1.5])
    with col2:
        if st.button("⭐ Save", key=f"save_p_{uid}"):
            save_item(title, link, "Paper", date)
    st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

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

# --- VIEW ROUTING ---

if current_view == "🚀 24h Briefing":
    st.markdown("### ⚡ Executive Summary: Last 48 Hours")
    st.write("A culmination of the most relevant intel posted recently across all lab focus areas.")
    
    cutoff_date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
    
    with st.spinner("Compiling Intelligence..."):
        # Fetch data for briefing
        syn_papers = [p for p in fetch_papers(queries["SynBio"], days_to_fetch, open_access_only) if p.get('firstPublicationDate', '') >= cutoff_date]
        circuits_papers = [p for p in fetch_papers(queries["Logic"], days_to_fetch, open_access_only) if p.get('firstPublicationDate', '') >= cutoff_date]
        aav_papers = [p for p in fetch_papers(queries["AAV"], days_to_fetch, open_access_only) if p.get('firstPublicationDate', '') >= cutoff_date]
        trials = [t for t in fetch_clinical_trials("Hepatocellular Carcinoma OR AAV OR Gene Therapy") if t.get('date', '') >= cutoff_date]
        fin_news = [n for n in fetch_news(vc_funding_feeds) if n['published_str'] >= cutoff_date]
    
    # Render Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='metric-card'><div class='metric-title'>SynBio & Circuits</div><div class='metric-value'>{len(syn_papers) + len(circuits_papers)}</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'><div class='metric-title'>AAV & Delivery</div><div class='metric-value'>{len(aav_papers)}</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card' style='border-left-color: #059669;'><div class='metric-title'>Clinical Trials</div><div class='metric-value'>{len(trials)}</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='metric-card' style='border-left-color: #10B981;'><div class='metric-title'>VC & Finance</div><div class='metric-value'>{len(fin_news)}</div></div>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("#### 🏆 Top Highlights")
    
    if (len(syn_papers) + len(circuits_papers) + len(aav_papers) + len(trials) + len(fin_news)) == 0:
        st.info("No significant updates in the last 48 hours. Enjoy your coffee! ☕")
    else:
        if circuits_papers or syn_papers:
            with st.expander("🔬 Top Synthetic Biology & Circuits Highlight", expanded=True):
                top_p = circuits_papers[0] if circuits_papers else syn_papers[0]
                render_paper_card(top_p, context="briefing_syn")
        if aav_papers:
            with st.expander("🦠 Top AAV & Delivery Highlight", expanded=True):
                render_paper_card(aav_papers[0], context="briefing_aav")
        if trials:
            with st.expander("🏥 Latest Clinical Trial Update", expanded=True):
                t = trials[0]
                st.markdown(f"**[{t['title']}](https://clinicaltrials.gov/study/{t['id']})**<br>Status: {t['status']} | Sponsor: {t['sponsor']}", unsafe_allow_html=True)
        if fin_news:
            with st.expander("💰 Latest Industry Funding", expanded=True):
                n = fin_news[0]
                st.markdown(f"**[{n['title']}]({n['link']})**<br>Published: {n['published_str']}", unsafe_allow_html=True)

elif current_view == "📚 Literature Database":
    st.markdown("### 📚 Literature Database")
    
    lit_tabs = st.tabs(["Synthetic Biology", "Genetic Circuits", "AAV Engineering", "CMC & Mfg", "Non-Viral Delivery", "Viral Delivery", "HCC & CRC"])
    
    tab_mapping = [
        (lit_tabs[0], queries["SynBio"], "synbio"),
        (lit_tabs[1], queries["Logic"], "logic"),
        (lit_tabs[2], queries["AAV"], "aav"),
        (lit_tabs[3], queries["CMC"], "cmc"),
        (lit_tabs[4], queries["NonViral"], "nonviral"),
        (lit_tabs[5], queries["ViralBroad"], "viral"),
        (lit_tabs[6], queries["HCC_CRC"], "hcc")
    ]
    
    for tab, query, context_id in tab_mapping:
        with tab:
            with st.spinner('Querying EuropePMC...'):
                raw_papers = fetch_papers(query, days_to_fetch, open_access_only)
                filtered_papers = filter_papers_by_ui(raw_papers)
                if not filtered_papers:
                    st.info("No publications met the criteria.")
                else:
                    for p in filtered_papers[:30]:
                        render_paper_card(p, context=context_id)

elif current_view == "🏥 Clinical Trials":
    st.markdown("### 🏥 Clinical Trial Tracker")
    st.caption("Monitoring ClinicalTrials.gov for 'HCC', 'CRC', 'AAV', and 'Gene Therapy'")
    with st.spinner("Fetching Trials..."):
        trials = fetch_clinical_trials("Hepatocellular Carcinoma OR Colorectal Cancer OR AAV OR Gene Therapy")
        if not trials: st.info("No recent trials fetched.")
        for t in trials[:15]:
            status_color = "#059669" if "RECRUITING" in t['status'].upper() else "#D97706" if "ACTIVE" in t['status'].upper() else "#475569"
            link = f"https://clinicaltrials.gov/study/{t['id']}"
            html_card = f"""
            <div style="background: rgba(255,255,255,0.8); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,1); border-left: 6px solid {status_color}; border-radius: 12px; padding: 20px; margin-bottom: 5px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);">
                <div style="font-size: 0.75rem; font-weight: 800; color: {status_color}; text-transform: uppercase; margin-bottom: 8px;">{t['status']} • {t['phases']}</div>
                <a href="{link}" target="_blank" style="font-size: 1.2rem; font-weight: 700; color: #1E293B; text-decoration: none; display: block; margin-bottom: 8px; line-height: 1.3;">{t['title']}</a>
                <div style="font-size: 0.9rem; color: #4A5568;"><strong>Sponsor:</strong> {t['sponsor']} &nbsp;|&nbsp; Updated: {t['date']}</div>
            </div>
            """
            st.markdown(html_card.replace('\n', ''), unsafe_allow_html=True)
            col1, col2 = st.columns([8.5, 1.5])
            with col2:
                if st.button("⭐ Save", key=f"save_t_{t['id']}"): save_item(t['title'], link, "Trial", t['date'])
            st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

elif current_view == "💰 VC Finance":
    st.markdown("### 💰 Financial Intelligence (VC & Industry Raises)")
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
            col1, col2 = st.columns([8.5, 1.5])
            with col2:
                # Use hash for unique button ID in news
                safe_hash = re.sub(r'[^a-zA-Z0-9]', '', item['title'])[:15]
                if st.button("⭐ Save", key=f"save_n_{safe_hash}"): save_item(item['title'], item['link'], "Finance", item['published_str'])
            st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

elif current_view == "🤺 Competitor Matrix":
    st.markdown("### 🤺 Competitor Entity Matrix")
    st.caption("Tracking: Strand Therapeutics, Senti Biosciences, Trogenix, Sirin, Link Cell Therapies")
    
    comp_col1, comp_col2 = st.columns(2)
    with comp_col1:
        st.markdown("#### 📰 Recent Corporate News")
        comp_news = fetch_news(competitor_news_feeds)
        if not comp_news: st.info("No recent news for targeted competitors.")
        for item in comp_news[:8]:
            st.markdown(f"**[{item['title']}]({item['link']})**<br><span style='color:gray; font-size:0.85rem;'>{item['published_str']}</span>", unsafe_allow_html=True)
            st.divider()
            
    with comp_col2:
        st.markdown("#### 🔬 Recent Publications")
        comp_papers = filter_papers_by_ui(fetch_papers(queries["Competitors"], days_back=90))
        if not comp_papers: st.info("No recent papers from targeted competitors.")
        for p in comp_papers[:8]:
            render_paper_card(p, context="comp")

elif current_view == "⭐ Saved":
    st.markdown("### ⭐ Your Saved Reading List")
    st.write("Items saved during this session.")
    
    if not st.session_state['saved_items']:
        st.info("You haven't saved any items yet. Click the ⭐ Save button on any card to build your reading list.")
    else:
        if st.button("🗑️ Clear Saved Items"):
            st.session_state['saved_items'] = []
            st.rerun()
            
        for idx, item in enumerate(reversed(st.session_state['saved_items'])):
            color = "#0284C7" if item['type'] == 'Paper' else "#059669" if item['type'] == 'Trial' else "#D97706"
            html_card = f"""
            <div style="background: rgba(255,255,255,0.9); border: 1px solid rgba(0,0,0,0.1); border-left: 6px solid {color}; border-radius: 8px; padding: 15px; margin-bottom: 10px;">
                <div style="font-size: 0.75rem; font-weight: 800; color: {color}; text-transform: uppercase; margin-bottom: 5px;">{item['type']}</div>
                <a href="{item['link']}" target="_blank" style="font-size: 1.1rem; font-weight: 600; color: #1E293B; text-decoration: none;">{item['title']}</a>
                <div style="font-size: 0.85rem; color: #64748B; margin-top: 5px;">{item['date']}</div>
            </div>
            """
            st.markdown(html_card.replace('\n', ''), unsafe_allow_html=True)
