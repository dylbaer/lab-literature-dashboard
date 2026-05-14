import streamlit as st
import requests
import feedparser
import pandas as pd
from datetime import datetime, timedelta

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Lab Literature Dashboard", page_icon="🧬", layout="wide")

# Custom CSS for a sleeker look
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .paper-title { font-size: 1.2rem; font-weight: 600; color: #1e3d59; margin-bottom: 0px;}
    .paper-meta { font-size: 0.9rem; color: #6c757d; margin-bottom: 10px;}
    .news-title { font-size: 1.1rem; font-weight: 600; color: #d9534f; margin-bottom: 0px;}
    </style>
""", unsafe_allow_html=True)

# --- DATA FETCHING FUNCTIONS ---

@st.cache_data(ttl=43200) # Cache data for 12 hours
def fetch_papers(topic_query, days_back=7):
    """Fetches recent papers from Europe PMC (covers PubMed, bioRxiv, etc.)"""
    date_from = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    date_to = datetime.now().strftime('%Y-%m-%d')
    
    # Constructing the Europe PMC query
    full_query = f'({topic_query}) AND FIRST_PDATE:[{date_from} TO {date_to}]'
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    
    params = {
        'query': full_query,
        'format': 'json',
        'resultType': 'core',
        'pageSize': 15  # Limit to top 15 most recent/relevant per category
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get('resultList', {}).get('result', [])
    except Exception as e:
        st.error(f"Error fetching literature: {e}")
        return []

@st.cache_data(ttl=43200)
def fetch_news():
    """Fetches biotech industry news from RSS feeds."""
    feeds = {
        "Fierce Biotech": "https://www.fiercebiotech.com/rss/xml",
        "Endpoints News": "https://endpts.com/feed/",
        "Google News (SynBio & AAV)": "https://news.google.com/rss/search?q=biotech+AND+(AAV+OR+%22synthetic+biology%22+OR+%22gene+therapy%22)&hl=en-US&gl=US&ceid=US:en"
    }
    
    news_items = []
    for source, url in feeds.items():
        try:
            parsed = feedparser.parse(url)
            # Grab top 5 articles from each feed
            for entry in parsed.entries[:5]:
                news_items.append({
                    'source': source,
                    'title': entry.get('title', 'No Title'),
                    'link': entry.get('link', '#'),
                    'published': entry.get('published', 'Recent')
                })
        except Exception as e:
            st.error(f"Error fetching news from {source}: {e}")
            
    return news_items

# --- QUERIES ---
# Group 1: AAV specific
query_aav = '"AAV" OR "adeno-associated virus" OR "AAV engineering" OR "AAV capsid"'

# Group 2: Synthetic Gene Circuits & Logic (Constrained to biology to avoid CS papers)
query_circuits = '("synthetic gene circuit" OR "synthetic biology" OR "genetic circuit") AND ("AND gate" OR "NOT gate" OR "OR gate" OR "boolean logic" OR "cancer")'

# Group 3: HCC & Immunotherapy
query_hcc = '"hepatocellular carcinoma" AND "immunotherapy"'


# --- UI LAYOUT ---
st.title("🧬 Lab Literature & Industry Dashboard")
st.markdown("Automated daily retrieval of publications, preprints, and biotech news.")

# Sidebar controls
with st.sidebar:
    st.header("⚙️ Settings")
    days_to_fetch = st.slider("Days of Literature to Fetch", min_value=1, max_value=30, value=7)
    if st.button("🔄 Refresh Data Now"):
        st.cache_data.clear()

# Tabs for organization
tab1, tab2, tab3, tab4 = st.tabs([
    "🧬 Synthetic Circuits & Logic", 
    "🦠 AAV Engineering", 
    "🔬 HCC & Immunotherapy", 
    "📈 Industry News"
])

def render_papers(papers):
    if not papers:
        st.info("No recent papers found for this topic in the selected timeframe.")
        return
        
    for p in papers:
        title = p.get('title', 'Unknown Title')
        journal = p.get('journalTitle', p.get('bookOrReportDetails', {}).get('publisher', 'Preprint/Unknown'))
        date = p.get('firstPublicationDate', 'Unknown Date')
        authors = p.get('authorString', 'Unknown Authors')
        doi = p.get('doi', '')
        link = f"https://doi.org/{doi}" if doi else f"https://europepmc.org/article/MED/{p.get('pmid', '')}"
        abstract = p.get('abstractText', 'No abstract available.')
        
        st.markdown(f"<p class='paper-title'><a href='{link}' target='_blank' style='color: #1e3d59; text-decoration: none;'>{title}</a></p>", unsafe_allow_html=True)
        st.markdown(f"<p class='paper-meta'><b>{journal}</b> | {date} | {authors}</p>", unsafe_allow_html=True)
        with st.expander("Read Abstract"):
            # Clean up HTML tags sometimes present in abstract text
            st.write(abstract.replace("<i>", "").replace("</i>", "").replace("<b>", "").replace("</b>", ""))
        st.divider()

# Render Tabs
with tab1:
    st.subheader("Synthetic Gene Circuits & Boolean Logic in Cancer")
    render_papers(fetch_papers(query_circuits, days_to_fetch))

with tab2:
    st.subheader("AAV Engineering & Delivery")
    render_papers(fetch_papers(query_aav, days_to_fetch))

with tab3:
    st.subheader("Hepatocellular Carcinoma & Immunotherapy")
    render_papers(fetch_papers(query_hcc, days_to_fetch))

with tab4:
    st.subheader("Biotech Industry & Startup News")
    news = fetch_news()
    if not news:
        st.info("No news fetched.")
    else:
        for item in news:
            st.markdown(f"<p class='news-title'><a href='{item['link']}' target='_blank' style='color: #d9534f; text-decoration: none;'>{item['title']}</a></p>", unsafe_allow_html=True)
            st.markdown(f"<p class='paper-meta'><b>{item['source']}</b> | {item['published']}</p>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
