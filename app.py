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

# --- ADVANCED UI/UX CSS INJECTION ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Hero Banner Header */
    .hero-banner {
        background: linear-gradient(135deg, #0A2540 0%, #1e3d59 100%);
        padding: 30px;
        border-radius: 12px;
        text-align: center;
        color: white;
        margin-bottom: 30px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 5px;
        letter-spacing: -0.5px;
    }
    .hero-subtitle {
        font-size: 1.05rem;
        font-weight: 400;
        color: #94A3B8;
    }

    /* Center the Streamlit Tabs */
    div[data-baseweb="tab-list"] {
        justify-content: center !important;
        gap: 15px;
    }
    div[data-baseweb="tab"] {
        font-size: 1.05rem !important;
        font-weight: 600 !important;
    }

    /* Journal Badge beside Title */
    .journal-badge {
        display: inline-block;
        background-color: #E2E8F0;
        color: #0F172A;
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
    .preprint-badge {
        background-color: #FEF3C7;
        color: #92400E;
    }
    
    /* Customization for the Expander Summary */
    .summary-box {
        background-color: #F8FAFC;
        border-left: 4px solid #00D2B6;
        padding: 15px;
        margin-top: 15px;
        border-radius: 4px;
        font-size: 0.95rem;
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
    
    # Clean HTML tags
    clean_text = re.sub(r'<[^>]+>', '', abstract_text)
    
    # Split into sentences safely
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', clean_text) if len(s.strip()) > 10]
    
    if len(sentences) <= 3:
        return clean_text
    
    # Return the last 2 sentences as the likely conclusion
    return " ".join(sentences[-2:])

# --- ROBUST DATA FETCHING ---

@st.cache_data(ttl=43200, show_spinner=False)
def fetch_papers(topic_query, days_back=7, lit_type="All"):
    """Fetches and sorts recent papers with type filtering."""
    date_from = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    date_to = datetime.now().strftime('%Y-%m-%d')
    
    # Apply Preprint vs Peer-Reviewed Logic via Europe PMC SRC tags
    type_filter = ""
    if lit_type == "Peer-Reviewed Only":
        type_filter = " AND (NOT SRC:PPR)"
    elif lit_type == "Preprints Only":
        type_filter = " AND (SRC:PPR)"
        
    full_query = f'({topic_query}){type_filter} AND FIRST_PDATE:[{date_from} TO {date_to}]'
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    
    params = {
        'query': full_query,
        'format': 'json',
        'resultType': 'core',
        'pageSize': 25 
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
    <div class="hero-subtitle">Real-time curation of high-impact publications, preprints, and industry intelligence.</div>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.markdown("### ⚙️ Engine Parameters")
    
    # New Filter Control
    st.markdown("#### Source Filter")
    literature_filter = st.radio(
        "Select literature type:",
        ["All", "Peer-Reviewed Only", "Preprints Only"],
        label_visibility="collapsed"
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
        st.info("No publications met the criteria in the selected timeframe.")
        return
        
    for p in papers:
        title = p.get('title', 'Unknown Title')
        
        # Determine Source and Badge styling
        is_preprint = p.get('pubType', '') == 'preprint' or p.get('source') == 'PPR'
        raw_journal = p.get('journalTitle', p.get('bookOrReportDetails', {}).get('publisher', 'Repository'))
        
        # Clean up common preprint server names for the badge
        if "bioRxiv" in raw_journal or is_preprint:
            badge_class = "journal-badge preprint-badge"
            journal_display = "Preprint: " + raw_journal
        else:
            badge_class = "journal-badge"
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
            # Inline Journal Badge + Title
            st.markdown(f"#### <span class='{badge_class}'>{journal_display}</span> <a href='{link}' style='color: inherit; text-decoration: none;'>{title}</a>", unsafe_allow_html=True)
            
            # Author and Date Meta
            st.markdown(f"<div style='color: #64748B; font-size: 0.9rem; margin-bottom: 10px;'>Published: {date} &nbsp;|&nbsp; <i>{authors}</i></div>", unsafe_allow_html=True)
            
            with st.expander("View Abstract & Extracted Conclusion"):
                # Clean Abstract
                st.write(clean_abstract)
                
                # Heuristic Summary Box
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
        render_papers(fetch_papers(query_circuits, days_to_fetch, literature_filter))

with t_aav:
    with st.spinner('Querying Database...'):
        render_papers(fetch_papers(query_aav, days_to_fetch, literature_filter))

with t_hcc:
    with st.spinner('Querying Database...'):
        render_papers(fetch_papers(query_hcc, days_to_fetch, literature_filter))

with t_news:
    with st.spinner('Aggregating Feeds...'):
        news = fetch_news()
        if not news:
            st.info("No industry news available at this time.")
        else:
            for item in news:
                with st.container(border=True):
                    st.markdown(f"#### <span class='journal-badge' style='background-color: #E0E7FF; color: #3730A3;'>{item['source']}</span> <a href='{item['link']}' style='color: inherit; text-decoration: none;'>{item['title']}</a>", unsafe_allow_html=True)
                    st.markdown(f"<div style='color: #64748B; font-size: 0.9rem;'>Published: {item['published_str']}</div>", unsafe_allow_html=True)
