import streamlit as st
import subprocess
import os
import uuid
from pathlib import Path
import shutil
import base64
import mimetypes

# --- Streamlit App Config ---
st.set_page_config(layout="wide", page_title="セミナーポスター自動生成")

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
    "ブルー/イエロー (デフォルト)": {
        "header_bg": "linear-gradient(135deg, #003f7f 0%,rgb(0, 120, 212) 100%)",
        "info_bg": "linear-gradient(135deg, #ffd700 0%,hsl(51, 98.50%, 73.90%) 100%)",
        "info_border": "#f0c814",
        "info_shadow": "rgba(255, 215, 0, 0.3)",
        "main_text": "#003f7f",
    },
    "グリーン/オレンジ": {
        "header_bg": "linear-gradient(135deg, #005a32 0%, #1e8449 100%)",
        "info_bg": "linear-gradient(135deg, #f39c12 0%, #e67e22 100%)",
        "info_border": "#d35400",
        "info_shadow": "rgba(243, 156, 18, 0.3)",
        "main_text": "#005a32",
    },
    "パープル/ミント": {
        "header_bg": "linear-gradient(135deg, #4a148c 0%, #8e44ad 100%)",
        "info_bg": "linear-gradient(135deg, #a7ffeb 0%, #64ffda 100%)",
        "info_border": "#1de9b6",
        "info_shadow": "rgba(100, 255, 218, 0.3)",
        "main_text": "#4a148c",
    },
    "モノクローム": {
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
    local_marp_path = os.path.join(home, ".local", "bin", "marp")

    if os.path.exists(local_marp_path):
        return local_marp_path

    # Fallback for local development
    if shutil.which("marp"):
        return shutil.which("marp")

    st.warning("Marp CLIが見つかりません。初回起動時に自動インストールを行います...")
    with st.spinner("Marp CLIをインストール中です... (初回のみ数分かかることがあります)"):
        try:
            command = "npm install --prefix ~/.local @marp-team/marp-cli@1.7.1"
            subprocess.run(command, shell=True, check=True, capture_output=True, text=True, encoding='utf-8')
            st.success("Marp CLIのインストールが完了しました！ページを再読み込みします。")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Marp CLIのインストールに失敗しました。エラー: {e}")
            if hasattr(e, 'stderr'):
                st.code(e.stderr)
            return None

MARP_PATH = setup_marp_cli()

# --- Helper function for dynamic font size ---
def get_dynamic_font_size(text, base_size=1.5, min_size=0.8, shrink_factor=12):
    """Reduces font size for longer text to prevent line breaks."""
    if len(text) > shrink_factor:
        reduction = (len(text) - shrink_factor) * 0.1
        return max(min_size, base_size - reduction)
    return base_size

# --- Markdown Generation ---
def generate_markdown(
    colloquium_name, title, photo_path, speaker_name, affiliation,
    date_time, location, abstract, colors, abstract_font_size, abstract_height,
    title_font_size, speaker_font_size
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
    font-size: {speaker_font_size}em; font-weight: 700; color: {colors['main_text']}; margin-bottom: 8px;
    white-space: nowrap;
  }}
  .affiliation {{
    font-size: 1.0em; color: #666; line-height: 1.4; font-weight: 400;
  }}
  .right-panel {{ flex: 1; display: flex; flex-direction: column; gap: 30px; }}
  .info-section {{
    background: {colors['info_bg']};
    padding: 25px; border-radius: 12px;
    box-shadow: 0 4px 12px {colors['info_shadow']};
    border: 2px solid {colors['info_border']};
  }}
  .event-info {{
    display: grid; grid-template-columns: auto 1fr; gap: 15px 25px; font-size: 0.9em;
  }}
  .info-label {{ font-weight: 700; color: {colors['main_text']}; }}
  .info-value {{ color: {colors['main_text']}; font-weight: 500; }}
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
    <img src="{photo_path}" alt="講演者写真" class="speaker-photo">
    <div class="speaker-info">
      <div class="speaker-name">{speaker_name}</div>
      <div class="affiliation">{affiliation_html}</div>
    </div>
  </div>
  <div class="right-panel">
    <div class="info-section">
      <div class="event-info">
        <div class="info-label">日時：</div> <div class="info-value">{date_time}</div>
        <div class="info-label">場所：</div> <div class="info-value">{location}</div>
      </div>
    </div>
    <div class="abstract">
      <div class="abstract-title">講演概要</div>
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
st.title("セミナーポスター自動生成ツール")

if not MARP_PATH:
    st.error("Marp CLIのセットアップが完了していません。上記のエラーメッセージをご確認ください。")
    st.stop()

# --- Sidebar Inputs ---
with st.sidebar:
    st.header("ポスター情報入力")
    colloquium_name = st.text_input("コロキウム名", "物理学教室コロキウム")
    title = st.text_input("講演タイトル", "高分子ゲルの精密な物理学")
    speaker_name = st.text_input("講演者名", "酒井 崇匡 氏")
    affiliation = st.text_area("所属", "東京大学大学院\n理学系研究科")
    date_time = st.text_input("日時", "2025年6月20日（金）17:00-18:30")
    location = st.text_input("場所", "小柴ホール")
    uploaded_photo = st.file_uploader("講演者の写真", type=['jpg', 'png', 'jpeg'])
    abstract = st.text_area("講演概要", "ハイドロゲル（以下ゲルと略）は、多量の水で膨潤した高分子ネットワークであり...（以下略）", height=200)

    st.header("デザイン設定")
    selected_theme_name = st.selectbox("カラーテーマ", COLOR_THEMES.keys())
    title_font_size = st.slider("タイトルのフォントサイズ", 1.0, 4.0, 2.8, 0.1)
    abstract_font_size = st.slider("概要のフォントサイズ", 0.5, 1.0, 0.65, 0.05)
    abstract_height = st.slider("概要ボックスの高さ (px)", 100, 500, 250, 10)

# --- Image Handling ---
if uploaded_photo:
    image_bytes = uploaded_photo.getvalue()
    mime_type = mimetypes.guess_type(uploaded_photo.name)[0]
    photo_display_path = f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode()}"
else:
    placeholder_svg = """<svg width="250" height="250" viewBox="0 0 250 250" xmlns="http://www.w3.org/2000/svg"><rect width="100%" height="100%" fill="#e9ecef"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="sans-serif" font-size="20" fill="#6c757d">写真なし</text></svg>"""
    photo_display_path = f"data:image/svg+xml;base64,{base64.b64encode(placeholder_svg.encode()).decode()}"

# --- Dynamic Font Sizing ---
speaker_font_size = get_dynamic_font_size(speaker_name)

# --- Markdown and Preview Generation ---
markdown_content = generate_markdown(
    colloquium_name, title, photo_display_path, speaker_name, affiliation,
    date_time, location, abstract, COLOR_THEMES[selected_theme_name], 
    abstract_font_size, abstract_height, title_font_size, speaker_font_size
)

st.subheader("リアルタイムプレビュー")
md_path = OUTPUT_DIR / "preview.md"
html_path = OUTPUT_DIR / "preview.html"
md_path.write_text(markdown_content, encoding="utf-8")

try:
    cmd = [MARP_PATH, str(md_path), "-o", str(html_path), "--html", "--allow-local-files"]
    subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8')
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    st.components.v1.html(html_content, height=550, scrolling=False)
except Exception as e:
    st.error("プレビューの生成に失敗しました。")
    if hasattr(e, 'stderr'):
        st.code(e.stderr)

# --- PDF Download ---
st.header("PDF生成")
if uploaded_photo:
    pdf_path = OUTPUT_DIR / "poster.pdf"
    try:
        cmd = [MARP_PATH, str(md_path), "-o", str(pdf_path), "--pdf", "--allow-local-files"]
        subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8')
        with open(pdf_path, "rb") as f:
            st.download_button(
                label="ポスターPDFをダウンロード",
                data=f.read(),
                file_name="colloquium_poster.pdf",
                mime="application/pdf",
                type="primary"
            )
    except Exception as e:
        st.error("PDFの生成に失敗しました。")
        if hasattr(e, 'stderr'):
            st.code(e.stderr)
else:
    st.warning("PDFを生成・ダウンロードするには、講演者の写真をアップロードしてください。")
