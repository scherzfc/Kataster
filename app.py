"""
Kataster-Sorter – Streamlit Web App
Sortierung & Deckblatt-Zuordnung für Liegenschaftskataster-Auszüge.
"""

import streamlit as st
from pdf_processor import KatasterSorter


st.set_page_config(
    page_title="Kataster-Sorter",
    page_icon="📄",
    layout="centered"
)

# === Custom CSS ===
st.markdown("""
<style>
    .stApp {
        max-width: 800px;
        margin: 0 auto;
    }
    .main-header {
        background: linear-gradient(135deg, #1a237e 0%, #283593 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2rem;
    }
    .main-header p {
        color: #b0bec5;
        margin: 0.3rem 0 0 0;
        font-size: 0.95rem;
    }
    .stat-box {
        background: #1e1e2e;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        border: 1px solid #333;
    }
    .stat-box .number {
        font-size: 1.8rem;
        font-weight: bold;
        color: #4caf50;
    }
    .stat-box .label {
        font-size: 0.85rem;
        color: #888;
    }
</style>
""", unsafe_allow_html=True)

# === Header ===
st.markdown("""
<div class="main-header">
    <h1>📄 Kataster-Sorter</h1>
    <p>PDFs hochladen – automatische Erkennung, Sortierung & Deckblatt-Zuordnung</p>
</div>
""", unsafe_allow_html=True)

# === File Upload ===
uploaded_files = st.file_uploader(
    "**PDF-Dateien hochladen**",
    type=["pdf"],
    accept_multiple_files=True,
    help="Kataster-Auszug und Deckblätter gemeinsam hochladen. "
         "Die App erkennt automatisch, was was ist."
)

if uploaded_files:
    file_names = [f.name for f in uploaded_files]
    st.info(f"📎 {len(uploaded_files)} Datei(en): {', '.join(file_names)}")

# === Verarbeiten ===
if uploaded_files and st.button(
    "▶️ Verarbeiten",
    type="primary",
    use_container_width=True
):
    with st.spinner("Analysiere und sortiere..."):
        try:
            sorter = KatasterSorter()
            
            # Dateien einlesen
            file_data = []
            for f in uploaded_files:
                file_data.append((f.name, f.read()))
            
            result = sorter.process_files(file_data)
            st.session_state['result'] = result
            
        except Exception as e:
            st.error(f"❌ Fehler: {e}")
            st.session_state['result'] = None

# === Ergebnisse ===
if 'result' in st.session_state and st.session_state['result']:
    r = st.session_state['result']
    
    st.success("✅ Verarbeitung abgeschlossen!")
    
    # Stats
    cols = st.columns(4)
    with cols[0]:
        st.metric("Seiten", r['total_pages'])
    with cols[1]:
        st.metric("Standard", r['standard_count'])
    with cols[2]:
        st.metric("Sonderfälle", r['sonderfall_count'])
    with cols[3]:
        cover_total = r['cover_standard_count'] + r['cover_sonder_count']
        st.metric("Deckblätter", cover_total)
    
    # AKZ Info
    if r['kataster_akz']:
        akz_text = f"**Antragskennzeichen:** `{r['kataster_akz']}`"
        if r['akz_mismatches']:
            akz_text += f" — {len(r['akz_mismatches'])} Korrektur(en)"
        st.info(akz_text)
    
    # Download
    if r['combined_pdf']:
        st.download_button(
            label="💾 Kombinierte PDF herunterladen",
            data=r['combined_pdf'],
            file_name="Kataster_Komplett.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )
    
    # Debug-Info
    with st.expander("🔍 Debug-Info"):
        for line in r.get('debug_log', []):
            st.text(line)
        
        if r['akz_mismatches']:
            st.markdown("**AKZ-Korrekturen:**")
            for m in r['akz_mismatches']:
                st.text(f"  {m}")
