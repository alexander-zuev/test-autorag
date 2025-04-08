# AutoRAG + Firecrawl Test Plan: Chat with Documentation

## Goal

Evaluate the effectiveness of Cloudflare AutoRAG for building a Q&A system over specific web documentation, using Firecrawl for content ingestion.

## Scope

1.  Crawl one or more pages from a target documentation site (e.g., `fastapi.tiangolo.com` or `developers.cloudflare.com/workers/`) using Firecrawl.
2.  Index the crawled content using Cloudflare AutoRAG.
3.  Test the RAG pipeline by asking relevant questions via the AutoRAG Playground.

## Key Steps

1.  **Crawl Content (Firecrawl -> HTML):**
    *   **How:** Use the Firecrawl **`crawl`** API endpoint (via Python `firecrawl-py` library).
    *   **Input:** Target documentation starting URL and crawl parameters (e.g., `max_pages`).
    *   **Output:** Request **HTML** format. Save **each crawled page's HTML** content locally into separate files (e.g., `page_1.html`, `page_2.html`, ...).

2.  **Upload Content to R2:**
    *   **How:** Use R2 REST API (via Python `httpx`).
    *   **Input:** The saved HTML files from Step 1.
    *   **Destination:** A designated R2 bucket (e.g., `autorag-firecrawl-test-docs`). Upload each file.

3.  **Configure AutoRAG:**
    *   **How:** Via Cloudflare Dashboard (AI > AutoRAG > Create).
    *   **Settings:**
        *   **Data Source:** Point to the R2 bucket containing the multiple HTML files.
        *   **Models:** Use default embedding and LLM models initially.
        *   **Name:** Assign a descriptive name (e.g., `firecrawl-docs-rag`).
    *   **Action:** Wait for indexing to complete (monitor status in dashboard).

4.  **Test & Evaluate:**
    *   **How:** Use the AutoRAG **Playground** tab in the Cloudflare dashboard.
    *   **Input:** Ask specific questions based on the crawled documentation content.
    *   **Evaluation:** Assess the relevance, accuracy, and coherence of the generated answers. Check if the answers correctly reference the source content.