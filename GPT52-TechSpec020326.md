Comprehensive Technical Specification — FDA Agentic AI System (“Regulatory Command Center”)
1. Executive Summary
The FDA Agentic AI System is a Streamlit-based “Regulatory Command Center” designed to support regulatory affairs specialists, medical device professionals, quality teams, and (optionally) reviewers in conducting rapid, defensible analysis of FDA-related datasets and regulatory documents. The system unifies four core FDA-oriented dataset families—510(k), Recalls, ADR/MDR (adverse events), and GUDID—within a single premium “WOW UI” experience that emphasizes clarity, speed, and a guided workflow.

The application provides two primary working modes:

Global Intelligence & Search: A multi-dataset global search that returns relevance-ranked results using fuzzy matching, and renders interactive visualizations (timeline and category distributions) to support quick exploration and triage.
Document Operating Room: A document-centric workspace for ingesting PDFs or text, trimming page ranges, extracting text and performing OCR (local or cloud vision), then running user-configurable agents sequentially. Users can edit agent outputs and reuse them as the input for the next agent, enabling controllable agentic workflows.
Beyond the core search and document pipeline, the system includes dedicated modules for:

Dataset Studio: Load datasets from default mock sets, paste content, or upload a file. Preview raw input, standardize schema into canonical fields, and use the standardized dataset in search and downstream analysis.
Agent Studio: Manage and validate agents.yaml (upload/edit/download/reset). Agents define reusable reasoning and summarization behaviors across multiple LLM providers and models.
Factory (Batch PDFs): Process batches of PDFs (from ZIP uploads or accessible directories), trim first pages, summarize each document cover page using an LLM, and compile a Master Table of Contents (ToC) for portfolio-level oversight. Users can then set the ToC as the “current document” and run agents on it.
AI Note Keeper: Paste or upload notes (text/markdown/PDF), transform into structured markdown with “AI Magics,” highlight keywords in custom colors, and optionally use “AI Magic” to choose a painter style for the UI theme based on the note/doc/query context.
The system is designed for deployment on Hugging Face Spaces. API keys are handled safely: when keys are provided via environment variables, the UI does not expose input fields; otherwise, users may input keys in-session. No API keys are written to persistent storage by design.

2. Goals and Non-Goals
2.1 Goals
Provide a premium, responsive “WOW UI” that feels like a modern command center.
Enable unified, cross-dataset search across FDA-related datasets with fuzzy matching.
Offer a robust document workflow for ingesting PDFs, trimming, OCR (local or cloud), normalization, and agent-driven analysis.
Provide agentic execution that is user-controlled, editable, and traceable (inputs/outputs kept in session state).
Support multiple LLM providers (OpenAI, Gemini, Anthropic, xAI) and allow users to select provider/model per run.
Provide batch processing for large PDF collections with Master ToC generation.
2.2 Non-Goals
The system does not attempt to be a legally authoritative reviewer. It supports analysis and drafting but must be used with expert oversight.
The system does not implement persistent user accounts, authentication, or multi-user collaboration (unless added later).
The system does not guarantee click-to-filter interactions on charts beyond rendering and exploration; interactivity is primarily visual.
3. Architecture Overview
The system uses a modular “micro-services-like” design implemented inside a single Streamlit application. Functionality is divided by concerns and routed via a navigation selector:

3.1 Presentation Layer (WOW UI)
Framework: Streamlit (Python).
Styling: Glassmorphism-inspired design via injected CSS:
Translucent cards, blur effects, accent gradients.
Default dark mode with optional light mode.
“Coral” (#FF7F50) as the global highlight color for risk/signal emphasis.
A secondary accent color derived from the selected painter style.
Theme controls:
Light/Dark theme toggle
Language toggle (English / Traditional Chinese)
20 painter-based styles, selectable via dropdown, random “Jackpot,” or “AI Magic: Pick Style.”
Status indicators:
API key status chips (env/session/missing)
Dataset counts
OCR readiness indicator
“Mana” style progress bar showing agent run count (a “WOW” playful status element)
3.2 Application Logic Layer
Session State Manager: Uses st.session_state as the unified store for:
UI preferences (theme/lang/style)
API keys (session-only)
loaded datasets (standardized DataFrames)
current document bytes/text/OCR output
agent definitions and YAML text
agent run history and final report
note keeper content and keyword coloring settings
factory/batch processing results
Search Engine: RegulatorySearchEngine orchestrates search across active datasets:
token-based fuzzy matching using rapidfuzz
dataset inclusion toggles
“exact match” mode option
scoring threshold controls
Agent Engine:
Loads agents.yaml
For each run, user selects provider/model and overrides prompts/tokens/temperature
Runs LLM calls and records outputs; output can be edited and passed forward to the next run
3.3 Data Processing Layer
Dataset Standardization:
Converts uploaded/pasted datasets into canonical schemas per dataset type (510k/recall/adr/gudid).
Uses field synonym mapping and fuzzy column-name matching to map non-standard columns.
Applies type normalization (e.g., booleans, list parsing, numeric parsing).
Document Pipeline:
PDF trimming and extraction via PyPDF2
OCR options:
text-layer extraction (PyPDF2)
local OCR via Tesseract (pytesseract + pdf2image)
cloud vision OCR using OpenAI or Gemini vision capability
Markdown reconstruction utility for cleaning OCR text into more readable structured text
Batch Processor (Factory):
Scans PDFs from ZIP or directory
Trims first page and extracts text
Summarizes each cover page via LLM
Aggregates summaries into a Master ToC markdown document
3.4 External Interfaces
LLM Providers:
OpenAI: uses openai responses API client
Gemini: uses google-generativeai
Anthropic: uses anthropic
xAI: uses OpenAI-compatible endpoint https://api.x.ai/v1
File Inputs:
PDF upload
dataset file upload (CSV/JSON/TXT)
notes upload (TXT/MD/PDF)
batch ZIP upload for Factory
4. Data Specifications
4.1 Default Datasets
A defaultsets.json file provides mock datasets and is loaded at startup when session datasets are empty. It contains:

datasets.510k: list of 510k records
datasets.recall: list of recall records
datasets.adr: list of adverse event records
datasets.gudid: list of GUDID device records
4.2 Canonical Schemas
The system standardizes datasets into canonical fields to ensure consistent search and visualization:

510(k) canonical fields (examples):

k_number, decision_date, decision, device_name, applicant, manufacturer_name, product_code, predicate_k_numbers, summary, etc.
Recall canonical fields:

recall_number, recall_class, event_date, termination_date, status, firm_name, product_code, reason_for_recall, quantity_in_commerce, etc.
ADR/MDR canonical fields:

adverse_event_id, report_date, event_type, patient_outcome, device_problem, narrative, recall_number_link, etc.
GUDID canonical fields:

primary_di, udi_di, device_description, manufacturer_name, brand_name, product_code, mri_safety, sterile, single_use, implantable, contains_nrl, etc.
4.3 Standardization Algorithm
Parse dataset blob (CSV/JSON/TXT) into a DataFrame.
Determine dataset type from user selection.
For each canonical field:
Try exact matching using normalized column names.
Else fuzzy match column names using rapidfuzz with threshold ≥ 85.
Generate a standardization mapping report for transparency.
Convert special types:
510k predicate_k_numbers to list
GUDID boolean fields to boolean/None
Recall quantity_in_commerce to int/None
Drop rows that are effectively empty across canonical fields.
5. Search & Visualization Engine
5.1 Search Workflow
Inputs:

Query string (global_query)
Dataset toggles (include/exclude 510k/recall/adr/gudid)
Match mode (exact vs fuzzy)
Fuzzy threshold slider (60–95)
Process:

For each dataset:
For each record:
compute a relevance score across selected text fields using fuzzy partial ratio or substring check
store records above threshold
Sort results by score descending
Special expansion:
If the query exactly matches a top 510k k_number, pull predicate K numbers into results (if present)
Outputs:

Per-dataset result lists limited to 200 records (for performance)
A merged results DataFrame for the dashboard view
5.2 Visualization
The Dashboard provides:

Timeline scatter: auto-select a date field if present (decision_date, event_date, report_date, publish_date).
Distribution pie/donut: auto-select a categorical field if present (device_class, recall_class, decision, panel, product_code, status, _dataset).
Bug fix requirement (implemented):
Streamlit can generate duplicate element IDs for Plotly charts when similar charts are rendered multiple times in different tabs. The system ensures uniqueness by passing explicit key= values for each plot (e.g., dash_510k_timeline, dash_510k_dist).

6. Document Operating Room (Workspace)
6.1 Input Modes
PDF mode:
Upload a PDF
Optionally trim pages by range (e.g., 1-2, 5)
Preview trimmed/original PDF in an iframe
Text mode:
Paste text
Treat it as the current document’s content (OCR/raw text)
6.2 Trim & Extract
Uses PyPDF2 to trim page ranges
Extracts text layer from trimmed PDF
Initializes OCR text equal to extracted text layer (until OCR is explicitly run)
6.3 OCR Options
User selects OCR engine:

Extract text (PyPDF2): fast, relies on embedded text layer
Local OCR (Tesseract):
Convert PDF pages to images using pdf2image
OCR via pytesseract.image_to_string
Cloud Vision OCR:
Convert pages to images
Send images to OpenAI or Gemini vision-capable endpoints
Return extracted plain text
To prevent widget instability and state errors, the system keeps Vision provider/model selectors stable and outside the OCR button handler.

6.4 Markdown Reconstruction
A lightweight formatter helps make OCR output more readable:

normalizes whitespace
standardizes bullet points
attempts to convert uppercase lines into headings
This step is conservative and does not invent missing content.

7. Agent Pipeline Execution
7.1 Agent Definitions
Agents are defined in agents.yaml and loaded into session. Each agent includes:

id, name, description
provider, model
temperature, max_tokens
system_prompt, user_prompt
7.2 Execution Flow
User chooses an agent
User can override provider/model/tokens/temperature and edit system/user prompts
User selects input source:
last edited output (preferred for chaining)
current document text (OCR preferred)
System composes final prompts:
shared system prompt from SKILL.md (prepended)
agent system prompt
agent user prompt + injected input text
LLM call is executed
Output is stored with metadata:
agent id/name, provider/model, prompts, max tokens, temperature, input, output
Output can be edited and becomes optional input to subsequent runs
User may append the latest edited output to a Final Report markdown area
7.3 Output Rendering
Markdown outputs are rendered with coral keyword highlighting using an ontology list (e.g., “warning,” “contraindication,” “recall,” “latex,” “death”).
Users can also view raw text output where needed.
8. Agent Studio
The Agent Studio provides configuration management:

Upload YAML
Edit YAML directly (text area)
Validate and standardize agent objects using heuristic mapping
Download standardized YAML
Reset to defaults
The system is designed to be resilient to non-standard YAML structures by attempting to map alternative keys (e.g., instructions → system_prompt) and fill defaults conservatively. It also refuses to silently accept invalid agents (e.g., missing id or system_prompt).

9. Dataset Studio
Dataset Studio is a controlled ingestion and normalization interface:

Data source options:
default: load from defaultsets.json
paste: paste CSV/JSON, parse, preview
upload: upload CSV/JSON/TXT, parse, preview
Standardization step converts to canonical schema and records a mapping report.
Standardized dataset is saved into session state and becomes available for global search and analysis.
Download standardized CSV/JSON to support offline analysis and audit.
10. Factory (Batch PDFs)
The Factory module supports portfolio-level oversight:

Input:
root directory (if accessible in runtime)
ZIP upload containing PDFs (works reliably on Spaces)
Process:
scan PDFs
display manifest table (name/path/size)
summarize first page for each PDF:
trim first page
extract text layer; if empty, fallback to local OCR for that page
LLM summarization into 3 sentences (device, firm, indication)
Output:
Master ToC markdown document aggregating summaries
Option to download Project_Master_ToC.md
Option to set Master ToC as the current document for agent analysis
This enables an “overview-first” approach to large submissions or document libraries.

11. AI Note Keeper
AI Note Keeper is optimized for unstructured notes:

Input:
paste text/markdown
upload TXT/MD/PDF
Actions:
“AI Magics” to transform content into structured markdown (organize, summary, action items, risk finder, checklist)
Keyword highlighting with user-chosen colors
UI Theme “AI Magic”:
uses note/query/doc content to select a painter style via LLM
allows random “Jackpot” selection
This mode is ideal for meeting notes, review notes, or copied excerpts that must be cleaned into a usable artifact.

12. API Key Management and Privacy
The system supports secure key handling patterns aligned with Hugging Face Spaces:

Environment variable keys are preferred:
OPENAI_API_KEY, GEMINI_API_KEY (or GOOGLE_API_KEY), ANTHROPIC_API_KEY, XAI_API_KEY
If a key is present via environment:
the UI does not show an input field (prevents accidental exposure)
status displays “Authenticated via Environment”
If missing:
user may enter a key in session, stored only in st.session_state['api_keys']
The system does not persist keys to disk, logs, or downloads.
13. Deployment Specification (Hugging Face Spaces)
13.1 Runtime and Packages
Python runtime supported by Spaces
requirements.txt includes Streamlit, data libs, LLM SDKs, OCR/PDF libraries, Plotly
13.2 System Packages
For OCR and PDF rendering:

poppler-utils for pdf2image
tesseract-ocr for local OCR
13.3 Storage
Application may read:
defaultsets.json, agents.yaml, SKILL.md
Writes are best-effort (may be disabled in some environments), so the system relies on session state for runtime edits.
14. Error Handling and Known Limitations
14.1 Fixed Issue: Duplicate Plotly Element IDs
Streamlit can raise StreamlitDuplicateElementId when charts are rendered in repeated contexts. The system resolves this by attaching unique key= values to each st.plotly_chart.

14.2 Limitations
Fuzzy search is row-by-row scanning; large datasets may become slow. For production-scale datasets, a dedicated index (e.g., vector DB, text index) is recommended.
Batch processing depends on compute and token budgets; summarization runs may be rate-limited by providers.
OCR quality depends on PDF quality and page scans; cloud vision OCR is more accurate but costs more.
15. Roadmap and Enhancement Opportunities
Add click-to-filter chart interactions via Streamlit selection events or Plotly selection callbacks.
Add caching for rendered PDF previews and OCR results to reduce rerun costs.
Add a persistent “Case” abstraction that saves document + outputs + datasets as an exportable bundle.
Add agent chaining presets (pipelines) and automated multi-step workflows.
Add audit exports: a zipped artifact containing prompts, model choices, timestamps, and outputs for compliance traceability.
Add advanced dataset linking views (e.g., product_code networks, recall-to-ADR propagation views).
Add schema inference to auto-detect dataset type when uploading unknown files.
20 follow-up questions
Should the spec mandate chart click-to-filter behavior (true interactivity), or keep the current dashboard “visual + table” approach as sufficient for v1?
Do you want a formal “Case” entity (case list, save/load, export/import) instead of the current single-session workflow?
Should agent runs be persisted as a downloadable audit bundle (JSON + markdown + metadata) for compliance documentation?
For search at scale, should we add a roadmap item for indexing (e.g., SQLite FTS, Whoosh, or vector search) rather than row scanning?
Should dataset standardization include an optional LLM-based column mapping when synonym/fuzzy mapping is weak?
Do you want explicit date range filtering wired into search, including per-dataset date fields and UI controls?
Should the document pipeline include a “smart OCR” mode: text-layer extraction first, then OCR only pages with low text density?
Should we add a built-in OCR Quality score and highlight pages likely needing manual correction?
Do you want a dedicated Agent Pipeline Designer UI that can execute a multi-step chain automatically with checkpoints?
Should the system support multiple agent packs (e.g., “510(k) Review,” “Safety Surveillance,” “QMS/CAPA”) with quick switching?
Do you want the Note Keeper to support saving multiple notes (note library) and linking notes to cases/documents?
Should the “Coral keyword ontology” be editable via UI and persisted (project dictionary) rather than hardcoded?
Do you want a “Result Cards” view (glass cards with action buttons) in addition to dataframes for a more premium results page?
Should Factory support multi-page trim rules (first N pages, ToC detection, keyword-based page selection) rather than only page 1?
Should Factory produce per-document structured JSON summaries (fields: device/firm/indication) for downstream analysis?
Do you want a cross-dataset “Device 360” page that explicitly links by product_code, udi_di, and manufacturer_name with visual graphs?
Should model selection be constrained by capability tags (vision, long context) to prevent invalid combinations?
Do you want streaming outputs (token streaming) for agent runs to increase “alive” feeling, or is spinner-based completion acceptable?
Should the UI support localized language beyond zh-TW and English (e.g., Japanese) using the same i18n structure?
Should the system include a “One-click Executive Report” generator that compiles dashboard insights + agent outputs into a standardized template automatically?
