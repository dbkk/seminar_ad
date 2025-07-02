import streamlit as st
import subprocess
import os
import uuid
from pathlib import Path
import shutil
import base64
import mimetypes

# --- Streamlit App Config ---
st.set_page_config(layout="wide", page_title="Seminar Poster Generator")

# --- Custom CSS for Spacing ---
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
        }
        [data-testid="stSidebar"] .st-emotion-cache-10oheav {
            padding-top: 2rem;
        }
    </style>
""", unsafe_allow_html=True)

# --- Constants and Setup ---
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

COLOR_THEMES = {
    "Blue/Yellow (Default)": {
        "header_bg": "linear-gradient(135deg, #003f7f 0%,rgb(0, 120, 212) 100%)",
        "info_bg": "linear-gradient(135deg, #ffd700 0%,hsl(51, 98.50%, 73.90%) 100%)",
        "info_border": "#f0c814",
        "info_shadow": "rgba(255, 215, 0, 0.3)",
        "main_text": "#003f7f",
    },
    "Green/Orange": {
        "header_bg": "linear-gradient(135deg, #005a32 0%, #1e8449 100%)",
        "info_bg": "linear-gradient(135deg, #f39c12 0%, #e67e22 100%)",
        "info_border": "#d35400",
        "info_shadow": "rgba(243, 156, 18, 0.3)",
        "main_text": "#005a32",
    },
    "Purple/Mint": {
        "header_bg": "linear-gradient(135deg, #4a148c 0%, #8e44ad 100%)",
        "info_bg": "linear-gradient(135deg, #a7ffeb 0%, #64ffda 100%)",
        "info_border": "#1de9b6",
        "info_shadow": "rgba(100, 255, 218, 0.3)",
        "main_text": "#4a148c",
    },
    "Monochrome": {
        "header_bg": "linear-gradient(135deg, #2c3e50 0%, #34495e 100%)",
        "info_bg": "linear-gradient(135deg, #ecf0f1 0%, #bdc3c7 100%)",
        "info_border": "#95a5a6",
        "info_shadow": "rgba(189, 195, 199, 0.3)",
        "main_text": "#2c3e50",
    }
}

# --- Marp CLI Setup for Streamlit Cloud ---
def setup_marp_cli():
    """
    Robustly installs and finds Marp CLI for Streamlit Cloud environments.
    """
    home = os.path.expanduser("~")
    marp_script_path = os.path.join(home, ".local", "lib", "node_modules", "@marp-team", "marp-cli", "marp-cli.js")

    if os.path.exists(marp_script_path):
        return ["node", marp_script_path]

    st.warning("Marp CLI not found. Installing automatically...")
    with st.spinner("Installing Marp CLI... (This may take a moment on first run)"):
        try:
            command = "npm install --prefix ~/.local @marp-team/marp-cli@1.7.1"
            subprocess.run(command, shell=True, check=True, capture_output=True, text=True, encoding='utf-8')
            
            if os.path.exists(marp_script_path):
                st.success("Marp CLI installed successfully! Rerunning page...")
                st.experimental_rerun()
            else:
                st.error("Marp CLI installation succeeded, but the executable could not be found.")
                return None
        except Exception as e:
            st.error(f"Failed to install Marp CLI. Error: {e}")
            if hasattr(e, 'stderr'):
                st.code(e.stderr)
            return None

MARP_PATH = setup_marp_cli()

# --- Markdown Generation ---
def generate_markdown(
    colloquium_name, title, photo_path, speaker_name, affiliation,
    date_time, location, abstract, colors, abstract_font_size, abstract_height,
    title_font_size
):
    style_css = f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap');
  section {{
    display: flex; flex-direction: column; padding: 0; 
    font-family: 'Noto Sans JP', sans-serif;
    background: linear-gradient(135deg, #f1f3f6 0%, #e8eef4 100%);
    overflow: hidden;
  }}
  .header-container {{
    background: {colors['header_bg']};
    padding: 50px 60px 30px 60px; margin-bottom: 0px;
    transform: skewY(-3deg); position: relative; z-index: 1; margin-top: -30px;
  }}
  .colloquium-name {{
    position: absolute; top: 35px; left: 970px; font-size: 1em;
    font-weight: 500; color: rgba(255, 255, 255, 0.8); transform: skewY(3deg);
  }}
  .title {{
    font-size: {title_font_size}em; font-weight: 900; color: #ffffff; text-align: center;
    line-height: 1.3; text-shadow: 0 2px 5px rgba(0, 0, 0, 0.25);
    transform: skewY(3deg); margin-bottom: 0; white-space: nowrap;
  }}
  .main-content {{
    display: flex; flex-direction: row; flex: 1; gap: 50px; padding: 0 40px;
  }}
  .left-panel {{
    flex: 0 0 280px; display: flex; flex-direction: column; align-items: center;
  }}
  .speaker-photo {{
    width: 250px; height: 250px; border-radius: 50%; object-fit: cover;
    object-position: center;
    box-shadow: 0 10px 30px rgba(0, 63, 127, 0.25);
    border: 5px solid #ffffff; margin-bottom: 25px; position: relative; z-index: 2;
  }}
  .speaker-info {{
    text-align: center; background-color: white; padding: 20px;
    border-radius: 12px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); width: 100%;
  }}
  .speaker-name {{
    font-size: 1.5em; font-weight: 700; color: {colors['main_text']}; margin-bottom: 8px;
    white-space: nowrap;
  }}
  .affiliation {{
    font-size: 1.0em; color: #666; line-height: 1.4; font-weight: 400;
  }}
  .abstract {{
    background-color: white; padding: 25px; border-radius: 12px;
    box-shadow: 0 4px 12px rgba(1, 36, 72, 0.15);
    border-left: 4px solid {colors['main_text']};
    height: {abstract_height}px;
    overflow-y: auto;
  }}
  .abstract-title {{
    font-size: 0.8em; color: {colors['main_text']}; margin-bottom: 18px;
    font-weight: 700; border-bottom: 2px solid {colors['main_text']}; padding-bottom: 8px;
  }}
  .abstract p {{
    font-size: {abstract_font_size}em; line-height: 1.6; color: #333; text-align: justify;
    margin-bottom: 12px; font-weight: 400;
  }}
</style>
"""
    affiliation_html = affiliation.replace('\n', '<br>')
    abstract_html = f"<p>{' '.join(abstract.strip().splitlines())}</p>"
    content_html = f"""
<div class="header-container">
  <div class="colloquium-name">{colloquium_name}</div>
  <div class="title">{title}</div>
</div>
<div class="main-content">
  <div class="left-panel">
    <img src="{photo_path}" alt="Speaker Photo" class="speaker-photo">
    <div class="speaker-info">
      <div class="speaker-name">{speaker_name}</div>
      <div class="affiliation">{affiliation_html}</div>
    </div>
  </div>
  <div class="right-panel">
    <div class="info-section">
      <div class="event-info">
        <div class="info-label">Date:</div> <div class="info-value">{date_time}</div>
        <div class="info-label">Location:</div> <div class="info-value">{location}</div>
      </div>
    </div>
    <div class="abstract">
      <div class="abstract-title">Abstract</div>
      {abstract_html}
    </div>
  </div>
</div>
"""
    return f"""---
marp: true
theme: default
paginate: false
size: 16:9
---
{style_css}
{content_html}
"""

# --- Main App ---
st.title("Seminar Poster Generator")

if not MARP_PATH:
    st.error("Marp CLI setup is incomplete. Please check the error messages above.")
    st.stop()

# --- Sidebar Inputs ---
with st.sidebar:
    st.header("Poster Information")
    colloquium_name = st.text_input("Colloquium Name", "Physics Dept. Colloquium")
    title = st.text_input("Presentation Title", "The Precise Physics of Polymer Gels")
    speaker_name = st.text_input("Speaker Name", "Dr. Takamasa Sakai")
    affiliation = st.text_area("Affiliation", "The University of Tokyo\nGraduate School of Engineering")
    date_time = st.text_input("Date & Time", "June 20, 2025, 17:00-18:30")
    location = st.text_input("Location", "Koshiba Hall")
    uploaded_photo = st.file_uploader("Speaker's Photo", type=['jpg', 'png', 'jpeg'])
    abstract = st.text_area("Abstract", "A hydrogel is a polymer network swollen with a large amount of water...", height=200)

    st.header("Design Settings")
    selected_theme_name = st.selectbox("Color Theme", COLOR_THEMES.keys())
    title_font_size = st.slider("Title Font Size", 1.0, 4.0, 2.8, 0.1)
    abstract_font_size = st.slider("Abstract Font Size", 0.5, 1.0, 0.65, 0.05)
    abstract_height = st.slider("Abstract Box Height (px)", 100, 500, 250, 10)

# --- Image Handling ---
if uploaded_photo:
    image_bytes = uploaded_photo.getvalue()
    mime_type = mimetypes.guess_type(uploaded_photo.name)[0]
    photo_display_path = f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode()}"
else:
    placeholder_svg = """<svg width="250" height="250" viewBox="0 0 250 250" xmlns="http://www.w3.org/2000/svg"><rect width="100%" height="100%" fill="#e9ecef"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="sans-serif" font-size="20" fill="#6c757d">No Photo</text></svg>"""
    photo_display_path = f"data:image/svg+xml;base64,{base64.b64encode(placeholder_svg.encode()).decode()}"

# --- Markdown and Preview Generation ---
markdown_content = generate_markdown(
    colloquium_name, title, photo_display_path, speaker_name, affiliation,
    date_time, location, abstract, COLOR_THEMES[selected_theme_name], 
    abstract_font_size, abstract_height, title_font_size
)

st.subheader("Live Preview")
md_path = OUTPUT_DIR / "preview.md"
html_path = OUTPUT_DIR / "preview.html"
md_path.write_text(markdown_content, encoding="utf-8")

try:
    cmd = MARP_PATH + [str(md_path), "-o", str(html_path), "--html", "--allow-local-files"]
    subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8')
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    st.components.v1.html(html_content, height=550, scrolling=False)
except Exception as e:
    st.error("Failed to generate preview.")
    if hasattr(e, 'stderr'):
        st.code(e.stderr)

# --- PDF Download ---
st.header("Generate PDF")
if uploaded_photo:
    pdf_path = OUTPUT_DIR / "poster.pdf"
    try:
        cmd = MARP_PATH + [str(md_path), "-o", str(pdf_path), "--pdf", "--allow-local-files"]
        subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8')
        with open(pdf_path, "rb") as f:
            st.download_button(
                label="Download Poster PDF",
                data=f.read(),
                file_name="colloquium_poster.pdf",
                mime="application/pdf",
                type="primary"
            )
    except Exception as e:
        st.error("Failed to generate PDF.")
        if hasattr(e, 'stderr'):
            st.code(e.stderr)
else:
    st.warning("Please upload a photo to generate and download the PDF.")
