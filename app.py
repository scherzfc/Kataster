"""
Kataster-Sorter: Streamlit Web App
Sortiert Liegenschaftskataster-Auszüge nach Fortführungsfallnummer und Grundbuchblatt.
"""

import streamlit as st
from pdf_processor import KatasterSorter

# Page config
st.set_page_config(
    page_title="Kataster-Sorter",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Material Design inspired styling
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global styles */
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main container */
    .main .block-container {
        max-width: 1200px;
        padding: 2rem 3rem;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #1a237e 0%, #3949ab 100%);
        color: white;
        padding: 2.5rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(26, 35, 126, 0.3);
    }
    
    .main-header h1 {
        margin: 0 0 0.5rem 0;
        font-weight: 700;
        font-size: 2.2rem;
    }
    
    .main-header p {
        margin: 0;
        opacity: 0.9;
        font-size: 1.1rem;
    }
    
    /* Upload area */
    .upload-area {
        background: linear-gradient(180deg, #f5f7ff 0%, #e8eaf6 100%);
        border: 2px dashed #5c6bc0;
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .upload-area:hover {
        border-color: #3949ab;
        background: linear-gradient(180deg, #e8eaf6 0%, #d1d9ff 100%);
    }
    
    /* Stats cards */
    .stat-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
        text-align: center;
        border-left: 4px solid;
    }
    
    .stat-card.primary {
        border-left-color: #3949ab;
    }
    
    .stat-card.success {
        border-left-color: #2e7d32;
    }
    
    .stat-card.warning {
        border-left-color: #f57c00;
    }
    
    .stat-card h3 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
        color: #1a237e;
    }
    
    .stat-card p {
        margin: 0.5rem 0 0 0;
        color: #5c6bc0;
        font-weight: 500;
    }
    
    /* Download buttons */
    .stDownloadButton > button {
        width: 100%;
        padding: 1rem 2rem;
        font-size: 1rem;
        font-weight: 600;
        border-radius: 12px;
        transition: all 0.3s ease;
    }
    
    .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    
    /* Info boxes */
    .info-box {
        background: #e3f2fd;
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #1976d2;
    }
    
    .info-box.success {
        background: #e8f5e9;
        border-left-color: #2e7d32;
    }
    
    .info-box.warning {
        background: #fff3e0;
        border-left-color: #f57c00;
    }
    
    /* Progress container */
    .stProgress > div > div {
        background: linear-gradient(90deg, #3949ab 0%, #5c6bc0 100%);
        border-radius: 8px;
    }
    
    /* Remove Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Section headers */
    .section-header {
        font-size: 1.3rem;
        font-weight: 600;
        color: #1a237e;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e8eaf6;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>📄 Kataster-Sorter</h1>
    <p>Automatische Sortierung von Liegenschaftskataster-Auszügen nach Fortführungsfallnummer und Grundbuchblatt</p>
</div>
""", unsafe_allow_html=True)

# Main content
st.markdown('<div class="section-header">📤 PDF hochladen</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "PDF-Datei hier ablegen oder klicken zum Auswählen",
    type=["pdf"],
    help="Laden Sie einen Kataster-Auszug als PDF hoch."
)

# Processing
if uploaded_file is not None:
    st.markdown('<div class="section-header">⚙️ Verarbeitung</div>', unsafe_allow_html=True)
    
    with st.status("PDF wird verarbeitet...", expanded=True) as status:
        st.write("📖 Lese PDF-Datei...")
        progress = st.progress(0)
        
        try:
            # Process the PDF
            sorter = KatasterSorter()
            
            st.write("🔍 Extrahiere Seitendaten...")
            progress.progress(25)
            
            st.write("📦 Gruppiere nach Fortführungsfallnummer...")
            progress.progress(50)
            
            st.write("📊 Analysiere Pakete...")
            progress.progress(75)
            
            # Actually process
            result = sorter.process(uploaded_file)
            
            st.write("✅ Generiere sortierte PDFs...")
            progress.progress(100)
            
            status.update(label="✅ Verarbeitung abgeschlossen!", state="complete", expanded=False)
            
        except Exception as e:
            status.update(label="❌ Fehler bei der Verarbeitung", state="error")
            st.error(f"Fehler: {str(e)}")
            st.stop()
    
    # Results section
    st.markdown('<div class="section-header">📊 Ergebnis</div>', unsafe_allow_html=True)
    
    # Stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="stat-card primary">
            <h3>{result['total_pages']}</h3>
            <p>Seiten gesamt</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-card success">
            <h3>{result['standard_count']}</h3>
            <p>Standard-Pakete</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-card warning">
            <h3>{result['sonderfall_count']}</h3>
            <p>Sonderfälle</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Download section
    st.markdown('<div class="section-header">💾 Download</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if result['standard_pdf']:
            st.download_button(
                label="📥 Sortierte_Akten.pdf herunterladen",
                data=result['standard_pdf'],
                file_name="Sortierte_Akten.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
            st.caption(f"Enthält {result['standard_count']} Pakete, sortiert nach Grundbuchblatt")
        else:
            st.info("Keine Standard-Pakete gefunden.")
    
    with col2:
        if result['sonderfall_pdf']:
            st.download_button(
                label="⚠️ Sonderfaelle_Pruefen.pdf herunterladen",
                data=result['sonderfall_pdf'],
                file_name="Sonderfaelle_Pruefen.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            st.caption(f"Enthält {result['sonderfall_count']} Pakete zur manuellen Prüfung")
        else:
            st.success("🎉 Keine Sonderfälle gefunden!")

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #9e9e9e; font-size: 0.9rem;'>"
    "Kataster-Sorter • Automatische PDF-Sortierung für Liegenschaftskataster"
    "</p>",
    unsafe_allow_html=True
)
