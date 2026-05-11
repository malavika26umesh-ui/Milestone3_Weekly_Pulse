# Weekly Product Review Pulse — Implementation Plan

This document outlines the phased roadmap for building the automated weekly review system. Each phase includes specific tasks and exit criteria to ensure modularity and quality.

---

## Phase 1: Foundation & Data Ingestion
**Goal**: Establish the project structure and build reliable scrapers for App Store and Google Play.

### Tasks
1.  **Environment Setup**: Initialize Python 3.10+ project with `poetry` or `venv`. Setup `.env` for API keys (OpenAI/Google) and internal configs.
2.  **Data Models**: Implement `Pydantic` models for `Review` and `ProductConfig`.
3.  **App Store Module**: Implement a fetcher using the iTunes RSS feed with pagination support.
4.  **Play Store Module**: Implement a scraper using `google-play-scraper`.
5.  **Data Normalization**: Create a unified pipeline that merges reviews from both sources into a single schema.

**Exit Criteria**: A CLI script that can fetch and save raw reviews for a specific product and ISO week to a local JSON file.

---

## Phase 2: ML & AI Processing Pipeline
**Goal**: Transform raw text into structured themes using clustering and LLMs.

### Tasks
1.  **PII Scrubber**: Implement Regex-based and basic NER scrubbing for phone numbers, emails, and names.
2.  **Embedding Layer**: Integrate `sentence-transformers` to generate vectors for scrubbed reviews.
3.  **Clustering Engine**: 
    *   Implement `UMAP` for dimensionality reduction.
    *   Implement `HDBSCAN` for grouping reviews.
4.  **LLM Integration**: 
    *   Develop system prompts for theme naming and insight generation using Gemini 1.5 Flash.
    *   Implement structured output parsing (JSON mode).
5.  **Quote Validator**: Build a utility to verify that LLM-selected quotes exist verbatim in the source reviews.

**Exit Criteria**: A processing script that takes raw reviews and outputs a `PulseReport` JSON object containing themes, count, and validated quotes.

---

## Phase 3: State Management & Idempotency
**Goal**: Ensure the system is resilient and doesn't produce duplicate outputs.

### Tasks
1.  **SQLite Setup**: Create `pulse_state.db` with the `pulse_runs` table.
2.  **Persistence Layer**: Build an internal API to record run status (`STARTED`, `SUCCESS`, `FAILED`) and metadata.
3.  **Idempotency Checks**: Integrate a pre-run check in the orchestrator to skip already-processed (Product, Week) pairs.

**Exit Criteria**: Re-running the ingestion/processing script for the same week results in a "Skip" message and no new processing.

---

## Phase 4: MCP Integration (Google Docs)
**Goal**: Enable the agent to securely write reports to Google Docs via FastMCP.

### Tasks
1.  **FastMCP Server Setup**: Create a custom `FastMCP` server for Google Docs with OAuth2 credentials.
2.  **Markdown to Doc Conversion**: Implement logic to translate the `PulseReport` object into styled Markdown.
3.  **Docs Client**: Implement the MCP client call to `append_to_document` tool.
4.  **Template Management**: Ensure each product has a designated "System of Record" Google Doc.

**Exit Criteria**: Successful appending of a dummy report to a real Google Doc via the FastMCP server.

---

## Phase 5: MCP Integration (Gmail)
**Goal**: Automate stakeholder notifications with deep links to the Doc.

### Tasks
1.  **Gmail FastMCP Setup**: Create a custom `FastMCP` server for Gmail.
2.  **Email Templating**: Build HTML templates for the "teaser" email (Top themes + Link).
3.  **Deep Linking**: Implement logic to extract the Heading ID from the Docs MCP response and construct a URL anchor.
4.  **Draft Flow**: Implement the `create_pulse_draft` tool call via Gmail FastMCP.

**Exit Criteria**: A draft email appears in the "Drafts" folder with a functional link pointing to the correct section in the Google Doc.

---

## Phase 6: Orchestration & CLI
**Goal**: Tie everything together into a production-ready application.

### Tasks
1.  **Main Orchestrator**: Build the top-level loop that coordinates between Ingestion, Processing, and Delivery.
2.  **CLI Interface**: 
    *   `run --product [NAME] --week [ISO_WEEK]`
    *   `backfill --product [NAME] --weeks [N]`
3.  **Error Handling**: Implement retries for network calls and "Graceful Degradation" (e.g., skip email if Docs append fails).
4.  **Logging**: Setup structured logging to file and console.

**Exit Criteria**: A single CLI command completes the entire pipeline for a product, from scraping to Gmail draft creation.

---

## Phase 7: Testing & Refinement
**Goal**: Ensure high-quality insights and operational stability.

### Tasks
1.  **LLM Quality QA**: Review generated themes for accuracy and actionable value.
2.  **Performance Tuning**: Optimize UMAP/HDBSCAN parameters for different review volumes.
3.  **End-to-End Simulation**: Run a full backfill for 4 weeks for one product and verify the Google Doc structure.
4.  **Documentation**: Finalize README and operational guides.

**Exit Criteria**: System passes a full end-to-end "Dry Run" for all initial supported products (Groww, INDMoney, etc.).

---

## Phase 8: Automation & Monitoring
**Goal**: Ensure the system runs reliably without manual intervention and maintains health.

### Tasks
1.  **GitHub Actions Setup**: Create `weekly_pulse.yml` with a CRON trigger for Monday mornings.
2.  **Secret Management**: Encode `credentials.json` and `token.json` files to Base64 and store as GitHub Repo Secrets.
3.  **Dependency Hardening**: Create `requirements.txt` with pinned versions to prevent breaking changes in the CI environment.
4.  **Artifact Archiving**: Configure the workflow to upload local HTML/MD previews as build artifacts for auditability.

**Exit Criteria**: Successful "Scheduled" run in GitHub Actions that produces a Google Doc append and a Gmail draft.
