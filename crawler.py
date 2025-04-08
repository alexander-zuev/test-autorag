import asyncio
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from firecrawl import FirecrawlApp
from pydantic import BaseModel, Field

from logger import configure_logging, get_logger
from settings import settings

configure_logging()
logger = get_logger("crawler")

# --- Pydantic Models for Parameters ---


class FirecrawlScrapeOptions(BaseModel):
    """Options specific to the scraping process within a crawl."""

    formats: List[str] = Field(default=["rawHtml"], description="Formats to retrieve (only HTML needed)")
    remove_base64_images: bool = Field(
        default=True, alias="removeBase64Images", description="Exclude base64 encoded images"
    )
    only_main_content: bool = Field(default=True, alias="onlyMainContent", description="Extract main content only")
    # Add other scrape options if needed, e.g., includeTags, excludeTags

    class Config:
        populate_by_name = True  # Allows using either snake_case or alias


class FirecrawlCrawlParams(BaseModel):
    """Parameters for the Firecrawl crawl operation."""

    limit: Optional[int] = Field(default=10, description="Maximum number of pages to crawl")
    max_depth: Optional[int] = Field(default=5, alias="maxDepth", description="Maximum depth relative to the base URL")
    # include_paths: Optional[List[str]] = Field(default=None, alias="includePaths", description="URL patterns to include")
    # exclude_paths: Optional[List[str]] = Field(default=None, alias="excludePaths", description="URL patterns to exclude")
    scrape_options: FirecrawlScrapeOptions = Field(default_factory=FirecrawlScrapeOptions, alias="scrapeOptions")

    class Config:
        populate_by_name = True  # Allows using either snake_case or alias


# --- Crawler Class ---


class Crawler:
    """Manages Firecrawl API interactions for crawling websites."""

    def __init__(self) -> None:
        self.app: FirecrawlApp = FirecrawlApp(api_key=settings.firecrawl_api_key)
        logger.info("FirecrawlApp initialized.")

    async def start_crawl(self, start_url: str, params: FirecrawlCrawlParams) -> str | None:
        """Starts an async crawl job and returns the job ID."""
        logger.info(
            f"Starting crawl for: {start_url} with params: {params.model_dump(exclude_none=True, by_alias=True)}"
        )
        try:
            # Use model_dump to get dict matching API schema (handles aliases)
            crawl_result = self.app.async_crawl_url(
                url=start_url,
                params=params.model_dump(exclude_none=True, by_alias=True),
            )
            job_id = crawl_result.get("id")  # Note: Key is 'id' based on SDK source
            if job_id:
                logger.info(f"Crawl job started successfully. Job ID: {job_id}")
                return job_id
            else:
                logger.error(f"Failed to start crawl job for {start_url}. Response: {crawl_result}")
                return None
        except Exception as e:
            logger.exception(f"Error starting crawl job for {start_url}: {e}")
            return None

    async def check_crawl_status(self, job_id: str) -> Dict[str, Any] | None:
        """Checks the status of a crawl job."""
        logger.debug(f"Checking status for job ID: {job_id}")
        try:
            status_data = self.app.check_crawl_status(job_id)
            logger.debug(f"Status for job {job_id}: {status_data.get('status')}")
            return status_data
        except Exception as e:
            logger.exception(f"Error checking status for job ID {job_id}: {e}")
            return None

    async def save_crawl_results(self, crawl_data: List[Dict[str, Any]], output_dir: str) -> int:
        """Saves the HTML content from crawl data to files."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        saved_count = 0
        logger.info(f"Saving crawl results to directory: {output_dir}")

        for i, page_data in enumerate(crawl_data):
            html_content = page_data.get("rawHtml")
            source_url = page_data.get("metadata", {}).get("sourceURL", f"unknown_url_{i}")

            if not html_content:
                logger.warning(f"No HTML content found for page {i + 1} (URL: {source_url})")
                continue

            # Generate a unique filename
            filename = f"page_{uuid.uuid4()}.html"
            filepath = output_path / filename

            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(html_content)
                logger.debug(f"Saved HTML for {source_url} to {filepath}")
                saved_count += 1
            except IOError as e:
                logger.error(f"Failed to write file {filepath} for {source_url}: {e}")
            except Exception as e:
                logger.exception(f"An unexpected error occurred while saving {filepath}: {e}")

        logger.info(f"Successfully saved {saved_count} HTML files out of {len(crawl_data)} results.")
        return saved_count


# --- Main Execution Example (Async) ---


async def main(start_url: str, output_dir: str, limit: int = 10):
    """Main async function to run the crawl process."""
    crawler = Crawler()
    crawl_params = FirecrawlCrawlParams(limit=limit)

    job_id = await crawler.start_crawl(start_url, crawl_params)

    if not job_id:
        logger.error("Failed to start crawl job. Exiting.")
        return

    logger.info(f"Monitoring crawl job: {job_id} (checking status every 10 seconds)")
    while True:
        status_data = await crawler.check_crawl_status(job_id)
        if not status_data:
            logger.error(f"Failed to get status for job {job_id}. Exiting monitor loop.")
            break

        status = status_data.get("status")
        completed_count = status_data.get("completed", 0)
        total_count = status_data.get("total", 0)
        logger.info(f"Job {job_id} status: {status} ({completed_count}/{total_count} pages completed)")

        if status == "completed":
            logger.info(f"Crawl job {job_id} completed.")
            crawl_results = status_data.get("data", [])
            if crawl_results:
                await crawler.save_crawl_results(crawl_results, output_dir)
            else:
                logger.warning(f"Crawl job {job_id} completed but no data was returned.")
            break
        elif status == "failed":
            logger.error(f"Crawl job {job_id} failed. Status data: {status_data}")
            # Optionally check for errors: crawler.app.get_crawl_errors(job_id)
            break
        elif status == "scraping":
            await asyncio.sleep(10)  # Wait before checking status again
        else:
            logger.warning(f"Unknown status '{status}' for job {job_id}. Status data: {status_data}")
            await asyncio.sleep(10)


if __name__ == "__main__":
    # --- Configuration ---
    TARGET_START_URL = "https://modelcontextprotocol.io/docs/"
    OUTPUT_DIRECTORY = "crawled_html"
    PAGE_LIMIT = 2  # Max pages to crawl
    # ---------------------

    asyncio.run(main(TARGET_START_URL, OUTPUT_DIRECTORY, limit=PAGE_LIMIT))
