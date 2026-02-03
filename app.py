import os
import re
import io
import json
import base64
import random
import zipfile
import tempfile
import pathlib
import datetime
import traceback
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple, Union

import streamlit as st
import pandas as pd
import yaml
from rapidfuzz import fuzz
from PyPDF2 import PdfReader, PdfWriter

import plotly.express as px

from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image

# ============================================================
# Constants / Files
# ============================================================
DEFAULTSETS_PATH = "defaultsets.json"
AGENTS_PATH = "agents.yaml"
SKILL_PATH = "SKILL.md"

CORAL = "#FF7F50"

KEY_ENV_CANDIDATES = {
    "OPENAI_API_KEY": ["OPENAI_API_KEY"],
    "GEMINI_API_KEY": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
    "ANTHROPIC_API_KEY": ["ANTHROPIC_API_KEY"],
    "XAI_API_KEY": ["XAI_API_KEY"],
}

OPENAI_MODELS = ["gpt-4o-mini", "gpt-4.1-mini"]
GEMINI_MODELS = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-3-flash-preview"]
ANTHROPIC_MODELS = ["claude-3-5-sonnet-latest", "claude-3-5-haiku-latest"]
XAI_MODELS = ["grok-4-fast-reasoning", "grok-3-mini"]

# ============================================================
# i18n
# ============================================================
STRINGS = {
    "en": {
        "app_title": "FDA 510(k) Review Studio — Regulatory Command Center",
        "nav_dashboard": "Dashboard",
        "nav_command": "Command Center",
        "nav_datasets": "Dataset Studio",
        "nav_agents": "Agent Studio",
        "nav_factory": "Factory (Batch PDFs)",
        "nav_notes": "AI Note Keeper",
        "settings": "Settings",
        "theme": "Theme",
        "language": "Language",
        "style": "Painter Style",
        "jackpot": "Jackpot",
        "style_ai_pick": "AI Magic: Pick Style",
        "light": "Light",
        "dark": "Dark",
        "global_search": "Global Search (device, K#, UDI, product code...)",
        "search_placeholder": "Try: 'Infusion Pump', 'K240123', 'Latex', 'Battery'",
        "search": "Search",
        "smart_suggestions": "Smart Suggestions",
        "kpi_loaded": "Loaded records",
        "status": "Status",
        "api_keys": "API Keys",
        "managed_by_env": "Authenticated via Environment",
        "missing_key": "Missing — enter on this page",
        "session_key": "Session",
        "datasets": "Datasets",
        "dataset_source": "Dataset Source",
        "use_default": "Use default mock datasets",
        "paste": "Paste",
        "upload": "Upload",
        "parse_load": "Parse & Load",
        "standardize": "Standardize",
        "preview": "Preview",
        "standardization_report": "Standardization report",
        "loaded_rows": "Loaded rows",
        "reset_defaults": "Reset to default datasets",
        "download_json": "Download JSON",
        "download_csv": "Download CSV",
        "dashboard": "Interactive Dashboard",
        "timeline": "Timeline",
        "distribution": "Distribution",
        "results": "Results",
        "all": "All",
        "workspace": "Document Operating Room",
        "source_material": "Source (PDF/Text)",
        "intelligence": "Intelligence (Agents/Markdown)",
        "upload_pdf": "Upload PDF",
        "paste_text": "Paste text",
        "input_mode": "Input mode",
        "pdf": "PDF",
        "text": "Text",
        "trim_ocr": "Trim & OCR",
        "page_ranges": "Page ranges (e.g., 1-3, 5)",
        "render_preview": "Render PDF preview",
        "trim_extract": "Trim + Extract text layer",
        "ocr_engine": "OCR engine",
        "extract_text": "Extract text (PyPDF2)",
        "local_ocr": "Local OCR (Tesseract)",
        "vision_ocr": "Cloud Vision OCR (OpenAI/Gemini)",
        "run_ocr": "Run OCR",
        "download_trimmed": "Download trimmed PDF",
        "raw_text": "Raw extracted text",
        "ocr_text": "OCR text",
        "markdown_reconstruct": "Markdown Reconstruct",
        "apply": "Apply",
        "agent_pipeline": "Agent Pipeline",
        "agent": "Agent",
        "provider": "Provider",
        "model": "Model",
        "max_tokens": "Max tokens",
        "temperature": "Temperature",
        "system_prompt": "System prompt",
        "user_prompt": "User prompt",
        "input_source": "Agent input source",
        "use_last_output": "Use last edited output",
        "use_doc_text": "Use current document text (OCR preferred)",
        "execute": "Execute agent",
        "append_final": "Append output to Final Report",
        "final_report": "Final Report",
        "render": "Render",
        "markdown": "Markdown",
        "text_view": "Text",
        "edit_output_for_next": "Edit output used as input for next agent",
        "agent_runs": "Agent runs",
        "agent_yaml": "agents.yaml",
        "upload_yaml": "Upload YAML",
        "download_yaml": "Download YAML",
        "reset_agents": "Reset to default",
        "yaml_invalid": "YAML invalid",
        "yaml_loaded": "agents.yaml standardized & loaded",
        "agent_cards": "Agent Cards",
        "auto_standardize_llm": "Auto-standardize with LLM (optional)",
        "diff": "Diff",
        "factory": "Batch PDF Factory",
        "root_dir": "Root directory (optional, if accessible)",
        "upload_zip": "Upload ZIP containing PDFs",
        "scan": "Scan",
        "manifest": "Manifest",
        "trim_page1": "Trim first page",
        "summarize": "Summarize",
        "generate_toc": "Generate Master ToC",
        "set_as_current_doc": "Set Master ToC as current document",
        "note_keeper": "AI Note Keeper",
        "paste_note": "Paste text/markdown",
        "upload_note": "Upload TXT/MD/PDF",
        "ai_magics": "AI Magics",
        "run_magic": "Run Magic",
        "keywords": "Keywords",
        "keyword_colors": "Keyword Colors",
        "clear_session": "Clear session state",
        "danger_zone": "Danger Zone",
        "fuzzy_level": "Fuzzy level",
        "exact_match": "Exact match",
        "dataset_toggles": "Dataset toggles",
        "date_range": "Date range",
        "no_results": "No results",
        "select_to_filter": "Select chart area to filter (if supported)",
        "style_recommended": "Recommended style",
        "style_ai_help": "Use your current query / note / doc text as vibe signals to pick a painter style.",
        "run": "Run",
    },
    "zh-TW": {
        "app_title": "FDA 510(k) 審查工作室 — 法規指揮中心",
        "nav_dashboard": "儀表板",
        "nav_command": "指揮中心",
        "nav_datasets": "資料集工作室",
        "nav_agents": "代理工作室",
        "nav_factory": "工廠（批次 PDF）",
        "nav_notes": "AI 筆記整理",
        "settings": "設定",
        "theme": "主題",
        "language": "語言",
        "style": "畫家風格",
        "jackpot": "隨機開獎",
        "style_ai_pick": "AI 魔法：挑風格",
        "light": "亮色",
        "dark": "暗色",
        "global_search": "全域搜尋（裝置、K號、UDI、產品代碼…）",
        "search_placeholder": "試試：'Infusion Pump'、'K240123'、'Latex'、'Battery'",
        "search": "搜尋",
        "smart_suggestions": "智慧建議",
        "kpi_loaded": "已載入筆數",
        "status": "狀態",
        "api_keys": "API 金鑰",
        "managed_by_env": "由環境變數驗證",
        "missing_key": "未設定 — 請在網頁輸入",
        "session_key": "Session",
        "datasets": "資料集",
        "dataset_source": "資料來源",
        "use_default": "使用預設 mock 資料",
        "paste": "貼上",
        "upload": "上傳",
        "parse_load": "解析並載入",
        "standardize": "標準化",
        "preview": "預覽",
        "standardization_report": "標準化報告",
        "loaded_rows": "已載入筆數",
        "reset_defaults": "重置為預設資料集",
        "download_json": "下載 JSON",
        "download_csv": "下載 CSV",
        "dashboard": "互動儀表板",
        "timeline": "時間軸",
        "distribution": "分佈",
        "results": "結果",
        "all": "全部",
        "workspace": "文件手術室（Operating Room）",
        "source_material": "來源（PDF/文字）",
        "intelligence": "智慧區（Agents/Markdown）",
        "upload_pdf": "上傳 PDF",
        "paste_text": "貼上文字",
        "input_mode": "輸入模式",
        "pdf": "PDF",
        "text": "文字",
        "trim_ocr": "裁切與 OCR",
        "page_ranges": "頁碼範圍（例如 1-3, 5）",
        "render_preview": "顯示 PDF 預覽",
        "trim_extract": "裁切並擷取文字層",
        "ocr_engine": "OCR 引擎",
        "extract_text": "擷取文字（PyPDF2）",
        "local_ocr": "本機 OCR（Tesseract）",
        "vision_ocr": "雲端視覺 OCR（OpenAI/Gemini）",
        "run_ocr": "執行 OCR",
        "download_trimmed": "下載裁切 PDF",
        "raw_text": "原始擷取文字",
        "ocr_text": "OCR 文字",
        "markdown_reconstruct": "Markdown 重建",
        "apply": "套用",
        "agent_pipeline": "代理流程（Pipeline）",
        "agent": "代理",
        "provider": "供應商",
        "model": "模型",
        "max_tokens": "最大 tokens",
        "temperature": "溫度",
        "system_prompt": "系統提示詞",
        "user_prompt": "使用者提示詞",
        "input_source": "代理輸入來源",
        "use_last_output": "使用上次已編修輸出",
        "use_doc_text": "使用目前文件文字（優先 OCR）",
        "execute": "執行代理",
        "append_final": "附加到最終報告",
        "final_report": "最終報告",
        "render": "呈現",
        "markdown": "Markdown",
        "text_view": "文字",
        "edit_output_for_next": "編修輸出（作為下一代理輸入）",
        "agent_runs": "代理執行次數",
        "agent_yaml": "agents.yaml",
        "upload_yaml": "上傳 YAML",
        "download_yaml": "下載 YAML",
        "reset_agents": "重置為預設",
        "yaml_invalid": "YAML 無效",
        "yaml_loaded": "agents.yaml 已標準化並載入",
        "agent_cards": "代理卡片",
        "auto_standardize_llm": "使用 LLM 自動標準化（可選）",
        "diff": "差異（Diff）",
        "factory": "批次 PDF 工廠",
        "root_dir": "根目錄（若可存取）",
        "upload_zip": "上傳包含 PDF 的 ZIP",
        "scan": "掃描",
        "manifest": "清單",
        "trim_page1": "裁切第一頁",
        "summarize": "摘要",
        "generate_toc": "產生 Master ToC",
        "set_as_current_doc": "將 Master ToC 設為目前文件",
        "note_keeper": "AI 筆記整理",
        "paste_note": "貼上文字/Markdown",
        "upload_note": "上傳 TXT/MD/PDF",
        "ai_magics": "AI 魔法",
        "run_magic": "執行魔法",
        "keywords": "關鍵詞",
        "keyword_colors": "關鍵詞上色",
        "clear_session": "清除 session 狀態",
        "danger_zone": "危險區",
        "fuzzy_level": "模糊程度",
        "exact_match": "完全匹配",
        "dataset_toggles": "資料集開關",
        "date_range": "日期範圍",
        "no_results": "沒有結果",
        "select_to_filter": "選取圖表區域以篩選（若支援）",
        "style_recommended": "建議風格",
        "style_ai_help": "使用目前查詢 / 筆記 / 文件文字作為氛圍信號，交給 AI 挑一個畫家風格。",
        "run": "執行",
    },
}


def t(lang: str, key: str) -> str:
    return STRINGS.get(lang, STRINGS["en"]).get(key, key)


# ============================================================
# Painter styles (20)
# ============================================================
PAINTER_STYLES = [
    {"id": "monet", "name": "Claude Monet", "accent": "#7FB3D5"},
    {"id": "vangogh", "name": "Vincent van Gogh", "accent": "#F4D03F"},
    {"id": "picasso", "name": "Pablo Picasso", "accent": "#AF7AC5"},
    {"id": "rembrandt", "name": "Rembrandt", "accent": "#D4AC0D"},
    {"id": "vermeer", "name": "Johannes Vermeer", "accent": "#5DADE2"},
    {"id": "hokusai", "name": "Hokusai", "accent": "#48C9B0"},
    {"id": "klimt", "name": "Gustav Klimt", "accent": "#F5CBA7"},
    {"id": "kahlo", "name": "Frida Kahlo", "accent": "#EC7063"},
    {"id": "pollock", "name": "Jackson Pollock", "accent": "#58D68D"},
    {"id": "cezanne", "name": "Paul Cézanne", "accent": "#F0B27A"},
    {"id": "turner", "name": "J.M.W. Turner", "accent": "#F5B041"},
    {"id": "matisse", "name": "Henri Matisse", "accent": "#EB984E"},
    {"id": "dali", "name": "Salvador Dalí", "accent": "#85C1E9"},
    {"id": "warhol", "name": "Andy Warhol", "accent": "#FF5DA2"},
    {"id": "sargent", "name": "John Singer Sargent", "accent": "#AED6F1"},
    {"id": "rothko", "name": "Mark Rothko", "accent": "#CD6155"},
    {"id": "caravaggio", "name": "Caravaggio", "accent": "#A04000"},
    {"id": "okeeffe", "name": "Georgia O’Keeffe", "accent": "#F1948A"},
    {"id": "seurat", "name": "Georges Seurat", "accent": "#76D7C4"},
    {"id": "basquiat", "name": "Jean-Michel Basquiat", "accent": "#F7DC6F"},
]


def jackpot_style():
    return random.choice(PAINTER_STYLES)


# ============================================================
# WOW CSS: Glassmorphism + Coral + Painter accent
# ============================================================
def inject_css(theme: str, painter_accent: str, coral: str = CORAL):
    if theme == "light":
        bg = "#F6F7FB"
        fg = "#0B1020"
        card = "rgba(10, 16, 32, 0.05)"
        border = "rgba(10, 16, 32, 0.12)"
        shadow = "rgba(10, 16, 32, 0.12)"
    else:
        bg = "#0B1020"
        fg = "#EAF0FF"
        card = "rgba(255,255,255,0.06)"
        border = "rgba(255,255,255,0.10)"
        shadow = "rgba(0,0,0,0.40)"

    return f"""
    <style>
      :root {{
        --bg: {bg};
        --fg: {fg};
        --card: {card};
        --border: {border};
        --accent: {painter_accent};
        --coral: {coral};
        --ok: #2ECC71;
        --warn: #F1C40F;
        --bad: #E74C3C;
        --shadow: {shadow};
      }}

      .stApp {{
        background:
          radial-gradient(1200px 600px at 20% 0%, rgba(255,127,80,0.14), transparent 60%),
          radial-gradient(900px 500px at 80% 10%, rgba(0,200,255,0.12), transparent 55%),
          var(--bg);
        color: var(--fg);
      }}

      .wow-card {{
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 14px 14px;
        backdrop-filter: blur(12px);
        box-shadow: 0 18px 55px var(--shadow);
      }}

      .wow-mini {{
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 10px 12px;
        backdrop-filter: blur(12px);
      }}

      .chip {{
        display:inline-flex;
        align-items:center;
        gap:8px;
        padding: 6px 10px;
        margin: 0 8px 8px 0;
        border-radius: 999px;
        border: 1px solid var(--border);
        background: var(--card);
        font-size: 12px;
        line-height: 1;
      }}
      .dot {{
        width: 9px; height: 9px; border-radius: 99px;
        background: var(--accent);
        box-shadow: 0 0 0 3px rgba(255,255,255,0.06);
      }}

      .coral {{
        color: var(--coral);
        font-weight: 800;
      }}

      .editor-frame {{
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 12px;
        background: rgba(0,0,0,0.00);
      }}

      div[data-testid="stDataFrame"] {{
        border: 1px solid var(--border);
        border-radius: 14px;
        overflow: hidden;
      }}

      .fab {{
        position: fixed;
        bottom: 20px;
        right: 22px;
        z-index: 9999;
        border-radius: 999px;
        padding: 12px 16px;
        background: linear-gradient(135deg, var(--accent), var(--coral));
        color: white;
        font-weight: 900;
        border: 0px;
        box-shadow: 0 22px 55px rgba(0,0,0,0.45);
        letter-spacing: 0.5px;
      }}
      .fab-sub {{
        position: fixed;
        bottom: 68px;
        right: 22px;
        z-index: 9999;
        font-size: 12px;
        padding: 8px 10px;
        border-radius: 12px;
        background: var(--card);
        border: 1px solid var(--border);
        color: var(--fg);
        backdrop-filter: blur(10px);
      }}
      h1, h2, h3, h4 {{ margin-top: 0.2rem; }}
      a {{ color: var(--accent) !important; }}
    </style>
    """


# ============================================================
# Coral highlighting (regulatory ontology)
# ============================================================
DEFAULT_ONTOLOGY = [
    "predicate", "predicate device",
    "warning", "contraindication",
    "sterile", "biocompatibility",
    "malfunction", "recall",
    "mri", "latex",
    "serious injury", "death",
    "cybersecurity", "software",
    "failure", "misfire",
    "udi", "510(k)", "k-number", "k number",
    "intended use", "class iii", "class ii", "class i",
]


def coral_highlight(text: str, keywords: Optional[List[str]] = None) -> str:
    if not text:
        return ""
    kws = keywords or DEFAULT_ONTOLOGY
    kws = sorted(set([k.strip() for k in kws if k and k.strip()]), key=len, reverse=True)
    out = text

    def repl(m):
        w = m.group(0)
        return f'<span class="coral"><b>{w}</b></span>'

    for k in kws:
        pattern = re.compile(rf"(?i)({re.escape(k)})")
        out = pattern.sub(repl, out)
    return out


def safe_md_render(md: str) -> None:
    st.markdown(f"<div class='wow-card editor-frame'>{coral_highlight(md)}</div>", unsafe_allow_html=True)


# ============================================================
# Defaultsets JSON: ensure + load
# ============================================================
def ensure_defaultsets_json():
    if os.path.exists(DEFAULTSETS_PATH):
        return
    fallback = {"version": "1.0", "datasets": {"510k": [], "adr": [], "gudid": [], "recall": []}}
    with open(DEFAULTSETS_PATH, "w", encoding="utf-8") as f:
        json.dump(fallback, f, ensure_ascii=False, indent=2)


def load_defaultsets_json() -> Dict[str, Any]:
    ensure_defaultsets_json()
    with open(DEFAULTSETS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# Dataset parsing + standardization
# ============================================================
CANON = {
    "510k": [
        "k_number", "decision_date", "decision", "device_name", "applicant", "manufacturer_name", "product_code",
        "regulation_number", "device_class", "panel", "review_advisory_committee", "predicate_k_numbers", "summary",
    ],
    "adr": [
        "adverse_event_id", "report_date", "event_type", "patient_outcome", "device_problem", "manufacturer_name",
        "brand_name", "product_code", "device_class", "udi_di", "recall_number_link", "narrative",
    ],
    "gudid": [
        "primary_di", "udi_di", "device_description", "device_class", "manufacturer_name", "brand_name", "product_code",
        "gmdn_term", "mri_safety", "sterile", "single_use", "implantable", "contains_nrl", "version_or_model_number",
        "catalog_number", "record_status", "publish_date", "company_contact_email", "company_contact_phone",
        "company_state", "company_country",
    ],
    "recall": [
        "recall_number", "recall_class", "event_date", "termination_date", "status", "firm_name", "manufacturer_name",
        "product_description", "product_code", "code_info", "reason_for_recall", "distribution_pattern",
        "quantity_in_commerce", "country", "state",
    ],
}

SYNONYMS = {
    "510k": {
        "k_number": ["k_number", "knumber", "k", "k_no", "k#", "submission_number"],
        "decision_date": ["decision_date", "clearance_date", "date"],
        "decision": ["decision", "decision_code", "determination", "se_decision"],
        "device_name": ["device_name", "device", "name", "device_title", "device title"],
        "applicant": ["applicant", "submitter", "company", "applicant_name"],
        "manufacturer_name": ["manufacturer_name", "manufacturer", "mfr", "firm_name"],
        "product_code": ["product_code", "productcode", "procode", "code"],
        "regulation_number": ["regulation_number", "regulation", "21cfr", "cfr"],
        "device_class": ["device_class", "class"],
        "panel": ["panel", "medical_specialty", "review_panel"],
        "review_advisory_committee": ["review_advisory_committee", "committee"],
        "predicate_k_numbers": ["predicate_k_numbers", "predicates", "predicate", "predicate_k", "predicate_knumbers"],
        "summary": ["summary", "description", "clearance_summary", "decision_summary"],
    },
    "adr": {
        "adverse_event_id": ["adverse_event_id", "mdr_id", "event_id", "report_id", "mdr_report_key"],
        "report_date": ["report_date", "date"],
        "event_type": ["event_type", "type"],
        "patient_outcome": ["patient_outcome", "outcome"],
        "device_problem": ["device_problem", "problem", "issue", "device_problem_code"],
        "manufacturer_name": ["manufacturer_name", "manufacturer", "mfr", "firm_name"],
        "brand_name": ["brand_name", "brand", "device_brand"],
        "product_code": ["product_code", "code"],
        "device_class": ["device_class", "class"],
        "udi_di": ["udi_di", "udi", "primary_di", "di"],
        "recall_number_link": ["recall_number_link", "recall_number", "linked_recall"],
        "narrative": ["narrative", "description", "event_description", "text"],
    },
    "gudid": {
        "primary_di": ["primary_di", "primarydi", "udi_di", "udi", "di"],
        "udi_di": ["udi_di", "primary_di", "udi", "di"],
        "device_description": ["device_description", "description", "device_desc"],
        "device_class": ["device_class", "class"],
        "manufacturer_name": ["manufacturer_name", "manufacturer", "mfr", "company"],
        "brand_name": ["brand_name", "brand", "device_brand"],
        "product_code": ["product_code", "code"],
        "gmdn_term": ["gmdn_term", "gmdn", "gmdn_name"],
        "mri_safety": ["mri_safety", "mri", "mri_status", "mri_safety_status"],
        "sterile": ["sterile", "is_sterile"],
        "single_use": ["single_use", "singleuse", "is_single_use"],
        "implantable": ["implantable", "is_implantable"],
        "contains_nrl": ["contains_nrl", "nrl", "latex", "contains_latex"],
        "version_or_model_number": ["version_or_model_number", "model", "model_number", "version"],
        "catalog_number": ["catalog_number", "catalog", "cat_no"],
        "record_status": ["record_status", "status"],
        "publish_date": ["publish_date", "date"],
        "company_contact_email": ["company_contact_email", "email"],
        "company_contact_phone": ["company_contact_phone", "phone", "telephone"],
        "company_state": ["company_state", "state"],
        "company_country": ["company_country", "country"],
    },
    "recall": {
        "recall_number": ["recall_number", "recall", "recall_id", "z_number", "z#"],
        "recall_class": ["recall_class", "class"],
        "event_date": ["event_date", "date", "initiation_date"],
        "termination_date": ["termination_date", "term_date"],
        "status": ["status", "recall_status"],
        "firm_name": ["firm_name", "firm", "company", "applicant"],
        "manufacturer_name": ["manufacturer_name", "manufacturer", "mfr", "firm_name"],
        "product_description": ["product_description", "description", "product"],
        "product_code": ["product_code", "code"],
        "code_info": ["code_info", "lots", "serials", "batch"],
        "reason_for_recall": ["reason_for_recall", "reason", "root_cause", "root_cause_description", "cause"],
        "distribution_pattern": ["distribution_pattern", "distribution"],
        "quantity_in_commerce": ["quantity_in_commerce", "quantity", "qty"],
        "country": ["country"],
        "state": ["state"],
    },
}


def _norm_col(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def detect_format(text: str) -> str:
    t0 = (text or "").lstrip()
    if not t0:
        return "unknown"
    if t0.startswith("{") or t0.startswith("["):
        return "json"
    if "," in t0 and "\n" in t0:
        return "csv"
    return "text"


def parse_dataset_blob(blob: Union[str, bytes], filename: Optional[str] = None) -> pd.DataFrame:
    if isinstance(blob, bytes):
        text = blob.decode("utf-8", errors="ignore")
    else:
        text = blob

    fmt = None
    if filename:
        fn = filename.lower()
        if fn.endswith(".json"):
            fmt = "json"
        elif fn.endswith(".csv"):
            fmt = "csv"
        else:
            fmt = detect_format(text)
    else:
        fmt = detect_format(text)

    if fmt == "json":
        obj = json.loads(text)
        if isinstance(obj, dict):
            for k in ["datasets", "data", "records", "items", "rows"]:
                if k in obj and isinstance(obj[k], list):
                    obj = obj[k]
                    break
            if isinstance(obj, dict):
                obj = [obj]
        if not isinstance(obj, list):
            raise ValueError("JSON must be a list of objects (or a wrapper containing a list).")
        return pd.DataFrame(obj)

    if fmt == "csv":
        return pd.read_csv(io.StringIO(text))

    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            obj = [obj]
        return pd.DataFrame(obj)
    except Exception:
        return pd.read_csv(io.StringIO(text))


def _best_match_column(df_cols: List[str], candidates: List[str]) -> Optional[str]:
    norm_map = {_norm_col(c): c for c in df_cols}
    for cand in candidates:
        n = _norm_col(cand)
        if n in norm_map:
            return norm_map[n]
    best, best_score = None, 0
    for c in df_cols:
        for cand in candidates:
            sc = fuzz.ratio(_norm_col(c), _norm_col(cand))
            if sc > best_score:
                best_score, best = sc, c
    return best if best_score >= 85 else None


def standardize_df(dataset_type: str, df: pd.DataFrame) -> Tuple[pd.DataFrame, str]:
    dataset_type = dataset_type.lower().strip()
    if df is None or df.empty:
        return pd.DataFrame(), "No data to standardize."

    canon = CANON[dataset_type]
    syn = SYNONYMS[dataset_type]
    original_cols = list(df.columns)

    mapped: Dict[str, Optional[str]] = {}
    report_lines = ["### Standardization Mapping", "", "| Canonical field | Source column |", "|---|---|"]
    for cfield in canon:
        src = _best_match_column(original_cols, syn.get(cfield, [cfield]))
        mapped[cfield] = src
        report_lines.append(f"| `{cfield}` | `{src if src else '— (missing)'}` |")

    out = pd.DataFrame()
    for cfield in canon:
        src = mapped[cfield]
        out[cfield] = df[src] if (src and src in df.columns) else None

    if dataset_type == "510k":
        def to_list(x):
            if x is None or (isinstance(x, float) and pd.isna(x)):
                return []
            if isinstance(x, list):
                return x
            if isinstance(x, str):
                parts = [p.strip() for p in re.split(r"[;,]+", x) if p.strip()]
                return parts
            return [str(x)]
        out["predicate_k_numbers"] = out["predicate_k_numbers"].apply(to_list)

    if dataset_type == "gudid":
        def to_bool(v):
            if isinstance(v, bool):
                return v
            if v is None or (isinstance(v, float) and pd.isna(v)):
                return None
            s = str(v).strip().lower()
            if s in ["true", "t", "yes", "y", "1"]:
                return True
            if s in ["false", "f", "no", "n", "0"]:
                return False
            return None
        for bcol in ["sterile", "single_use", "implantable", "contains_nrl"]:
            out[bcol] = out[bcol].apply(to_bool)

    if dataset_type == "recall":
        def to_int(v):
            if v is None or (isinstance(v, float) and pd.isna(v)):
                return None
            try:
                return int(float(str(v).replace(",", "").strip()))
            except Exception:
                return None
        out["quantity_in_commerce"] = out["quantity_in_commerce"].apply(to_int)

    def row_has_any_signal(r):
        for c in canon:
            v = r.get(c)
            if isinstance(v, list) and len(v) > 0:
                return True
            if v is None:
                continue
            if isinstance(v, float) and pd.isna(v):
                continue
            if str(v).strip() != "":
                return True
        return False

    out = out[out.apply(row_has_any_signal, axis=1)].reset_index(drop=True)

    report_lines += ["", f"**Rows:** {len(out)}", f"**Original columns:** {len(original_cols)}"]
    return out, "\n".join(report_lines)


def df_to_json_records(df: pd.DataFrame) -> str:
    return json.dumps(df.to_dict(orient="records"), ensure_ascii=False, indent=2)


# ============================================================
# Search engine
# ============================================================
@dataclass
class SearchResult:
    dataset: str
    score: int
    record: Dict[str, Any]


class RegulatorySearchEngine:
    def __init__(self, dfs: Dict[str, pd.DataFrame]):
        self.dfs = dfs

    def _score_row(self, row: Dict[str, Any], cols: List[str], query: str, exact: bool, fuzzy_level: int) -> int:
        q = (query or "").strip().lower()
        if not q:
            return 0
        best = 0
        for c in cols:
            v = str(row.get(c, "")).lower()
            if not v:
                continue
            if exact:
                if q in v:
                    best = max(best, 100)
            else:
                best = max(best, fuzz.partial_ratio(q, v))
        return best if best >= fuzzy_level else 0

    def search(self, query: str, include: Dict[str, bool], exact: bool, fuzzy_level: int) -> Dict[str, List[SearchResult]]:
        results: Dict[str, List[SearchResult]] = {k: [] for k in ["510k", "recall", "adr", "gudid"]}
        q = (query or "").strip()
        if not q:
            return results

        specs = {
            "510k": ["k_number", "device_name", "applicant", "manufacturer_name", "product_code", "summary", "panel", "decision"],
            "recall": ["recall_number", "firm_name", "manufacturer_name", "product_code", "reason_for_recall", "product_description", "recall_class", "status"],
            "adr": ["adverse_event_id", "brand_name", "manufacturer_name", "product_code", "udi_di", "device_problem", "patient_outcome", "narrative"],
            "gudid": ["udi_di", "primary_di", "brand_name", "manufacturer_name", "product_code", "device_description", "gmdn_term", "mri_safety"],
        }

        for ds, df in self.dfs.items():
            if ds not in results:
                continue
            if not include.get(ds, True):
                continue
            if df is None or df.empty:
                continue
            cols = specs.get(ds, list(df.columns))
            for _, r in df.iterrows():
                rec = r.to_dict()
                sc = self._score_row(rec, cols, q, exact=exact, fuzzy_level=fuzzy_level)
                if sc:
                    results[ds].append(SearchResult(ds, sc, rec))
            results[ds].sort(key=lambda x: x.score, reverse=True)
            results[ds] = results[ds][:200]

        q_upper = q.upper()
        if include.get("510k", True) and results["510k"]:
            top = results["510k"][0].record
            if str(top.get("k_number", "")).upper() == q_upper:
                preds = top.get("predicate_k_numbers") or []
                for pk in preds:
                    for _, r in self.dfs["510k"].iterrows():
                        rec = r.to_dict()
                        if str(rec.get("k_number", "")).upper() == str(pk).upper():
                            results["510k"].append(SearchResult("510k", 95, rec))
                results["510k"].sort(key=lambda x: x.score, reverse=True)

        return results


# ============================================================
# LLM routing (OpenAI / Gemini / Anthropic / xAI)
# ============================================================
def provider_model_map():
    return {
        "openai": OPENAI_MODELS,
        "gemini": GEMINI_MODELS,
        "anthropic": ANTHROPIC_MODELS,
        "xai": XAI_MODELS,
    }


def _get_env_any(env_keys: List[str]) -> Optional[str]:
    for k in env_keys:
        v = os.environ.get(k)
        if v:
            return v
    return None


def get_api_key(env_primary: str) -> Tuple[Optional[str], str]:
    env_val = _get_env_any(KEY_ENV_CANDIDATES.get(env_primary, [env_primary]))
    if env_val:
        return env_val, "env"
    sess = st.session_state.get("api_keys", {}).get(env_primary)
    if sess:
        return sess, "session"
    return None, "missing"


def call_llm_text(provider: str, model: str, api_key: str, system: str, user: str,
                  max_tokens: int = 12000, temperature: float = 0.2) -> str:
    provider = (provider or "").lower().strip()

    if provider == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        resp = client.responses.create(
            model=model,
            input=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            max_output_tokens=max_tokens,
            temperature=temperature,
        )
        return resp.output_text or ""

    if provider == "gemini":
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        m = genai.GenerativeModel(
            model_name=model,
            generation_config={"temperature": temperature, "max_output_tokens": max_tokens},
        )
        r = m.generate_content([system, user])
        return (r.text or "").strip()

    if provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        parts = []
        for b in msg.content:
            if getattr(b, "type", "") == "text":
                parts.append(b.text)
        return "".join(parts).strip()

    if provider == "xai":
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
        resp = client.responses.create(
            model=model,
            input=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            max_output_tokens=max_tokens,
            temperature=temperature,
        )
        return resp.output_text or ""

    raise ValueError(f"Unsupported provider: {provider}")


def call_vision_ocr(provider: str, model: str, api_key: str, images: List[Image.Image], lang: str,
                    max_tokens: int = 12000) -> str:
    provider = (provider or "").lower().strip()
    sys = "You are an OCR engine for regulatory PDFs. Preserve tables when possible. Output plain text (no markdown)."
    if lang == "zh-TW":
        sys = "你是法規 PDF 的 OCR 引擎。盡可能保留表格結構與數值。輸出純文字（不要 Markdown）。"
    prompt = "Transcribe verbatim. Preserve headings and tables."
    if lang == "zh-TW":
        prompt = "請逐字轉錄，保留標題與表格結構。"

    chunks = []
    if provider == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        for i, img in enumerate(images, start=1):
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            data_url = f"data:image/png;base64,{b64}"
            resp = client.responses.create(
                model=model,
                input=[
                    {"role": "system", "content": sys},
                    {"role": "user", "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": data_url},
                    ]},
                ],
                max_output_tokens=max_tokens,
                temperature=0.0,
            )
            chunks.append(f"\n\n--- PAGE {i} ---\n{(resp.output_text or '').strip()}")
        return "\n".join(chunks).strip()

    if provider == "gemini":
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        m = genai.GenerativeModel(model_name=model, generation_config={"temperature": 0.0, "max_output_tokens": max_tokens})
        for i, img in enumerate(images, start=1):
            r = m.generate_content([sys + "\n" + prompt, img])
            chunks.append(f"\n\n--- PAGE {i} ---\n{(r.text or '').strip()}")
        return "\n".join(chunks).strip()

    raise ValueError("Vision OCR only supported for provider=openai or gemini.")


# ============================================================
# PDF tools
# ============================================================
def parse_page_ranges(ranges_str: str) -> List[Tuple[int, int]]:
    ranges_str = (ranges_str or "").strip()
    if not ranges_str:
        return []
    out = []
    parts = [p.strip() for p in ranges_str.split(",") if p.strip()]
    for p in parts:
        if "-" in p:
            a, b = p.split("-", 1)
            a = int(a.strip())
            b = int(b.strip())
            if a > b:
                a, b = b, a
            out.append((a, b))
        else:
            n = int(p)
            out.append((n, n))
    return out


def trim_pdf_bytes(pdf_bytes: bytes, page_ranges: List[Tuple[int, int]]) -> bytes:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()
    n = len(reader.pages)
    for (s, e) in page_ranges:
        s = max(1, s)
        e = min(n, e)
        for i in range(s - 1, e):
            writer.add_page(reader.pages[i])
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def extract_text_pypdf2(pdf_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return "\n\n".join([(p.extract_text() or "") for p in reader.pages]).strip()


def render_pdf_iframe(pdf_bytes: bytes, height: int = 520) -> str:
    b64 = base64.b64encode(pdf_bytes).decode("utf-8")
    return f"""
    <iframe
        src="data:application/pdf;base64,{b64}"
        width="100%"
        height="{height}"
        style="border: 1px solid var(--border); border-radius: 14px; background: white;"
        type="application/pdf">
    </iframe>
    """


def markdown_reconstruct(text: str) -> str:
    if not text:
        return ""
    x = text.replace("\r\n", "\n")
    x = re.sub(r"[ \t]+\n", "\n", x)
    x = re.sub(r"\n{3,}", "\n\n", x)
    x = re.sub(r"\n(\*|-|•)\s*", r"\n- ", x)

    def as_heading(m):
        line = m.group(1).strip()
        return f"\n\n## {line.title()}\n"

    x = re.sub(r"\n([A-Z][A-Z0-9 \-/]{8,})\n", as_heading, x)
    return x.strip()


# ============================================================
# Agents YAML handling (heuristic standardization + optional LLM)
# ============================================================
DEFAULT_AGENTS_YAML = """version: "1.0"
agents:
  - id: substantial_equivalence_writer
    name: Substantial Equivalence Writer
    description: Draft SE narrative and identify key equivalence arguments.
    provider: openai
    model: gpt-4o-mini
    temperature: 0.2
    max_tokens: 6000
    system_prompt: |
      You are a senior FDA 510(k) reviewer. Be conservative; do not fabricate.
      Provide structured Markdown with sections, evidence quotes, and gaps.
    user_prompt: |
      Analyze the document and draft an SE-focused review note:
      - Intended Use
      - Predicate comparison
      - Technological characteristics
      - Performance testing
      - Labeling and contraindications
      - Risks & gaps
"""


def read_text_file(path: str, default: str) -> str:
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
    except Exception:
        pass
    return default


def safe_write_text(path: str, content: str):
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception:
        pass


def standardize_agents_obj(obj: Any) -> Dict[str, Any]:
    if obj is None:
        return {"version": "1.0", "agents": []}

    if isinstance(obj, list):
        obj = {"version": "1.0", "agents": obj}

    if not isinstance(obj, dict):
        return {"version": "1.0", "agents": []}

    version = str(obj.get("version", "1.0"))
    agents = obj.get("agents", obj.get("items", obj.get("data", [])))
    if not isinstance(agents, list):
        agents = []

    fixed = []
    for i, a in enumerate(agents):
        if not isinstance(a, dict):
            continue
        aid = a.get("id") or a.get("agent_id") or a.get("key") or f"agent_{i+1}"
        name = a.get("name") or a.get("title") or aid
        desc = a.get("description") or a.get("desc") or ""
        provider = (a.get("provider") or a.get("vendor") or "openai").lower()
        model = a.get("model") or a.get("llm") or "gpt-4o-mini"
        temp = a.get("temperature", 0.2)
        mx = a.get("max_tokens", a.get("max_output_tokens", 6000))
        system_prompt = a.get("system_prompt") or a.get("system") or a.get("instructions") or a.get("prompt") or ""
        user_prompt = a.get("user_prompt") or a.get("user") or a.get("task") or "Analyze the provided content."

        fixed.append({
            "id": str(aid),
            "name": str(name),
            "description": str(desc),
            "provider": str(provider),
            "model": str(model),
            "temperature": float(temp) if str(temp).replace(".", "", 1).isdigit() else 0.2,
            "max_tokens": int(mx) if str(mx).isdigit() else 6000,
            "system_prompt": str(system_prompt),
            "user_prompt": str(user_prompt),
        })

    return {"version": version, "agents": fixed}


def load_agents_yaml(raw_text: str) -> Tuple[Dict[str, Any], Optional[str]]:
    try:
        obj = yaml.safe_load(raw_text) if raw_text.strip() else {"version": "1.0", "agents": []}
        cfg = standardize_agents_obj(obj)

        for a in cfg.get("agents", []):
            if not a.get("id") or not a.get("system_prompt"):
                return cfg, "Agent missing required keys: id and/or system_prompt."
        return cfg, None
    except Exception as e:
        return {"version": "1.0", "agents": []}, str(e)


def dump_agents_yaml(cfg: Dict[str, Any]) -> str:
    return yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True)


def unified_diff(a: str, b: str) -> str:
    import difflib
    return "".join(difflib.unified_diff(
        a.splitlines(keepends=True),
        b.splitlines(keepends=True),
        fromfile="before.yaml",
        tofile="after.yaml",
    ))


def llm_standardize_agents_yaml(raw_yaml: str, provider: str, model: str, api_key: str, lang: str) -> str:
    schema = {
        "version": "1.0",
        "agents": [{
            "id": "string (unique)",
            "name": "string",
            "description": "string",
            "provider": "enum(openai, gemini, anthropic, xai)",
            "model": "string",
            "temperature": 0.2,
            "max_tokens": 6000,
            "system_prompt": "string",
            "user_prompt": "string",
        }]
    }
    sys = "You convert arbitrary YAML agent configs into a strict standard YAML schema. Output YAML only."
    if lang == "zh-TW":
        sys = "你負責把任意 agents YAML 轉成嚴格標準 schema。只輸出 YAML。"
    user = f"""Convert the following YAML into this strict schema. Fill missing fields conservatively.

SCHEMA (example):
```json
{json.dumps(schema, ensure_ascii=False, indent=2)}
```

INPUT YAML:
```yaml
{raw_yaml}
```
"""
    out = call_llm_text(provider, model, api_key, sys, user, max_tokens=4000, temperature=0.0)
    return out.strip()


# ============================================================
# AI Note Keeper Magics (6)
# ============================================================
NOTE_MAGICS = [
    "Organize Note (Markdown)",
    "Executive Summary",
    "Action Items + Owners",
    "Risk/Deficiency Finder",
    "Compliance Checklist Generator",
    "AI Keywords Highlighter",
]


def magic_run(magic_name: str, provider: str, model: str, api_key: str, raw_note: str, lang: str, max_tokens: int = 6000) -> str:
    if lang == "zh-TW":
        system = "你是資深法規與技術編輯助理。請回傳乾淨、結構化的 Markdown。內容需保守、不可捏造，缺資料請用 Gap 標示。"
    else:
        system = "You are an expert regulatory assistant and technical editor. Return clean, structured Markdown. Be conservative; do not fabricate. Mark missing info as Gap."

    if magic_name == "Organize Note (Markdown)":
        user = f"請把以下筆記整理成結構化 Markdown（含標題、重點、待辦、風險/缺口、關鍵詞）：\n\n{raw_note}" if lang == "zh-TW" else \
               f"Organize the following note into structured Markdown with headings, bullets, action items, gaps, and keywords:\n\n{raw_note}"
        return call_llm_text(provider, model, api_key, system, user, max_tokens=max_tokens, temperature=0.2)

    if magic_name == "Executive Summary":
        user = f"請產出一段高密度主管摘要（Markdown，3~7 點重點）：\n\n{raw_note}" if lang == "zh-TW" else \
               f"Create an executive summary (Markdown) with 3-7 key points:\n\n{raw_note}"
        return call_llm_text(provider, model, api_key, system, user, max_tokens=max_tokens, temperature=0.2)

    if magic_name == "Action Items + Owners":
        user = f"請從筆記抽取待辦事項，輸出 Markdown 表格：Action、Owner(建議)、Due date(建議)、Rationale。\n\n{raw_note}" if lang == "zh-TW" else \
               f"Extract action items. Output a Markdown table: Action, Owner (suggested), Due date (suggested), Rationale.\n\n{raw_note}"
        return call_llm_text(provider, model, api_key, system, user, max_tokens=max_tokens, temperature=0.2)

    if magic_name == "Risk/Deficiency Finder":
        user = f"請找出法規風險/缺失點，並以 [High/Med/Low] 分級；每點需包含證據摘錄（引用原文）。\n\n{raw_note}" if lang == "zh-TW" else \
               f"Identify regulatory risks/deficiencies with [High/Med/Low] severity and evidence quotes.\n\n{raw_note}"
        return call_llm_text(provider, model, api_key, system, user, max_tokens=max_tokens, temperature=0.2)

    if magic_name == "Compliance Checklist Generator":
        user = f"請依常見 510(k) 審查主題產出合規核對清單（Markdown checkbox），如：biocompatibility、sterility、labeling、cybersecurity、software V&V。\n\n{raw_note}" if lang == "zh-TW" else \
               f"Generate a compliance checklist (Markdown checkboxes) for common 510(k) topics.\n\n{raw_note}"
        return call_llm_text(provider, model, api_key, system, user, max_tokens=max_tokens, temperature=0.2)

    raise ValueError("AI Keywords Highlighter handled in UI.")


def apply_keyword_colors(text: str, pairs: List[Tuple[str, str]]) -> str:
    out = coral_highlight(text)
    for kw, color in pairs:
        if not kw.strip():
            continue
        out = re.sub(
            rf"(?i)({re.escape(kw)})",
            rf"<span style='color:{color}; font-weight:900; text-shadow:0 0 18px rgba(255,255,255,0.08)'>\1</span>",
            out,
        )
    return out


# ============================================================
# Smart suggestions (intent)
# ============================================================
def smart_suggestions(lang: str, q: str) -> List[str]:
    q = (q or "").strip()
    if not q:
        return [
            "Search 'Infusion Pump' in 510(k)",
            "Find Recalls related to 'Battery'",
            "Analyze 'Latex Allergy' signals",
            "Check 'K240123'",
        ] if lang == "en" else [
            "在 510(k) 搜尋 'Infusion Pump'",
            "找出與 'Battery' 相關的召回",
            "分析 'Latex Allergy' 信號",
            "查詢 'K240123'",
        ]
    base = q
    if lang == "en":
        return [
            f"Search '{base}' across ALL datasets",
            f"Search '{base}' in 510(k)",
            f"Find Recalls related to '{base}'",
            f"Find ADR/MDR events for '{base}'",
            f"Lookup GUDID for '{base}' (UDI/DI)",
        ]
    return [
        f"在全部資料集搜尋 '{base}'",
        f"在 510(k) 搜尋 '{base}'",
        f"找出與 '{base}' 相關的召回",
        f"找出與 '{base}' 相關的 ADR/MDR",
        f"在 GUDID 查詢 '{base}'（UDI/DI）",
    ]


# ============================================================
# Batch Factory: scan/trim/summarize/toc
# ============================================================
def scan_pdfs(root_dir: str) -> List[str]:
    p = pathlib.Path(root_dir)
    if not p.exists():
        return []
    return [str(x) for x in p.rglob("*.pdf") if x.is_file()]


def trim_first_page_to_bytes(pdf_path: str) -> bytes:
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    return trim_pdf_bytes(pdf_bytes, [(1, 1)])


def summarize_cover(provider: str, model: str, api_key: str, text: str, lang: str) -> str:
    sys = "You summarize FDA regulatory cover pages. Output Markdown." if lang != "zh-TW" else "你負責摘要 FDA 法規文件封面頁。輸出 Markdown。"
    user = (
        "Summarize in 3 sentences: Device Name, Applicant/Firm, Primary Indication/Intended Use. Do not fabricate.\n\n"
        f"TEXT:\n{text}"
    ) if lang != "zh-TW" else (
        "請用 3 句摘要：裝置名稱、公司/申請者、主要適應症/預期用途。不可捏造。\n\n"
        f"文字：\n{text}"
    )
    return call_llm_text(provider, model, api_key, sys, user, max_tokens=800, temperature=0.2)


def build_master_toc(items: List[Dict[str, str]]) -> str:
    lines = ["# Project Master Index", ""]
    for i, it in enumerate(items, start=1):
        lines += [
            f"## {i}. {it.get('file_name','(unknown)')}",
            f"* Path: `{it.get('path','')}`",
            f"* Summary:\n\n{it.get('summary_md','')}",
            "",
        ]
    return "\n".join(lines).strip()


# ============================================================
# Streamlit setup + Session init
# ============================================================
st.set_page_config(page_title="FDA Review Studio", layout="wide")


def ss_init():
    st.session_state.setdefault("theme", "dark")
    st.session_state.setdefault("lang", "en")
    st.session_state.setdefault("style", PAINTER_STYLES[0])

    st.session_state.setdefault("api_keys", {})

    st.session_state.setdefault("global_query", "")
    st.session_state.setdefault("search_exact", False)
    st.session_state.setdefault("search_fuzzy", 80)
    st.session_state.setdefault("search_include", {"510k": True, "recall": True, "adr": True, "gudid": True})

    st.session_state.setdefault("dfs", {"510k": pd.DataFrame(), "recall": pd.DataFrame(), "adr": pd.DataFrame(), "gudid": pd.DataFrame()})
    st.session_state.setdefault("dataset_loaded_from", "defaultsets.json")

    st.session_state.setdefault("doc_input_mode", "PDF")
    st.session_state.setdefault("pdf_bytes", None)
    st.session_state.setdefault("trimmed_pdf_bytes", None)
    st.session_state.setdefault("raw_text", "")
    st.session_state.setdefault("ocr_text", "")
    st.session_state.setdefault("doc_text_override", "")

    # OCR stable selections (FIX: keep widget state stable, not inside button handler)
    st.session_state.setdefault("doc_ocr_engine_choice", "extract")
    st.session_state.setdefault("doc_vision_provider", "openai")
    st.session_state.setdefault("doc_vision_model", OPENAI_MODELS[0])

    st.session_state.setdefault("agents_yaml_text", "")
    st.session_state.setdefault("agents_cfg", {"version": "1.0", "agents": []})
    st.session_state.setdefault("skill_md", "")

    st.session_state.setdefault("agent_runs", [])
    st.session_state.setdefault("final_report", "")

    st.session_state.setdefault("note_raw", "")
    st.session_state.setdefault("note_md", "")
    st.session_state.setdefault("note_render_html", "")
    st.session_state.setdefault("keyword_pairs", [("", CORAL), ("", "#00B3B3"), ("", "#F4D03F")])

    st.session_state.setdefault("ds_source_mode", "default")
    st.session_state.setdefault("ds_selected_type", "510k")
    st.session_state.setdefault("ds_paste_text", "")
    st.session_state.setdefault("ds_report", "")

    st.session_state.setdefault("factory_manifest", pd.DataFrame())
    st.session_state.setdefault("factory_toc_md", "")
    st.session_state.setdefault("factory_items", [])


ss_init()


def load_defaults_into_session():
    data = load_defaultsets_json()
    ds = data.get("datasets", {})
    for k in ["510k", "recall", "adr", "gudid"]:
        st.session_state["dfs"][k] = pd.DataFrame(ds.get(k, []))
    st.session_state["dataset_loaded_from"] = DEFAULTSETS_PATH


if st.session_state["dfs"]["510k"].empty and st.session_state["dfs"]["recall"].empty and st.session_state["dfs"]["adr"].empty and st.session_state["dfs"]["gudid"].empty:
    load_defaults_into_session()

if not st.session_state["agents_yaml_text"].strip():
    st.session_state["agents_yaml_text"] = read_text_file(AGENTS_PATH, DEFAULT_AGENTS_YAML)

if not st.session_state["skill_md"].strip():
    st.session_state["skill_md"] = read_text_file(SKILL_PATH, "# SKILL\n\n(Place shared constraints/instructions here.)\n")

agents_cfg, agents_err = load_agents_yaml(st.session_state["agents_yaml_text"])
st.session_state["agents_cfg"] = agents_cfg

lang = st.session_state["lang"]
theme = st.session_state["theme"]
style = st.session_state["style"]

st.markdown(inject_css(theme, style["accent"]), unsafe_allow_html=True)
st.markdown("<div class='fab'>WOW</div><div class='fab-sub'>Regulatory Command Center</div>", unsafe_allow_html=True)

# ============================================================
# Top Bar: Title + Status + Settings popover (improved)
# ============================================================
def status_chip(label: str, env_primary: str) -> str:
    key, src = get_api_key(env_primary)
    if src == "env":
        dot = "var(--ok)"; stt = t(lang, "managed_by_env")
    elif src == "session":
        dot = "var(--warn)"; stt = t(lang, "session_key")
    else:
        dot = "var(--bad)"; stt = t(lang, "missing_key")
    return f"<span class='chip'><span class='dot' style='background:{dot}'></span>{label}: {stt}</span>"


def dataset_chip() -> str:
    dfs = st.session_state["dfs"]
    return f"<span class='chip'><span class='dot'></span>510k:{len(dfs['510k'])} Recall:{len(dfs['recall'])} ADR:{len(dfs['adr'])} GUDID:{len(dfs['gudid'])}</span>"


def ocr_chip() -> str:
    ok = bool((st.session_state["ocr_text"] or "").strip())
    dot = "var(--ok)" if ok else "var(--warn)"
    txt = "READY" if ok else "EMPTY"
    return f"<span class='chip'><span class='dot' style='background:{dot}'></span>OCR: {txt}</span>"


def choose_style_with_ai(provider: str, model: str, api_key: str, context: str, lang: str) -> Optional[Dict[str, Any]]:
    style_list = "\n".join([f"- {s['name']} (id={s['id']})" for s in PAINTER_STYLES])
    sys = "You pick an art style for a UI theme. Output exactly one style id from the list. No extra words."
    if lang == "zh-TW":
        sys = "你負責替 UI 選擇畫家風格。請只輸出一個 style id，不要多餘文字。"
    user = f"""Choose ONE painter style id based on the vibe (regulatory/clinical/engineering) and the content.

STYLES:
{style_list}

CONTENT:
{context[:7000]}
"""
    sid = call_llm_text(provider, model, api_key, sys, user, max_tokens=40, temperature=0.2).strip().lower()
    return next((s for s in PAINTER_STYLES if s["id"] == sid), None)


top = st.container()
with top:
    c1, c2, c3 = st.columns([2.1, 3.5, 1.2], vertical_alignment="center")
    with c1:
        st.markdown(f"<div class='wow-card'><h3 style='margin:0'>{t(lang,'app_title')}</h3></div>", unsafe_allow_html=True)
    with c2:
        chips = ""
        chips += status_chip("OpenAI", "OPENAI_API_KEY")
        chips += status_chip("Gemini", "GEMINI_API_KEY")
        chips += status_chip("Anthropic", "ANTHROPIC_API_KEY")
        chips += status_chip("xAI", "XAI_API_KEY")
        chips += dataset_chip()
        chips += ocr_chip()
        st.markdown(f"<div class='wow-card'>{chips}</div>", unsafe_allow_html=True)

        mana = (len(st.session_state["agent_runs"]) % 10) / 10.0
        st.progress(mana, text=f"{t(lang,'agent_runs')}: {len(st.session_state['agent_runs'])}")

    with c3:
        with st.popover(t(lang, "settings")):
            st.session_state["theme"] = st.radio(t(lang, "theme"), ["dark", "light"], index=0 if theme == "dark" else 1, key="set_theme")
            st.session_state["lang"] = st.radio(t(lang, "language"), ["en", "zh-TW"], index=0 if lang == "en" else 1, key="set_lang")

            style_names = [s["name"] for s in PAINTER_STYLES]
            curr = st.session_state["style"]["name"]
            ix = style_names.index(curr) if curr in style_names else 0
            pick = st.selectbox(t(lang, "style"), style_names, index=ix, key="set_style")
            st.session_state["style"] = next(s for s in PAINTER_STYLES if s["name"] == pick)

            colA, colB = st.columns([1, 1])
            with colA:
                if st.button(t(lang, "jackpot"), use_container_width=True, key="set_style_jackpot"):
                    st.session_state["style"] = jackpot_style()
                    st.rerun()

            with colB:
                with st.expander(t(lang, "style_ai_pick"), expanded=False):
                    st.caption(t(lang, "style_ai_help"))
                    pmap = provider_model_map()
                    prov = st.selectbox(t(lang, "provider"), list(pmap.keys()), index=0, key="set_style_ai_prov")
                    model = st.selectbox(t(lang, "model"), pmap[prov], index=0, key="set_style_ai_model")

                    # context from query + note + doc
                    ctx = "\n\n".join([
                        f"QUERY:\n{st.session_state.get('global_query','')}",
                        f"NOTE:\n{st.session_state.get('note_raw','')}",
                        f"DOC:\n{st.session_state.get('ocr_text','')}",
                    ]).strip()

                    if st.button(f"{t(lang,'run')} AI", use_container_width=True, key="set_style_ai_run"):
                        env_primary = {"openai": "OPENAI_API_KEY", "gemini": "GEMINI_API_KEY", "anthropic": "ANTHROPIC_API_KEY", "xai": "XAI_API_KEY"}[prov]
                        api_key, src = get_api_key(env_primary)
                        if not api_key:
                            st.error(f"{env_primary} missing.")
                        else:
                            try:
                                chosen = choose_style_with_ai(prov, model, api_key, ctx, lang=st.session_state["lang"])
                                if chosen:
                                    st.session_state["style"] = chosen
                                    st.success(f"{t(st.session_state['lang'],'style_recommended')}: {chosen['name']}")
                                    st.rerun()
                                else:
                                    st.warning("AI returned an unknown style id.")
                            except Exception as e:
                                st.error(f"AI style pick failed: {e}")

# refresh locals after settings changes
lang = st.session_state["lang"]
theme = st.session_state["theme"]
style = st.session_state["style"]
st.markdown(inject_css(theme, style["accent"]), unsafe_allow_html=True)

# ============================================================
# Sidebar: API Keys (rule: hide input if env exists)
# ============================================================
with st.sidebar:
    st.markdown(f"<div class='wow-card'><h4 style='margin:0'>{t(lang,'status')}</h4></div>", unsafe_allow_html=True)

    def api_key_block(label: str, env_primary: str):
        key, src = get_api_key(env_primary)
        if src == "env":
            st.markdown(f"<div class='wow-mini'><b>{label}</b><br/>{t(lang,'managed_by_env')}</div>", unsafe_allow_html=True)
            return
        val = st.text_input(f"{label} key", value=st.session_state["api_keys"].get(env_primary, ""), type="password", key=f"key_{env_primary}")
        if val:
            st.session_state["api_keys"][env_primary] = val

    api_key_block("OpenAI", "OPENAI_API_KEY")
    api_key_block("Gemini", "GEMINI_API_KEY")
    api_key_block("Anthropic", "ANTHROPIC_API_KEY")
    api_key_block("xAI", "XAI_API_KEY")

    st.divider()
    st.markdown(f"<div class='wow-card'><h4 style='margin:0'>{t(lang,'danger_zone')}</h4></div>", unsafe_allow_html=True)
    if st.button(t(lang, "clear_session"), use_container_width=True, key="clear_session_btn"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

# ============================================================
# Navigation + Global command bar
# ============================================================
nav = st.columns([2.2, 1.8, 2.0], vertical_alignment="center")
with nav[0]:
    page = st.selectbox(
        "Navigation",
        [
            t(lang, "nav_dashboard"),
            t(lang, "nav_command"),
            t(lang, "nav_datasets"),
            t(lang, "nav_agents"),
            t(lang, "nav_factory"),
            t(lang, "nav_notes"),
        ],
        index=0,
        key="nav_page",
    )

with nav[1]:
    st.session_state["global_query"] = st.text_input(
        t(lang, "global_search"),
        value=st.session_state["global_query"],
        placeholder=t(lang, "search_placeholder"),
        key="global_query_input",
    )

with nav[2]:
    with st.expander("Search Settings", expanded=False):
        st.session_state["search_exact"] = st.checkbox(t(lang, "exact_match"), value=st.session_state["search_exact"], key="search_exact_cb")
        st.session_state["search_fuzzy"] = st.slider(t(lang, "fuzzy_level"), 60, 95, int(st.session_state["search_fuzzy"]), 1, key="search_fuzzy_slider")
        st.caption(t(lang, "dataset_toggles"))
        inc = st.session_state["search_include"]
        inc["510k"] = st.checkbox("510k", value=inc.get("510k", True), key="inc_510k")
        inc["recall"] = st.checkbox("recall", value=inc.get("recall", True), key="inc_recall")
        inc["adr"] = st.checkbox("adr", value=inc.get("adr", True), key="inc_adr")
        inc["gudid"] = st.checkbox("gudid", value=inc.get("gudid", True), key="inc_gudid")
        st.session_state["search_include"] = inc

engine = RegulatorySearchEngine(st.session_state["dfs"])

def run_search_now() -> Dict[str, List[SearchResult]]:
    return engine.search(
        st.session_state["global_query"],
        include=st.session_state["search_include"],
        exact=st.session_state["search_exact"],
        fuzzy_level=int(st.session_state["search_fuzzy"]),
    )

search_results = run_search_now() if st.session_state["global_query"].strip() else {"510k": [], "recall": [], "adr": [], "gudid": []}

# ============================================================
# Dashboard Page (FIXED: unique Plotly keys)
# ============================================================
def dashboard_page():
    st.markdown(f"<div class='wow-card'><h3 style='margin:0'>{t(lang,'dashboard')}</h3></div>", unsafe_allow_html=True)

    dfs = st.session_state["dfs"]
    k1, k2, k3, k4 = st.columns(4)
    for col, name in zip([k1, k2, k3, k4], ["510k", "recall", "adr", "gudid"]):
        with col:
            st.markdown(
                f"<div class='wow-mini'><b>{name.upper()}</b><br/>{t(lang,'kpi_loaded')}: <span class='coral'>{len(dfs[name])}</span></div>",
                unsafe_allow_html=True,
            )

    with st.expander(t(lang, "smart_suggestions"), expanded=True):
        sugg = smart_suggestions(lang, st.session_state["global_query"])
        s_cols = st.columns(2)
        for i, s in enumerate(sugg[:6]):
            with s_cols[i % 2]:
                if st.button(s, use_container_width=True, key=f"sugg_{i}"):
                    m = re.search(r"'([^']+)'", s)
                    st.session_state["global_query"] = m.group(1) if m else s
                    st.rerun()

    st.markdown(f"<div class='wow-mini'><b>{t(lang,'results')}</b></div>", unsafe_allow_html=True)

    total_hits = sum(len(v) for v in search_results.values())
    if total_hits == 0 and st.session_state["global_query"].strip():
        st.info(t(lang, "no_results"))
        return

    rows = []
    for ds, items in search_results.items():
        for it in items[:200]:
            r = dict(it.record)
            r["_dataset"] = ds
            r["_score"] = it.score
            rows.append(r)
    df_hits = pd.DataFrame(rows)

    tabs = st.tabs([
        f"{t(lang,'all')} ({len(df_hits)})",
        f"510K ({len(search_results['510k'])})",
        f"RECALL ({len(search_results['recall'])})",
        f"ADR ({len(search_results['adr'])})",
        f"GUDID ({len(search_results['gudid'])})",
    ])

    def show_hits(df: pd.DataFrame, key_prefix: str):
        """
        FIX: Always pass unique `key_prefix` so all plotly charts use distinct keys.
        This prevents StreamlitDuplicateElementId in multi-tab rendering.
        """
        if df is None or df.empty:
            st.write("—")
            return

        date_col = None
        for c in ["decision_date", "event_date", "report_date", "publish_date"]:
            if c in df.columns:
                date_col = c
                break

        cat_col = None
        for c in ["device_class", "recall_class", "decision", "panel", "product_code", "status", "_dataset"]:
            if c in df.columns:
                cat_col = c
                break

        cA, cB = st.columns([1, 1])
        with cA:
            st.caption(t(lang, "timeline"))
            if date_col:
                tmp = df.copy()
                tmp[date_col] = pd.to_datetime(tmp[date_col], errors="coerce")
                tmp = tmp.dropna(subset=[date_col])
                if not tmp.empty:
                    fig = px.scatter(tmp.sort_values(date_col), x=date_col, y="_dataset", size="_score", hover_data=tmp.columns)
                    st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_timeline")
                else:
                    st.write("—")
            else:
                st.write("—")

        with cB:
            st.caption(t(lang, "distribution"))
            if cat_col:
                tmp = df.copy()
                tmp[cat_col] = tmp[cat_col].astype(str)
                agg = tmp[cat_col].value_counts().reset_index()
                agg.columns = [cat_col, "count"]
                fig = px.pie(agg.head(12), names=cat_col, values="count", hole=0.55)
                st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_dist")
                st.caption(t(lang, "select_to_filter"))
            else:
                st.write("—")

        st.divider()
        st.dataframe(df.sort_values("_score", ascending=False).head(200), use_container_width=True, height=420)

    with tabs[0]:
        show_hits(df_hits, key_prefix="dash_all")
    with tabs[1]:
        show_hits(df_hits[df_hits["_dataset"] == "510k"] if not df_hits.empty else pd.DataFrame(), key_prefix="dash_510k")
    with tabs[2]:
        show_hits(df_hits[df_hits["_dataset"] == "recall"] if not df_hits.empty else pd.DataFrame(), key_prefix="dash_recall")
    with tabs[3]:
        show_hits(df_hits[df_hits["_dataset"] == "adr"] if not df_hits.empty else pd.DataFrame(), key_prefix="dash_adr")
    with tabs[4]:
        show_hits(df_hits[df_hits["_dataset"] == "gudid"] if not df_hits.empty else pd.DataFrame(), key_prefix="dash_gudid")


# ============================================================
# Dataset Studio Page
# ============================================================
def dataset_studio_page():
    st.markdown(f"<div class='wow-card'><h3 style='margin:0'>{t(lang,'nav_datasets')}</h3></div>", unsafe_allow_html=True)

    ds_type = st.selectbox("Dataset type", ["510k", "recall", "adr", "gudid"],
                           index=["510k", "recall", "adr", "gudid"].index(st.session_state["ds_selected_type"]),
                           key="ds_type_sel")
    st.session_state["ds_selected_type"] = ds_type

    source_mode = st.radio(
        t(lang, "dataset_source"),
        options=["default", "paste", "upload"],
        format_func=lambda x: t(lang, "use_default") if x == "default" else t(lang, x),
        horizontal=True,
        key="ds_source_mode_radio",
    )
    st.session_state["ds_source_mode"] = source_mode

    df_in = None
    raw_preview_df = None

    if source_mode == "default":
        data = load_defaultsets_json()
        raw = data.get("datasets", {}).get(ds_type, [])
        df_in = pd.DataFrame(raw)
        st.caption(f"Loaded from: {DEFAULTSETS_PATH}")

    elif source_mode == "paste":
        st.session_state["ds_paste_text"] = st.text_area(
            f"{t(lang,'paste')} dataset (CSV/JSON)",
            value=st.session_state["ds_paste_text"],
            height=180,
            key="ds_paste_text_widget",
        )
        if st.button(t(lang, "parse_load"), use_container_width=True, key="ds_parse_paste"):
            try:
                df_in = parse_dataset_blob(st.session_state["ds_paste_text"], filename=None)
                raw_preview_df = df_in.head(20)
                st.session_state["ds_tmp_df"] = df_in
            except Exception as e:
                st.error(f"Parse failed: {e}")
        df_in = st.session_state.get("ds_tmp_df")

    else:
        up = st.file_uploader(f"{t(lang,'upload')} dataset file (CSV/JSON/TXT)", type=["csv", "json", "txt"], key="ds_upload_file")
        if up:
            try:
                df_up = parse_dataset_blob(up.read(), filename=up.name)
                raw_preview_df = df_up.head(20)
                st.session_state["ds_tmp_df"] = df_up
            except Exception as e:
                st.error(f"Parse failed: {e}")
        df_in = st.session_state.get("ds_tmp_df")

    if isinstance(raw_preview_df, pd.DataFrame) and not raw_preview_df.empty:
        st.markdown(f"<div class='wow-mini'><b>{t(lang,'preview')} (raw)</b></div>", unsafe_allow_html=True)
        st.dataframe(raw_preview_df, use_container_width=True, height=220)

    st.divider()
    colA, colB = st.columns([1, 1])
    with colA:
        if st.button(t(lang, "standardize"), use_container_width=True, key="ds_standardize_btn"):
            try:
                if df_in is None or (isinstance(df_in, pd.DataFrame) and df_in.empty):
                    st.warning("No input dataset to standardize.")
                else:
                    df_std, rep = standardize_df(ds_type, df_in)
                    st.session_state["ds_report"] = rep
                    st.session_state["dfs"][ds_type] = df_std
                    st.session_state["dataset_loaded_from"] = source_mode
                    st.success(f"{ds_type} standardized. {t(lang,'loaded_rows')}: {len(df_std)}")
                    st.rerun()
            except Exception as e:
                st.error(f"Standardize failed: {e}")

    with colB:
        if st.button(t(lang, "reset_defaults"), use_container_width=True, key="ds_reset_defaults_btn"):
            load_defaults_into_session()
            st.session_state["ds_report"] = ""
            st.rerun()

    if st.session_state.get("ds_report"):
        with st.expander(t(lang, "standardization_report"), expanded=False):
            st.markdown(st.session_state["ds_report"])

    cur_df = st.session_state["dfs"][ds_type]
    st.markdown(f"<div class='wow-mini'><b>{t(lang,'preview')} (standardized)</b></div>", unsafe_allow_html=True)
    st.caption(f"{t(lang,'loaded_rows')}: {len(cur_df)} | loaded_from: {st.session_state['dataset_loaded_from']}")
    st.dataframe(cur_df.head(50), use_container_width=True, height=420)

    d1, d2 = st.columns([1, 1])
    with d1:
        st.download_button(t(lang, "download_csv"), data=cur_df.to_csv(index=False).encode("utf-8"),
                           file_name=f"{ds_type}_standardized.csv", use_container_width=True, key="dl_csv_std")
    with d2:
        st.download_button(t(lang, "download_json"), data=df_to_json_records(cur_df).encode("utf-8"),
                           file_name=f"{ds_type}_standardized.json", use_container_width=True, key="dl_json_std")


# ============================================================
# Agent Studio Page
# ============================================================
def agent_studio_page():
    st.markdown(f"<div class='wow-card'><h3 style='margin:0'>{t(lang,'nav_agents')}</h3></div>", unsafe_allow_html=True)

    left, right = st.columns([1.2, 1.0], gap="large")

    with left:
        st.markdown(f"<div class='wow-mini'><b>{t(lang,'agent_yaml')}</b></div>", unsafe_allow_html=True)
        up = st.file_uploader(t(lang, "upload_yaml"), type=["yml", "yaml"], key="agents_upload_yaml")
        if up:
            st.session_state["agents_yaml_text"] = up.read().decode("utf-8", errors="ignore")

        st.session_state["agents_yaml_text"] = st.text_area(
            t(lang, "agent_yaml"),
            value=st.session_state["agents_yaml_text"],
            height=420,
            key="agents_yaml_editor",
        )

        cfg, err = load_agents_yaml(st.session_state["agents_yaml_text"])
        if err:
            st.error(f"{t(lang,'yaml_invalid')}: {err}")
        else:
            st.success(t(lang, "yaml_loaded"))
            st.session_state["agents_cfg"] = cfg
            safe_write_text(AGENTS_PATH, st.session_state["agents_yaml_text"])

        btn1, btn2 = st.columns([1, 1])
        with btn1:
            st.download_button(t(lang, "download_yaml"), dump_agents_yaml(st.session_state["agents_cfg"]),
                               file_name="agents.yaml", use_container_width=True, key="dl_agents_yaml")
        with btn2:
            if st.button(t(lang, "reset_agents"), use_container_width=True, key="reset_agents_btn"):
                st.session_state["agents_yaml_text"] = DEFAULT_AGENTS_YAML
                safe_write_text(AGENTS_PATH, DEFAULT_AGENTS_YAML)
                st.rerun()

    with right:
        st.markdown(f"<div class='wow-mini'><b>{t(lang,'agent_cards')}</b></div>", unsafe_allow_html=True)
        cfg = st.session_state["agents_cfg"]
        agents = cfg.get("agents", [])
        if not agents:
            st.info("No agents loaded.")
        else:
            for a in agents:
                st.markdown(
                    f"""
                    <div class="wow-card">
                      <div style="display:flex; justify-content:space-between; gap:12px; align-items:center;">
                        <div>
                          <div style="font-weight:900; font-size:16px;">{a.get('name','')}</div>
                          <div style="opacity:0.9; font-size:12px;">id: <span class="coral">{a.get('id','')}</span></div>
                          <div style="opacity:0.9; font-size:12px;">{a.get('description','')}</div>
                        </div>
                        <div style="text-align:right; font-size:12px;">
                          <div class="chip"><span class="dot"></span>{a.get('provider','')} / {a.get('model','')}</div>
                          <div style="opacity:0.9;">max_tokens: {a.get('max_tokens', '')}</div>
                        </div>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# ============================================================
# Command Center Page (Workspace + Agent Pipeline + Final Report)
# ============================================================
def command_center_page():
    st.markdown(f"<div class='wow-card'><h3 style='margin:0'>{t(lang,'workspace')}</h3></div>", unsafe_allow_html=True)

    left, right = st.columns([1.05, 1.0], gap="large")

    with left:
        st.markdown(f"<div class='wow-card'><h4 style='margin:0'>{t(lang,'source_material')}</h4></div>", unsafe_allow_html=True)

        mode = st.radio(
            t(lang, "input_mode"),
            [t(lang, "pdf"), t(lang, "text")],
            horizontal=True,
            index=0 if st.session_state["doc_input_mode"] == "PDF" else 1,
            key="doc_input_mode_radio",
        )
        st.session_state["doc_input_mode"] = "PDF" if mode == t(lang, "pdf") else "TEXT"

        if st.session_state["doc_input_mode"] == "PDF":
            up = st.file_uploader(t(lang, "upload_pdf"), type=["pdf"], key="doc_pdf_uploader")
            if up:
                st.session_state["pdf_bytes"] = up.read()
                st.session_state["trimmed_pdf_bytes"] = None
                st.session_state["raw_text"] = ""
                st.session_state["ocr_text"] = ""

            if st.session_state["pdf_bytes"]:
                with st.expander(t(lang, "trim_ocr"), expanded=True):
                    ranges = st.text_input(t(lang, "page_ranges"), value="1-2", key="doc_page_ranges")
                    render_preview = st.checkbox(t(lang, "render_preview"), value=True, key="doc_render_preview")

                    a, b = st.columns([1, 1])
                    with a:
                        if st.button(t(lang, "trim_extract"), use_container_width=True, key="doc_trim_extract"):
                            try:
                                pr = parse_page_ranges(ranges) or [(1, 1)]
                                trimmed = trim_pdf_bytes(st.session_state["pdf_bytes"], pr)
                                st.session_state["trimmed_pdf_bytes"] = trimmed
                                st.session_state["raw_text"] = extract_text_pypdf2(trimmed)
                                st.session_state["ocr_text"] = st.session_state["raw_text"]
                                st.success("Trim/Extract done.")
                            except Exception as e:
                                st.error(f"Trim/Extract failed: {e}")

                    with b:
                        trimmed = st.session_state["trimmed_pdf_bytes"] or st.session_state["pdf_bytes"]
                        st.download_button(t(lang, "download_trimmed"), data=trimmed, file_name="trimmed.pdf",
                                           use_container_width=True, key="doc_dl_trimmed")

                    if render_preview:
                        st.markdown(render_pdf_iframe(st.session_state["trimmed_pdf_bytes"] or st.session_state["pdf_bytes"]), unsafe_allow_html=True)

                    st.divider()
                    ocr_engine = st.selectbox(
                        t(lang, "ocr_engine"),
                        [t(lang, "extract_text"), t(lang, "local_ocr"), t(lang, "vision_ocr")],
                        index=0,
                        key="doc_ocr_engine",
                    )

                    # FIX: stable vision controls outside the button handler (only shown if needed)
                    vision_provider = st.session_state.get("doc_vision_provider", "openai")
                    vision_model = st.session_state.get("doc_vision_model", OPENAI_MODELS[0])

                    if ocr_engine == t(lang, "vision_ocr"):
                        vp = st.selectbox("Vision provider", ["openai", "gemini"], index=0 if vision_provider == "openai" else 1, key="doc_vision_provider_sel")
                        st.session_state["doc_vision_provider"] = vp
                        vm_list = provider_model_map()[vp]
                        default_ix = 0
                        if st.session_state.get("doc_vision_model") in vm_list:
                            default_ix = vm_list.index(st.session_state["doc_vision_model"])
                        vm = st.selectbox("Vision model", vm_list, index=default_ix, key="doc_vision_model_sel")
                        st.session_state["doc_vision_model"] = vm

                    if st.button(t(lang, "run_ocr"), use_container_width=True, key="doc_run_ocr"):
                        try:
                            pr = parse_page_ranges(ranges) or [(1, 1)]
                            base_pdf = st.session_state["trimmed_pdf_bytes"] or st.session_state["pdf_bytes"]
                            pdf_for_ocr = trim_pdf_bytes(base_pdf, pr)

                            if ocr_engine == t(lang, "extract_text"):
                                st.session_state["ocr_text"] = extract_text_pypdf2(pdf_for_ocr)

                            elif ocr_engine == t(lang, "local_ocr"):
                                images = convert_from_bytes(pdf_for_ocr, dpi=220)
                                pages = []
                                for i, img in enumerate(images, start=1):
                                    pages.append(f"\n\n--- PAGE {i} ---\n{pytesseract.image_to_string(img)}")
                                st.session_state["ocr_text"] = "\n".join(pages).strip()

                            else:
                                vprov = st.session_state.get("doc_vision_provider", "openai")
                                vmodel = st.session_state.get("doc_vision_model", provider_model_map()[vprov][0])
                                env_primary = {"openai": "OPENAI_API_KEY", "gemini": "GEMINI_API_KEY"}[vprov]
                                api_key, src = get_api_key(env_primary)
                                if not api_key:
                                    st.error(f"{env_primary} missing.")
                                else:
                                    images = convert_from_bytes(pdf_for_ocr, dpi=220)
                                    st.session_state["ocr_text"] = call_vision_ocr(vprov, vmodel, api_key, images, lang=lang, max_tokens=12000)

                            st.success("OCR completed.")
                        except Exception as e:
                            st.error(f"OCR failed: {e}")

        else:
            st.session_state["doc_text_override"] = st.text_area(
                t(lang, "paste_text"),
                value=st.session_state["doc_text_override"],
                height=420,
                key="doc_paste_text_area",
            )
            st.session_state["ocr_text"] = st.session_state["doc_text_override"]
            st.session_state["raw_text"] = st.session_state["doc_text_override"]

        st.divider()
        st.markdown(f"<div class='wow-mini'><b>{t(lang,'ocr_text')}</b></div>", unsafe_allow_html=True)
        st.session_state["ocr_text"] = st.text_area(
            t(lang, "ocr_text"),
            value=st.session_state["ocr_text"],
            height=200,
            key="doc_ocr_text_area",
        )
        st.markdown(f"<div class='wow-mini'><b>{t(lang,'raw_text')}</b></div>", unsafe_allow_html=True)
        st.session_state["raw_text"] = st.text_area(
            t(lang, "raw_text"),
            value=st.session_state["raw_text"],
            height=160,
            key="doc_raw_text_area",
        )

        if st.button(t(lang, "markdown_reconstruct"), use_container_width=True, key="doc_reconstruct_btn"):
            st.session_state["ocr_text"] = markdown_reconstruct(st.session_state["ocr_text"])
            st.success("Applied Markdown reconstruction.")

    with right:
        st.markdown(f"<div class='wow-card'><h4 style='margin:0'>{t(lang,'intelligence')}</h4></div>", unsafe_allow_html=True)
        tabs = st.tabs([t(lang, "agent_pipeline"), t(lang, "final_report"), t(lang, "results")])

        with tabs[0]:
            cfg = st.session_state["agents_cfg"]
            agents = cfg.get("agents", [])
            if not agents:
                st.warning("No agents loaded. Go to Agent Studio to edit agents.yaml.")
            else:
                agent_names = [f"{a.get('name','')} ({a.get('id','')})" for a in agents]
                pick = st.selectbox(t(lang, "agent"), agent_names, index=0, key="pipeline_agent_pick")
                agent = agents[agent_names.index(pick)]

                pmap = provider_model_map()
                provider = st.selectbox(t(lang, "provider"), list(pmap.keys()),
                                        index=list(pmap.keys()).index(agent.get("provider", "openai")) if agent.get("provider", "openai") in pmap else 0,
                                        key="pipeline_provider")
                model = st.selectbox(t(lang, "model"), pmap[provider], index=0, key="pipeline_model")
                max_tokens = st.number_input(t(lang, "max_tokens"), min_value=512, max_value=12000, value=12000, step=256, key="pipeline_max_tokens")
                temperature = st.slider(t(lang, "temperature"), 0.0, 1.0, float(agent.get("temperature", 0.2)), 0.05, key="pipeline_temp")

                system_prompt = st.text_area(t(lang, "system_prompt"), value=str(agent.get("system_prompt", "")), height=140, key="pipeline_system")
                user_prompt = st.text_area(t(lang, "user_prompt"), value=str(agent.get("user_prompt", "")), height=140, key="pipeline_user")

                last_edited = st.session_state["agent_runs"][-1]["edited_output"] if st.session_state["agent_runs"] else ""
                source = st.radio(
                    t(lang, "input_source"),
                    [t(lang, "use_last_output"), t(lang, "use_doc_text")],
                    index=0,
                    key="pipeline_input_source",
                )

                if source == t(lang, "use_last_output") and last_edited.strip():
                    base_input = last_edited
                else:
                    base_input = st.session_state["ocr_text"].strip() or st.session_state["raw_text"].strip()

                runA, runB = st.columns([1, 1])
                with runA:
                    if st.button(t(lang, "execute"), use_container_width=True, key="pipeline_execute"):
                        env_primary = {"openai": "OPENAI_API_KEY", "gemini": "GEMINI_API_KEY", "anthropic": "ANTHROPIC_API_KEY", "xai": "XAI_API_KEY"}[provider]
                        api_key, src = get_api_key(env_primary)
                        if not api_key:
                            st.error(f"{env_primary} missing.")
                        else:
                            full_system = (st.session_state["skill_md"].strip() + "\n\n" + system_prompt.strip()).strip()
                            full_user = f"{user_prompt.strip()}\n\n---\nINPUT:\n{base_input}"
                            try:
                                with st.spinner("Running agent..."):
                                    out = call_llm_text(provider, model, api_key, full_system, full_user,
                                                        max_tokens=int(max_tokens), temperature=float(temperature))
                                st.session_state["agent_runs"].append({
                                    "ts": datetime.datetime.utcnow().isoformat(),
                                    "agent_id": agent.get("id", ""),
                                    "agent_name": agent.get("name", ""),
                                    "provider": provider,
                                    "model": model,
                                    "max_tokens": int(max_tokens),
                                    "temperature": float(temperature),
                                    "system_prompt": system_prompt,
                                    "user_prompt": user_prompt,
                                    "input": base_input,
                                    "output": out,
                                    "edited_output": out,
                                    "view_mode": "markdown",
                                })
                                st.success("Agent completed.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Agent run failed: {e}")
                                st.code(traceback.format_exc())

                with runB:
                    if st.button(t(lang, "append_final"), use_container_width=True, key="pipeline_append_final"):
                        if st.session_state["agent_runs"]:
                            st.session_state["final_report"] = (st.session_state["final_report"].strip() + "\n\n" +
                                                                st.session_state["agent_runs"][-1]["edited_output"]).strip()
                            st.success("Appended.")
                            st.rerun()

                st.divider()
                if st.session_state["agent_runs"]:
                    for idx in range(len(st.session_state["agent_runs"]) - 1, -1, -1):
                        run = st.session_state["agent_runs"][idx]
                        st.markdown(
                            f"<div class='wow-mini'><b>Run {idx+1}</b> — {run['agent_name']} "
                            f"(<span class='coral'>{run['provider']}/{run['model']}</span>)</div>",
                            unsafe_allow_html=True,
                        )
                        subtabs = st.tabs([t(lang, "render"), t(lang, "edit_output_for_next")])
                        with subtabs[0]:
                            view = st.radio(
                                "View",
                                [t(lang, "markdown"), t(lang, "text_view")],
                                index=0 if run.get("view_mode", "markdown") == "markdown" else 1,
                                horizontal=True,
                                key=f"run_view_{idx}",
                            )
                            st.session_state["agent_runs"][idx]["view_mode"] = "markdown" if view == t(lang, "markdown") else "text"
                            if st.session_state["agent_runs"][idx]["view_mode"] == "markdown":
                                safe_md_render(run["output"])
                            else:
                                st.text_area("Output (text)", value=run["output"], height=260, key=f"run_text_{idx}")

                        with subtabs[1]:
                            st.session_state["agent_runs"][idx]["edited_output"] = st.text_area(
                                "Edited output",
                                value=run["edited_output"],
                                height=220,
                                key=f"run_edit_{idx}",
                            )

        with tabs[1]:
            rtabs = st.tabs([t(lang, "markdown"), t(lang, "render")])
            with rtabs[0]:
                st.session_state["final_report"] = st.text_area(
                    t(lang, "final_report"),
                    value=st.session_state["final_report"],
                    height=520,
                    key="final_report_md",
                )
            with rtabs[1]:
                safe_md_render(st.session_state["final_report"])

        with tabs[2]:
            total_hits = sum(len(v) for v in search_results.values())
            st.markdown(f"<div class='wow-mini'><b>{t(lang,'results')}</b> — {total_hits}</div>", unsafe_allow_html=True)
            if total_hits == 0:
                st.write("—")
            else:
                rows = []
                for ds, items in search_results.items():
                    for it in items[:80]:
                        r = dict(it.record)
                        r["_dataset"] = ds
                        r["_score"] = it.score
                        rows.append(r)
                st.dataframe(pd.DataFrame(rows).sort_values("_score", ascending=False), use_container_width=True, height=520)


# ============================================================
# Factory Page
# ============================================================
def factory_page():
    st.markdown(f"<div class='wow-card'><h3 style='margin:0'>{t(lang,'factory')}</h3></div>", unsafe_allow_html=True)

    root_dir = st.text_input(t(lang, "root_dir"), value="", key="factory_root_dir")
    zip_up = st.file_uploader(t(lang, "upload_zip"), type=["zip"], key="factory_zip")

    pdf_paths: List[str] = []
    tmp_dir = None

    if zip_up is not None:
        tmp_dir = tempfile.mkdtemp(prefix="pdf_factory_")
        zbytes = zip_up.read()
        with zipfile.ZipFile(io.BytesIO(zbytes), "r") as z:
            z.extractall(tmp_dir)
        pdf_paths = scan_pdfs(tmp_dir)
        st.caption(f"ZIP extracted to temp dir. PDFs found: {len(pdf_paths)}")
    elif root_dir.strip():
        pdf_paths = scan_pdfs(root_dir.strip())
        st.caption(f"PDFs found: {len(pdf_paths)}")

    if st.button(t(lang, "scan"), use_container_width=True, key="factory_scan_btn"):
        st.rerun()

    if pdf_paths:
        manifest = pd.DataFrame([{
            "file_name": os.path.basename(p),
            "path": p,
            "size_kb": int(os.path.getsize(p) / 1024),
        } for p in pdf_paths]).sort_values("file_name")
        st.session_state["factory_manifest"] = manifest

    if isinstance(st.session_state["factory_manifest"], pd.DataFrame) and not st.session_state["factory_manifest"].empty:
        st.markdown(f"<div class='wow-mini'><b>{t(lang,'manifest')}</b></div>", unsafe_allow_html=True)
        st.dataframe(st.session_state["factory_manifest"], use_container_width=True, height=260)

        st.divider()
        pmap = provider_model_map()
        prov = st.selectbox(t(lang, "provider"), ["openai", "gemini"], index=0, key="factory_provider")
        model = st.selectbox(t(lang, "model"), pmap[prov], index=0, key="factory_model")

        a, b, c = st.columns([1, 1, 1])
        with a:
            st.button(t(lang, "trim_page1"), use_container_width=True, key="factory_trim_btn")

        with b:
            if st.button(t(lang, "summarize"), use_container_width=True, key="factory_summarize_btn"):
                env_primary = {"openai": "OPENAI_API_KEY", "gemini": "GEMINI_API_KEY"}[prov]
                api_key, src = get_api_key(env_primary)
                if not api_key:
                    st.error(f"{env_primary} missing.")
                else:
                    items = []
                    manifest = st.session_state["factory_manifest"].copy()
                    with st.spinner("Batch summarizing..."):
                        for _, row in manifest.iterrows():
                            path = row["path"]
                            try:
                                trimmed = trim_first_page_to_bytes(path)
                                txt = extract_text_pypdf2(trimmed)
                                if not txt.strip():
                                    images = convert_from_bytes(trimmed, dpi=220)
                                    txt = pytesseract.image_to_string(images[0]) if images else ""
                                summary_md = summarize_cover(prov, model, api_key, txt[:9000], lang=lang)
                                items.append({"file_name": row["file_name"], "path": path, "summary_md": summary_md})
                            except Exception as e:
                                items.append({"file_name": row["file_name"], "path": path, "summary_md": f"**Error:** {e}"})
                    st.session_state["factory_items"] = items
                    st.success("Batch summarization complete.")

        with c:
            if st.button(t(lang, "generate_toc"), use_container_width=True, key="factory_toc_btn"):
                items = st.session_state.get("factory_items", [])
                if not items:
                    st.warning("No summaries yet. Run Summarize first.")
                else:
                    st.session_state["factory_toc_md"] = build_master_toc(items)
                    st.success("Master ToC generated.")

        if st.session_state.get("factory_toc_md"):
            st.divider()
            st.markdown(f"<div class='wow-mini'><b>Project_Master_ToC.md</b></div>", unsafe_allow_html=True)
            toc_tabs = st.tabs([t(lang, "markdown"), t(lang, "render")])
            with toc_tabs[0]:
                st.session_state["factory_toc_md"] = st.text_area("Master ToC Markdown", value=st.session_state["factory_toc_md"],
                                                                  height=360, key="factory_toc_editor")
                st.download_button("Download Project_Master_ToC.md", data=st.session_state["factory_toc_md"].encode("utf-8"),
                                   file_name="Project_Master_ToC.md", use_container_width=True, key="dl_master_toc")
            with toc_tabs[1]:
                safe_md_render(st.session_state["factory_toc_md"])

            if st.button(t(lang, "set_as_current_doc"), use_container_width=True, key="factory_set_doc_btn"):
                st.session_state["doc_input_mode"] = "TEXT"
                st.session_state["doc_text_override"] = st.session_state["factory_toc_md"]
                st.session_state["ocr_text"] = st.session_state["factory_toc_md"]
                st.session_state["raw_text"] = st.session_state["factory_toc_md"]
                st.success("Master ToC set as current document for agents.")
                st.rerun()


# ============================================================
# AI Note Keeper Page
# ============================================================
def note_keeper_page():
    st.markdown(f"<div class='wow-card'><h3 style='margin:0'>{t(lang,'note_keeper')}</h3></div>", unsafe_allow_html=True)

    left, right = st.columns([1.15, 1.0], gap="large")

    with left:
        st.markdown(f"<div class='wow-mini'><b>{t(lang,'paste_note')}</b></div>", unsafe_allow_html=True)
        st.session_state["note_raw"] = st.text_area("", value=st.session_state["note_raw"], height=220, key="note_raw_area")

        up = st.file_uploader(t(lang, "upload_note"), type=["txt", "md", "pdf"], key="note_upload")
        if up:
            b = up.read()
            name = up.name.lower()
            if name.endswith(".pdf"):
                st.session_state["note_raw"] = extract_text_pypdf2(b)
            else:
                st.session_state["note_raw"] = b.decode("utf-8", errors="ignore")

        st.markdown(f"<div class='wow-mini'><b>{t(lang,'ai_magics')}</b></div>", unsafe_allow_html=True)

        pmap = provider_model_map()
        provider = st.selectbox(t(lang, "provider"), list(pmap.keys()), index=0, key="note_provider")
        model = st.selectbox(t(lang, "model"), pmap[provider], index=0, key="note_model")
        max_tokens = st.number_input(t(lang, "max_tokens"), min_value=512, max_value=12000, value=6000, step=256, key="note_max_tokens")

        magic = st.selectbox("Magic", NOTE_MAGICS, index=0, key="note_magic_pick")

        with st.expander(t(lang, "style_ai_pick"), expanded=False):
            st.caption(t(lang, "style_ai_help"))
            if st.button(t(lang, "jackpot"), use_container_width=True, key="note_style_jackpot"):
                st.session_state["style"] = jackpot_style()
                st.rerun()

            if st.button("Recommend style with AI", use_container_width=True, key="note_style_ai"):
                env_primary = {"openai": "OPENAI_API_KEY", "gemini": "GEMINI_API_KEY", "anthropic": "ANTHROPIC_API_KEY", "xai": "XAI_API_KEY"}[provider]
                api_key, src = get_api_key(env_primary)
                if not api_key:
                    st.error(f"{env_primary} missing.")
                else:
                    ctx = "\n\n".join([
                        f"QUERY:\n{st.session_state.get('global_query','')}",
                        f"NOTE:\n{st.session_state.get('note_raw','')}",
                        f"DOC:\n{st.session_state.get('ocr_text','')}",
                    ]).strip()
                    chosen = choose_style_with_ai(provider, model, api_key, ctx, lang=lang)
                    if chosen:
                        st.session_state["style"] = chosen
                        st.success(f"{t(lang,'style_recommended')}: {chosen['name']}")
                        st.rerun()
                    else:
                        st.warning("AI returned unknown style id.")

        if magic != "AI Keywords Highlighter":
            if st.button(t(lang, "run_magic"), use_container_width=True, key="note_run_magic"):
                env_primary = {"openai": "OPENAI_API_KEY", "gemini": "GEMINI_API_KEY", "anthropic": "ANTHROPIC_API_KEY", "xai": "XAI_API_KEY"}[provider]
                api_key, src = get_api_key(env_primary)
                if not api_key:
                    st.error(f"{env_primary} missing.")
                else:
                    out = magic_run(magic, provider, model, api_key, st.session_state["note_raw"], lang=lang, max_tokens=int(max_tokens))
                    st.session_state["note_md"] = out
                    st.session_state["note_render_html"] = coral_highlight(out)
        else:
            st.caption(t(lang, "keyword_colors"))
            pairs = st.session_state["keyword_pairs"]
            for i in range(len(pairs)):
                ckw, ccol = st.columns([1.2, 0.8], vertical_alignment="center")
                with ckw:
                    pairs[i] = (st.text_input(f"{t(lang,'keywords')} #{i+1}", value=pairs[i][0], key=f"note_kw_{i}"), pairs[i][1])
                with ccol:
                    pairs[i] = (pairs[i][0], st.color_picker(f"Color #{i+1}", value=pairs[i][1], key=f"note_kc_{i}"))
            st.session_state["keyword_pairs"] = pairs

            if st.button(t(lang, "apply"), use_container_width=True, key="note_apply_keywords"):
                base = st.session_state["note_md"] or st.session_state["note_raw"]
                st.session_state["note_render_html"] = apply_keyword_colors(base, st.session_state["keyword_pairs"])

    with right:
        tabA, tabB, tabC = st.tabs([t(lang, "markdown"), t(lang, "text_view"), t(lang, "render")])
        with tabA:
            st.session_state["note_md"] = st.text_area("Markdown", value=st.session_state["note_md"], height=560, key="note_md_area")
        with tabB:
            st.session_state["note_raw"] = st.text_area("Text", value=st.session_state["note_raw"], height=560, key="note_text_area")
        with tabC:
            html = st.session_state["note_render_html"] or coral_highlight(st.session_state["note_md"] or st.session_state["note_raw"])
            st.markdown(f"<div class='wow-card editor-frame'>{html}</div>", unsafe_allow_html=True)


# ============================================================
# Page router
# ============================================================
if page == t(lang, "nav_dashboard"):
    dashboard_page()
elif page == t(lang, "nav_command"):
    command_center_page()
elif page == t(lang, "nav_datasets"):
    dataset_studio_page()
elif page == t(lang, "nav_agents"):
    agent_studio_page()
elif page == t(lang, "nav_factory"):
    factory_page()
else:
    note_keeper_page()
