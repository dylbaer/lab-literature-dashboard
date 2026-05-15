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
    
    /* Summary Paragraph Styling */
    .narrative-summary {
        background: rgba(255,255,255,0.85); border-left: 6px solid #D8B4FE;
        padding: 25px; border-radius: 12px; font-size: 1.1rem; color: #2D3748;
        line-height: 1.7; box-shadow: 0 4px 15px rgba(0,0,0,0.03); margin-bottom: 30px;
    }
    .narrative-summary a { color: #9F7AEA; font-weight: 600; text-decoration: none; }
    .narrative-summary a:hover { text-decoration: underline; }
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
    params = {"query.term": query_term, "pageSize": 50, "format": "json"}
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
                'ID': id_mod.get('nctId', 'Unknown'),
                'Title': id_mod.get('briefTitle', 'Untitled Trial'),
                'Status': stat_mod.get('overallStatus', 'Unknown'),
                'Phase': ", ".join(design_mod.get('phases', ['Unknown'])),
                'Sponsor': sponsor_mod.get('leadSponsor', {}).get('name', 'Unknown Sponsor'),
                'Updated': stat_mod.get('statusDate', 'Recent')
            })
    except Exception as e: pass
    return trials

# --- EXHAUSTIVE TARGETED QUERIES ---
queries = {
    "SynBio": '("synthetic biology" OR "synthetic genome")',
    "Logic": '("synthetic gene circuit" OR "genetic circuit" OR "AND gate" OR "NOT gate" OR "OR gate" OR "boolean logic" OR "logic gate") AND ("gene therapy" OR "AAV" OR "cancer" OR "cell therapy" OR "HCC" OR "CRC")',
    "AAV": '("AAV" OR "adeno-associated virus" OR "AAV capsid" OR "directed evolution AAV")',
    "CMC": '("AAV" OR "lentivirus" OR "viral vector") AND ("CMC" OR "manufacturing" OR "bioprocessing" OR "GMP" OR "scale-up" OR "downstream processing")',
    "NonViral": '("LNP" OR "lipid nanoparticle" OR "polymeric nanoparticle" OR "non-viral delivery" OR "liposome" OR "VLP" OR "polyplex")',
    "ViralBroad": '("viral vector" OR "lentivirus" OR "adenovirus" OR "retrovirus" OR "baculovirus")',
    "HCC_CRC": '("hepatocellular carcinoma" OR "HCC" OR "colorectal cancer" OR "CRC") AND ("immunotherapy" OR "CAR-T" OR "gene therapy")'
}

# Heavily restricted VC query to prevent "raised awareness" false positives
vc_funding_feeds = { 
    "Biotech VC Deals": "https://news.google.com/rss/search?q=(%22Series+A%22+OR+%22Series+B%22+OR+%22Series+C%22+OR+%22seed+round%22+OR+%22financing+round%22+OR+%22secures+funding%22)+AND+(%22gene+therapy%22+OR+%22cell+therapy%22+OR+%22synthetic+biology%22+OR+%22oncology%22)&hl=en-US&gl=US&ceid=US:en" 
}

# --- CURATED COMPETITOR PIPELINE DATABASE ---
# Hardcoded curated pipeline reflecting actual entities in the logic/cell therapy/HCC space
pipeline_data = [
    {"Company": "Senti Biosciences", "Asset": "SENTI-202", "Modality": "Logic-Gated CAR-NK (OR + NOT)", "Indication": "AML", "Stage": "Phase 1", "Progress": 60},
    {"Company": "Senti Biosciences", "Asset": "SENTI-301A", "Modality": "Logic-Gated CAR-NK", "Indication": "HCC", "Stage": "Preclinical", "Progress": 30},
    {"Company": "Strand Therapeutics", "Asset": "STX-001", "Modality": "Programmable mRNA Circuit", "Indication": "Solid Tumors", "Stage": "Phase 1", "Progress": 60},
    {"Company": "ArsenalBio", "Asset": "AB-1015", "Modality": "Logic-Gated CAR-T (AND)", "Indication": "Ovarian Cancer", "Stage": "Phase 1", "Progress": 60},
    {"Company": "ArsenalBio", "Asset": "AB-2100", "Modality": "Logic-Gated CAR-T", "Indication": "Clear Cell Renal Cell Carcinoma", "Stage": "Phase 1", "Progress": 60},
    {"Company": "Trogenix", "Asset": "Undisclosed", "Modality": "Gene Circuit Therapy", "Indication": "Solid Tumors", "Stage": "Discovery", "Progress": 10},
    {"Company": "Link Cell Therapies", "Asset": "Undisclosed", "Modality": "Cell Therapy", "Indication": "Oncology", "Stage": "Discovery", "Progress": 10},
    {"Company": "Sirin", "Asset": "Undisclosed", "Modality": "Precision Gene Therapy", "Indication": "Undisclosed", "Stage": "Discovery", "Progress": 10}
]

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
        "📚 Literature", 
        "🏥 Clinical Trials", 
        "💰 VC Finance", 
        "🤺 Competitor Pipeline", 
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
    st.markdown("### ⚡ Executive Narrative Briefing")
    
    cutoff_date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
    
    with st.spinner("Synthesizing Intel..."):
        syn_papers = [p for p in fetch_papers(queries["SynBio"], days_to_fetch, open_access_only) if p.get('firstPublicationDate', '') >= cutoff_date]
        circuits_papers = [p for p in fetch_papers(queries["Logic"], days_to_fetch, open_access_only) if p.get('firstPublicationDate', '') >= cutoff_date]
        aav_papers = [p for p in fetch_papers(queries["AAV"], days_to_fetch, open_access_only) if p.get('firstPublicationDate', '') >= cutoff_date]
        trials = [t for t in fetch_clinical_trials("Hepatocellular Carcinoma OR Colorectal Cancer OR AAV") if t.get('Updated', '') >= cutoff_date]
        fin_news = [n for n in fetch_news(vc_funding_feeds) if n['published_str'] >= cutoff_date]
    
    # Automated Narrative Generation
    narrative = []
    total_papers = len(syn_papers) + len(circuits_papers) + len(aav_papers)
    
    if total_papers > 0 or trials or fin_news:
        narrative.append(f"In the past 48 hours, **{total_papers} new publications** were indexed across our core technical domains.")
        
        if circuits_papers:
            p = circuits_papers[0]
            link = f"https://doi.org/{p.get('doi')}" if p.get('doi') else "#"
            narrative.append(f"Notably in *Genetic Circuits*, a new paper titled <a href='{link}' target='_blank'>'{p.get('title', 'Unknown')}'</a> was published in {get_journal_name(p)}.")
        elif aav_papers:
            p = aav_papers[0]
            link = f"https://doi.org/{p.get('doi')}" if p.get('doi') else "#"
            narrative.append(f"In *AAV Engineering*, recent work titled <a href='{link}' target='_blank'>'{p.get('title', 'Unknown')}'</a> highlights new developments.")
            
        if trials:
            t = trials[0]
            narrative.append(f"On the translational front, **{t['Sponsor']}** updated the status of their clinical trial for <a href='https://clinicaltrials.gov/study/{t['ID']}' target='_blank'>'{t['Title']}'</a> to *{t['Status']}* ({t['Phase']}).")
        
        if fin_news:
            n = fin_news[0]
            narrative.append(f"In industry financing, <a href='{n['link']}' target='_blank'>{n['title']}</a> was recently announced, signaling continued capital deployment in the gene and cell therapy sector.")
            
        summary_html = f"<div class='narrative-summary'>{' '.join(narrative)}</div>"
        st.markdown(summary_html, unsafe_allow_html=True)
    else:
        st.markdown("<div class='narrative-summary'>No significant new publications, clinical trial updates, or funding rounds were detected in your core domains over the last 48 hours.</div>", unsafe_allow_html=True)

elif current_view == "📚 Literature":
    st.markdown("### 📚 Curated Literature")
    
    lit_tabs = st.tabs(["🧬 SynBio", "🧮 Genetic Circuits", "🦠 AAV Eng", "🏭 CMC & Mfg", "💉 Non-Viral", "🔬 Viral Delivery", "🎯 HCC & CRC"])
    
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
            with st.spinner('Querying Database...'):
                raw_papers = fetch_papers(query, days_to_fetch, open_access_only)
                filtered_papers = filter_papers_by_ui(raw_papers)
                if not filtered_papers:
                    st.info("No publications met the criteria.")
                else:
                    for p in filtered_papers[:30]:
                        render_paper_card(p, context=context_id)

elif current_view == "🏥 Clinical Trials":
    st.markdown("### 🏥 Clinical Trial Tracker")
    st.write("Structured data pulled directly from ClinicalTrials.gov for 'HCC', 'CRC', 'AAV', and 'Gene Therapy'.")
    
    with st.spinner("Structuring Trial Data..."):
        trials = fetch_clinical_trials("Hepatocellular Carcinoma OR Colorectal Cancer OR AAV OR Gene Therapy")
        if not trials: 
            st.info("No recent trials fetched.")
        else:
            df_trials = pd.DataFrame(trials)
            st.dataframe(
                df_trials, 
                column_config={
                    "Title": st.column_config.TextColumn("Trial Title", width="large"),
                    "Status": st.column_config.TextColumn("Status", width="medium"),
                    "Phase": st.column_config.TextColumn("Phase", width="small")
                },
                hide_index=True,
                use_container_width=True
            )

elif current_view == "💰 VC Finance":
    st.markdown("### 💰 Financial Intelligence")
    st.write("Tracking Series A/B, seed rounds, and venture capital raises in the Gene and Cell Therapy sector.")
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
                safe_hash = re.sub(r'[^a-zA-Z0-9]', '', item['title'])[:15]
                if st.button("⭐ Save", key=f"save_n_{safe_hash}"): save_item(item['title'], item['link'], "Finance", item['published_str'])
            st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

elif current_view == "🤺 Competitor Pipeline":
    st.markdown("### 🤺 Competitor Entity Pipeline")
    st.write("A curated, visual representation of clinical and preclinical assets developed by rival organizations focusing on logic gating, cell therapy, and precision oncology.")
    
    df_pipeline = pd.DataFrame(pipeline_data)
    
    st.dataframe(
        df_pipeline,
        column_config={
            "Company": st.column_config.TextColumn("Entity", width="medium"),
            "Asset": st.column_config.TextColumn("Asset Name", width="small"),
            "Modality": st.column_config.TextColumn("Modality", width="medium"),
            "Indication": st.column_config.TextColumn("Target Indication", width="medium"),
            "Stage": st.column_config.TextColumn("Clinical Stage", width="small"),
            "Progress": st.column_config.ProgressColumn("Pipeline Progression", format="%f", min_value=0, max_value=100)
        },
        hide_index=True,
        use_container_width=True
    )
    
    st.markdown("<br><p style='font-size:0.85rem; color:gray;'>*Note: Early stage biotech pipelines are notoriously opaque. This table is manually curated based on publicly available PR and SEC filings.*</p>", unsafe_allow_html=True)

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
