import streamlit as st
import requests
import feedparser
from datetime import datetime, timedelta
import time
import re

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Lab Literature Dashboard", 
    page_icon="🧬", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- ADVANCED UI/UX CSS INJECTION & ANIMATIONS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Subliminal Ambient Background Animation */
    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .stApp {
        background: linear-gradient(-45deg, #f8f9fc, #f1f5f9, #e2e8f0, #edf2f7);
        background-size: 400% 400%;
        animation: gradientBG 20s ease infinite;
    }
    
    /* Hero Banner Header with Vibrant Animated Gradient */
    .hero-banner {
        background: linear-gradient(-45deg, #0f2027, #203a43, #2c5364, #1e3d59, #00D2B6);
        background-size: 300% 300%;
        animation: gradientBG 15s ease infinite;
        padding: 35px;
        border-radius: 12px;
        text-align: center;
        color: white;
        margin-bottom: 30px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }
    .hero-title {
        font-size: 2.4rem;
        font-weight: 700;
        margin-bottom: 8px;
        letter-spacing: -0.5px;
        text-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    .hero-subtitle {
        font-size: 1.1rem;
        font-weight: 400;
        color: #e2e8f0;
    }

    /* Center the Streamlit Tabs */
    div[data-baseweb="tab-list"] {
        justify-content: center !important;
        gap: 20px;
    }
    div[data-baseweb="tab"] {
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        padding-bottom: 10px !important;
    }

    /* Base Journal Badge */
    .journal-badge {
        display: inline-block;
        color: #ffffff;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-right: 12px;
        vertical-align: middle;
        transform: translateY(-2px);
    }
    
    /* Specific Journal Color Palettes */
    .badge-nature { background-color: #10b981; box-shadow: 0 2px 4px rgba(16, 185, 129, 0.3); } /* Emerald */
    .badge-cell { background-color: #ef4444; box-shadow: 0 2px 4px rgba(239, 68, 68, 0.3); } /* Crimson */
    .badge-science { background-color: #0ea5e9; box-shadow: 0 2px 4px rgba(14, 165, 233, 0.3); } /* Cyan */
    .badge-nejm { background-color: #4f46e5; box-shadow: 0 2px 4px rgba(79, 70, 229, 0.3); } /* Indigo */
    .badge-preprint { background-color: #f59e0b; box-shadow: 0 2px 4px rgba(245, 158, 11, 0.3); } /* Amber */
    .badge-default { background-color: #64748b; box-shadow: 0 2px 4px rgba(100, 116, 139, 0.3); } /* Slate */
    
    /* Customization for the Expander Summary */
    .summary-box {
        background-color: rgba(255, 255, 255, 0.8);
        border-left: 4px solid #00D2B6;
        padding: 15px;
        margin-top: 15px;
        border-radius: 4px;
        font-size: 0.95rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .summary-label {
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 5px;
        text-transform: uppercase;
        font-size: 0.8rem;
        letter-spacing: 0.5px;
    }
    </style>
""", unsafe_allow_html=True)

# --- UTILITY FUNCTIONS ---

def extract_conclusion(abstract_text):
    """Heuristic to extract the likely conclusion from an abstract."""
    if not abstract_text or len(abstract_text) < 50:
        return "No sufficient abstract text to extract conclusions."
    
    clean_text = re.sub(r'<[^>]+>', '', abstract_text)
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', clean_text) if len(s.strip()) > 10]
    
    if len(sentences) <= 3:
        return clean_text
    
    return " ".join(sentences[-2:])

def get_journal_name(paper_data):
    """Cascading extraction to correctly identify the journal name."""
    raw = paper_data.get('journalTitle')
    if not raw:
        raw = paper_data.get('journalInfo', {}).get('journal', {}).get('title')
    if not raw:
        raw = paper_data.get('bookOrReportDetails', {}).get('publisher')
    return raw if raw else "Unknown Publisher"

# --- ROBUST DATA FETCHING ---

@st.cache_data(ttl=43200, show_spinner=False)
def fetch_papers(topic_query, days_back=7, lit_type="All", specific_journals=None):
    """Fetches and sorts recent papers with type and journal filtering."""
    date_from = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    date_to = datetime.now().strftime('%Y-%m-%d')
    
    type_filter = ""
    if lit_type == "Peer-Reviewed Only":
        type_filter = " AND (NOT SRC:PPR)"
    elif lit_type == "Preprints Only":
        type_filter = " AND (SRC:PPR)"

    journal_filter = ""
    if specific_journals and len(specific_journals) > 0:
        j_queries = [f'JOURNAL:"{j}"' for j in specific_journals]
        journal_filter = f" AND ({' OR '.join(j_queries)})"
        
    full_query = f'({topic_query}){type_filter}{journal_filter} AND FIRST_PDATE:[{date_from} TO {date_to}]'
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    
    params = {
        'query': full_query,
        'format': 'json',
        'resultType': 'core',
        'pageSize': 30 
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        papers = response.json().get('resultList', {}).get('result', [])
        return sorted(papers, key=lambda x: x.get('firstPublicationDate', '1900-01-01'), reverse=True)
    except requests.exceptions.RequestException as e:
        st.error(f"API Connection Error: {e}")
        return []

@st.cache_data(ttl=43200, show_spinner=False)
def fetch_news():
    """Fetches biotech industry news."""
    feeds = {
        "Fierce Biotech": "https://www.fiercebiotech.com/rss/xml",
        "Endpoints News": "https://endpts.com/feed/"
    }
    
    news_items = []
    for source, url in feeds.items():
        try:
            parsed = feedparser.parse(url)
            for entry in parsed.entries[:6]:
                dt = datetime.now()
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                    except (TypeError, OverflowError):
                        pass 
                
                news_items.append({
                    'source': source,
                    'title': entry.get('title', 'Untitled Article'),
                    'link': entry.get('link', '#'),
                    'published_str': dt.strftime('%b %d, %Y'),
                    'date_obj': dt
                })
        except Exception:
            pass 
            
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
    
    st.markdown("#### Source Filter")
    literature_filter = st.radio(
        "Select literature type:",
        ["All", "Peer-Reviewed Only", "Preprints Only"],
        label_visibility="collapsed"
    )
    
    st.markdown("#### Specific Journals (Optional)")
    selected_journals = st.multiselect(
        "Filter by target publications:",
        ["Nature", "Cell", "Science", "New England Journal of Medicine", 
         "Nature Biotechnology", "Nature Medicine", "Hepatology", 
         "ACS Synthetic Biology", "bioRxiv", "medRxiv"],
        default=[]
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    days_to_fetch = st.slider("Timeframe (Days)", min_value=1, max_value=30, value=7)
    
    st.markdown("---")
    if st.button("🔄 Force Data Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# --- RENDERING LOGIC ---
def render_papers(papers):
    if not papers:
        st.info("No publications met the criteria in the selected timeframe/filters.")
        return
        
    for p in papers:
        title = p.get('title', 'Unknown Title')
        raw_journal = get_journal_name(p)
        journal_lower = raw_journal.lower()
        
        is_preprint = p.get('pubType', '') == 'preprint' or p.get('source') == 'PPR' or "rxiv" in journal_lower
        
        # Color-Coordinated Badge Logic
        if is_preprint:
            badge_class = "journal-badge badge-preprint"
            journal_display = "Preprint: " + raw_journal
        elif "nature" in journal_lower:
            badge_class = "journal-badge badge-nature"
            journal_display = raw_journal
        elif "cell" in journal_lower:
            badge_class = "journal-badge badge-cell"
            journal_display = raw_journal
        elif "science" in journal_lower:
            badge_class = "journal-badge badge-science"
            journal_display = raw_journal
        elif "new england journal" in journal_lower or "nejm" in journal_lower:
            badge_class = "journal-badge badge-nejm"
            journal_display = raw_journal
        else:
            badge_class = "journal-badge badge-default"
            journal_display = raw_journal

        date = p.get('firstPublicationDate', 'Unknown Date')
        authors = p.get('authorString', 'Unknown Authors')
        doi = p.get('doi', '')
        pmid = p.get('pmid', '')
        abstract = p.get('abstractText', 'No abstract available.')
        
        if doi: link = f"https://doi.org/{doi}"
        elif pmid: link = f"https://europepmc.org/article/MED/{pmid}"
        else: link = f"https://europepmc.org/search?query={title.replace(' ', '+')}"

        clean_abstract = re.sub(r'<[^>]+>', '', abstract)
        conclusion = extract_conclusion(abstract)

        with st.container(border=True):
            st.markdown(f"#### <span class='{badge_class}'>{journal_display}</span> <a href='{link}' style='color: #0F172A; text-decoration: none;'>{title}</a>", unsafe_allow_html=True)
            st.markdown(f"<div style='color: #64748B; font-size: 0.9rem; margin-bottom: 10px;'>Published: {date} &nbsp;|&nbsp; <i>{authors}</i></div>", unsafe_allow_html=True)
            
            with st.expander("View Abstract & Extracted Conclusion"):
                st.write(clean_abstract)
                st.markdown(f"""
                <div class="summary-box">
                    <div class="summary-label">Extracted Conclusion</div>
                    {conclusion}
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"<br>[🔗 Direct Link to Source]({link})", unsafe_allow_html=True)

# --- TABBED NAVIGATION ---
t_circuits, t_aav, t_hcc, t_news = st.tabs([
    "🧬 SynBio & Logic Circuits", 
    "🦠 AAV Engineering", 
    "🔬 HCC Immunotherapy", 
    "📈 Industry News"
])

with t_circuits:
    with st.spinner('Querying Database...'):
        render_papers(fetch_papers(query_circuits, days_to_fetch, literature_filter, selected_journals))

with t_aav:
    with st.spinner('Querying Database...'):
        render_papers(fetch_papers(query_aav, days_to_fetch, literature_filter, selected_journals))

with t_hcc:
    with st.spinner('Querying Database...'):
        render_papers(fetch_papers(query_hcc, days_to_fetch, literature_filter, selected_journals))

with t_news:
    with st.spinner('Aggregating Feeds...'):
        news = fetch_news()
        if not news:
            st.info("No industry news available at this time.")
        else:
            for item in news:
                with st.container(border=True):
                    # Using the Indigo badge for Industry news for separation
                    st.markdown(f"#### <span class='journal-badge badge-nejm'>{item['source']}</span> <a href='{item['link']}' style='color: #0F172A; text-decoration: none;'>{item['title']}</a>", unsafe_allow_html=True)
                    st.markdown(f"<div style='color: #64748B; font-size: 0.9rem;'>Published: {item['published_str']}</div>", unsafe_allow_html=True)
