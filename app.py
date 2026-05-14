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

# --- ADVANCED UI/UX CSS INJECTION ---
# Stripped out gimmicky animations for a highly professional, Benchling-style SaaS aesthetic.
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #F8FAFC;
    }
    
    /* Clean, Professional Hero Banner */
    .hero-banner {
        background: #0F172A; /* Deep slate */
        padding: 40px 30px;
        border-radius: 12px;
        text-align: center;
        color: white;
        margin-bottom: 40px;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.2);
        border: 1px solid #1E293B;
    }
    .hero-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 10px;
        letter-spacing: -0.02em;
    }
    .hero-subtitle {
        font-size: 1.1rem;
        font-weight: 400;
        color: #94A3B8;
    }

    /* Center Tabs */
    div[data-baseweb="tab-list"] {
        justify-content: center !important;
        gap: 30px;
    }
    div[data-baseweb="tab"] {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        padding-bottom: 15px !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- UTILITY FUNCTIONS ---

def safe_text(text):
    """Escapes text to prevent HTML injection breaks."""
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
    """Returns exact hex codes for tinted backgrounds and borders."""
    j_lower = journal_name.lower()
    if is_preprint or "rxiv" in j_lower:
        return {"bg": "#FFFBEB", "border": "#F59E0B", "text": "#B45309", "label": "PREPRINT"}
    elif "nature" in j_lower:
        return {"bg": "#ECFDF5", "border": "#10B981", "text": "#047857", "label": "NATURE PORTFOLIO"}
    elif "cell" in j_lower:
        return {"bg": "#FEF2F2", "border": "#EF4444", "text": "#B91C1C", "label": "CELL PRESS"}
    elif "science" in j_lower:
        return {"bg": "#ECFEFF", "border": "#0EA5E9", "text": "#0369A1", "label": "SCIENCE MAG"}
    elif "new england" in j_lower or "nejm" in j_lower:
        return {"bg": "#EEF2FF", "border": "#6366F1", "text": "#4338CA", "label": "CLINICAL"}
    else:
        return {"bg": "#F1F5F9", "border": "#64748B", "text": "#334155", "label": "PEER-REVIEWED"}

# --- ROBUST DATA FETCHING ---

@st.cache_data(ttl=43200, show_spinner=False)
def fetch_papers(topic_query, days_back=30):
    """Fetches a large pool of papers; filtering happens locally to prevent API drops."""
    date_from = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    date_to = datetime.now().strftime('%Y-%m-%d')
    
    full_query = f'({topic_query}) AND FIRST_PDATE:[{date_from} TO {date_to}]'
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    
    params = {
        'query': full_query,
        'format': 'json',
        'resultType': 'core',
        'pageSize': 100 # Fetch more to allow for aggressive local filtering
    }
    
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
                    try:
                        dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                    except: pass 
                news_items.append({
                    'source': source,
                    'title': entry.get('title', 'Untitled'),
                    'link': entry.get('link', '#'),
                    'published_str': dt.strftime('%b %d, %Y'),
                    'date_obj': dt
                })
        except: pass 
    return sorted(news_items, key=lambda x: x['date_obj'], reverse=True)

# --- QUERIES ---
query_circuits = '("synthetic gene circuit" OR "synthetic biology" OR "genetic circuit") AND ("AND gate" OR "NOT gate" OR "OR gate" OR "boolean logic" OR "cancer")'
query_aav = '"AAV" OR "adeno-associated virus" OR "AAV engineering" OR "AAV capsid"'
query_hcc = '"hepatocellular carcinoma" AND "immunotherapy"'

# --- HEADER UI ---
st.markdown("""
<div class="hero-banner">
    <div class="hero-title">Lab Literature Dashboard</div>
    <div class="hero-subtitle">Real-time curation of relevant publications, preprints, and industry news.</div>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.markdown("### ⚙️ Engine Parameters")
    
    literature_filter = st.radio(
        "Source Filter:",
        ["All", "Peer-Reviewed Only", "Preprints Only"],
    )
    
    st.markdown("#### Journal Isolation")
    st.caption("Leave empty to search all journals.")
    selected_journals = st.multiselect(
        "Isolate target publications:",
        ["Nature", "Cell", "Science", "New England Journal of Medicine", 
         "Nature Biotechnology", "Nature Medicine", "Hepatology", 
         "ACS Synthetic Biology", "bioRxiv", "medRxiv"],
        default=[]
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    # Increased default to 30 days. Scientific publishing is too slow for a 7 day default on niche queries.
    days_to_fetch = st.slider("Timeframe (Days)", min_value=7, max_value=90, value=30, step=7) 
    
    st.markdown("---")
    if st.button("🔄 Force Data Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# --- RENDERING LOGIC ---
def render_papers(all_papers, lit_type, target_journals):
    filtered_papers = []
    
    # Python-side filtering for bulletproof accuracy
    for p in all_papers:
        raw_journal = get_journal_name(p)
        j_lower = raw_journal.lower()
        is_preprint = p.get('pubType', '') == 'preprint' or p.get('source') == 'PPR' or "rxiv" in j_lower
        
        # 1. Type Filter
        if lit_type == "Peer-Reviewed Only" and is_preprint: continue
        if lit_type == "Preprints Only" and not is_preprint: continue
            
        # 2. Journal Filter (Substring match prevents dropping "Cell Chemical Biology" when "Cell" is selected)
        if target_journals:
            match_found = any(target.lower() in j_lower for target in target_journals)
            if not match_found: continue
            
        filtered_papers.append(p)

    if not filtered_papers:
        st.warning("No publications met the criteria. Try broadening your timeframe or clearing the journal filter.")
        return
        
    for p in filtered_papers:
        title = safe_text(p.get('title', 'Unknown Title'))
        raw_journal = safe_text(get_journal_name(p))
        is_preprint = p.get('pubType', '') == 'preprint' or p.get('source') == 'PPR' or "rxiv" in raw_journal.lower()
        
        # Get Semantic Colors
        theme = get_card_theme(raw_journal, is_preprint)
        
        date = safe_text(p.get('firstPublicationDate', 'Unknown Date'))
        authors = safe_text(p.get('authorString', 'Unknown Authors'))
        doi = p.get('doi', '')
        pmid = p.get('pmid', '')
        raw_abstract = p.get('abstractText', 'No abstract available.')
        
        link = f"https://doi.org/{doi}" if doi else f"https://europepmc.org/article/MED/{pmid}" if pmid else "#"

        clean_abstract = safe_text(re.sub(r'<[^>]+>', '', raw_abstract))
        conclusion = safe_text(extract_conclusion(raw_abstract))

        # The Ultimate UI Hack: HTML `<details>` element for perfectly tinted, unified cards.
        st.markdown(f"""
        <div style="background-color: {theme['bg']}; border: 1px solid {theme['border']}; border-left: 6px solid {theme['border']}; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
            <div style="font-size: 0.75rem; font-weight: 800; color: {theme['text']}; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">
                {theme['label']} • {raw_journal}
            </div>
            <a href="{link}" target="_blank" style="font-size: 1.2rem; font-weight: 700; color: #0F172A; text-decoration: none; display: block; margin-bottom: 8px; line-height: 1.4;">
                {title}
            </a>
            <div style="font-size: 0.9rem; color: #64748B; margin-bottom: 15px;">
                <strong>Published:</strong> {date} &nbsp;|&nbsp; <i>{authors}</i>
            </div>
            
            <details style="cursor: pointer; outline: none;">
                <summary style="font-size: 0.95rem; font-weight: 600; color: {theme['text']}; user-select: none;">
                    ▶ View Abstract & Extracted Conclusion
                </summary>
                <div style="margin-top: 15px; font-size: 0.95rem; color: #334155; line-height: 1.6; padding-top: 15px; border-top: 1px solid rgba(0,0,0,0.05);">
                    <p>{clean_abstract}</p>
                    <div style="background-color: rgba(255,255,255,0.7); border-left: 3px solid {theme['border']}; padding: 12px; margin-top: 15px; border-radius: 0 6px 6px 0;">
                        <strong style="color: {theme['text']}; font-size: 0.85rem; text-transform: uppercase;">Extracted Conclusion</strong><br>
                        {conclusion}
                    </div>
                </div>
            </details>
        </div>
        """, unsafe_allow_html=True)

# --- TABBED NAVIGATION ---
t_circuits, t_aav, t_hcc, t_news = st.tabs([
    "🧬 SynBio & Logic Circuits", 
    "🦠 AAV Engineering", 
    "🔬 HCC Immunotherapy", 
    "📈 Industry News"
])

with t_circuits:
    with st.spinner('Querying EuropePMC...'):
        render_papers(fetch_papers(query_circuits, days_to_fetch), literature_filter, selected_journals)

with t_aav:
    with st.spinner('Querying EuropePMC...'):
        render_papers(fetch_papers(query_aav, days_to_fetch), literature_filter, selected_journals)

with t_hcc:
    with st.spinner('Querying EuropePMC...'):
        render_papers(fetch_papers(query_hcc, days_to_fetch), literature_filter, selected_journals)

with t_news:
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
                # Business News uses a sleek slate/indigo theme
                st.markdown(f"""
                <div style="background-color: #F8FAFC; border: 1px solid #CBD5E1; border-left: 6px solid #475569; border-radius: 8px; padding: 20px; margin-bottom: 15px;">
                    <div style="font-size: 0.75rem; font-weight: 800; color: #475569; text-transform: uppercase; margin-bottom: 8px;">INDUSTRY NEWS • {s}</div>
                    <a href="{l}" target="_blank" style="font-size: 1.15rem; font-weight: 600; color: #0F172A; text-decoration: none; display: block; margin-bottom: 8px;">{t}</a>
                    <div style="font-size: 0.85rem; color: #64748B;">Published: {d}</div>
                </div>
                """, unsafe_allow_html=True)
