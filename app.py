import streamlit as st
import requests
import feedparser
from datetime import datetime, timedelta
import time

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Lab Literature Dashboard", 
    page_icon="🧬", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- MINIMAL CSS FOR TYPOGRAPHY (Respects Light/Dark Mode) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0px;
        padding-top: 10px;
    }
    .sub-header {
        font-size: 1.1rem;
        font-weight: 400;
        color: gray;
        text-align: center;
        margin-bottom: 30px;
    }
    </style>
""", unsafe_allow_html=True)

# --- ROBUST DATA FETCHING ---

@st.cache_data(ttl=43200, show_spinner=False)
def fetch_papers(topic_query, days_back=7):
    """Fetches and sorts recent papers from Europe PMC with strict error handling."""
    date_from = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    date_to = datetime.now().strftime('%Y-%m-%d')
    
    full_query = f'({topic_query}) AND FIRST_PDATE:[{date_from} TO {date_to}]'
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    
    params = {
        'query': full_query,
        'format': 'json',
        'resultType': 'core',
        'pageSize': 25 
    }
    
    try:
        # Added a strict 10-second timeout to prevent infinite hangs
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        papers = response.json().get('resultList', {}).get('result', [])
        
        # Sort chronologically, handling missing dates safely
        return sorted(papers, key=lambda x: x.get('firstPublicationDate', '1900-01-01'), reverse=True)
    
    except requests.exceptions.RequestException as e:
        st.error(f"API Connection Error: Could not retrieve literature. ({e})")
        return []

@st.cache_data(ttl=43200, show_spinner=False)
def fetch_news():
    """Fetches and sorts biotech industry news with bulletproof date parsing."""
    feeds = {
        "Fierce Biotech": "https://www.fiercebiotech.com/rss/xml",
        "Endpoints News": "https://endpts.com/feed/"
    }
    
    news_items = []
    for source, url in feeds.items():
        try:
            parsed = feedparser.parse(url)
            for entry in parsed.entries[:6]:
                # Bulletproof date extraction
                dt = datetime.now() # Fallback
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                    except (TypeError, OverflowError):
                        pass # Keep the fallback
                
                news_items.append({
                    'source': source,
                    'title': entry.get('title', 'Untitled Article'),
                    'link': entry.get('link', '#'),
                    'published_str': dt.strftime('%b %d, %Y'),
                    'date_obj': dt
                })
        except Exception:
            pass # Silently continue if one feed fails, protecting the overall UI
            
    # Sort chronologically (Newest first)
    return sorted(news_items, key=lambda x: x['date_obj'], reverse=True)

# --- QUERIES ---
query_circuits = '("synthetic gene circuit" OR "synthetic biology" OR "genetic circuit") AND ("AND gate" OR "NOT gate" OR "OR gate" OR "boolean logic" OR "cancer")'
query_aav = '"AAV" OR "adeno-associated virus" OR "AAV engineering" OR "AAV capsid"'
query_hcc = '"hepatocellular carcinoma" AND "immunotherapy"'

# --- MAIN UI ---
st.markdown("<div class='main-header'>Lab Literature Dashboard</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>Real-time curation of high-impact publications and industry intelligence.</div>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Engine Parameters")
    days_to_fetch = st.slider("Timeframe (Days)", min_value=1, max_value=30, value=7)
    
    st.markdown("---")
    if st.button("🔄 Force Data Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.caption("Cache auto-refreshes every 12 hours.")

# --- RENDERING LOGIC ---
def render_papers(papers):
    if not papers:
        st.info("No publications met the criteria in the selected timeframe.")
        return
        
    for p in papers:
        title = p.get('title', 'Unknown Title')
        journal = p.get('journalTitle', p.get('bookOrReportDetails', {}).get('publisher', 'Preprint / Repository'))
        date = p.get('firstPublicationDate', 'Unknown Date')
        authors = p.get('authorString', 'Unknown Authors')
        doi = p.get('doi', '')
        pmid = p.get('pmid', '')
        abstract = p.get('abstractText', 'No abstract available.')
        
        # Robust Link Generation
        if doi:
            link = f"https://doi.org/{doi}"
        elif pmid:
            link = f"https://europepmc.org/article/MED/{pmid}"
        else:
            link = f"https://europepmc.org/search?query={title.replace(' ', '+')}"

        clean_abstract = abstract.replace("<i>", "").replace("</i>", "").replace("<b>", "").replace("</b>", "")

        # Native Streamlit Card Container
        with st.container(border=True):
            st.markdown(f"#### [{title}]({link})")
            st.markdown(f"**{journal}** &nbsp;|&nbsp; {date} &nbsp;|&nbsp; _{authors}_")
            
            with st.expander("View Abstract & Insights"):
                st.write(clean_abstract)
                st.markdown(f"[🔗 Direct Link to Source]({link})")

# --- TABBED NAVIGATION ---
t_circuits, t_aav, t_hcc, t_news = st.tabs([
    "🧬 SynBio & Logic Circuits", 
    "🦠 AAV Engineering", 
    "🔬 HCC Immunotherapy", 
    "📈 Industry News"
])

with t_circuits:
    with st.spinner('Querying Database...'):
        render_papers(fetch_papers(query_circuits, days_to_fetch))

with t_aav:
    with st.spinner('Querying Database...'):
        render_papers(fetch_papers(query_aav, days_to_fetch))

with t_hcc:
    with st.spinner('Querying Database...'):
        render_papers(fetch_papers(query_hcc, days_to_fetch))

with t_news:
    with st.spinner('Aggregating Feeds...'):
        news = fetch_news()
        if not news:
            st.info("No industry news available at this time.")
        else:
            for item in news:
                with st.container(border=True):
                    st.markdown(f"#### [{item['title']}]({item['link']})")
                    st.markdown(f"**{item['source']}** &nbsp;|&nbsp; Published: {item['published_str']}")
