from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from logger import configure_logging, get_logger
from settings import settings

# Setup logging
configure_logging()
logger = get_logger("upload_data")  # Using logger.py

# Constants
CRAWL_OUTPUT_DIR = Path(__file__).parent / "crawled_html"


def upload_files_to_r2():
    """
    Lists HTML files in the crawled_html directory and uploads them to R2.
    """
    endpoint_url = f"https://{settings.r2_account_id}.r2.cloudflarestorage.com"
    # Reading bucket name and keys from settings
    if (
        not endpoint_url
        or not settings.r2_bucket_name
        or not settings.r2_access_key_id
        or not settings.r2_secret_access_key
    ):
        logger.error(
            "Missing necessary R2 configuration (Account ID, Bucket Name, Access Key, or Secret Key). Cannot proceed."
        )
        return

    if not CRAWL_OUTPUT_DIR.is_dir():
        logger.error(f"Directory not found: {CRAWL_OUTPUT_DIR}")
        return

    logger.info(f"Connecting to R2 bucket: {settings.r2_bucket_name} at {endpoint_url}")
    try:
        # Using client is generally preferred for explicit operations
        s3_client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            region_name="auto",  # Standard R2 setting
        )
        logger.info("Successfully created R2 client.")
    except Exception as e:
        logger.error(f"Failed to create R2 client: {e}")
        return

    logger.info(f"Scanning directory for HTML files: {CRAWL_OUTPUT_DIR}")
    try:
        files_to_upload = list(CRAWL_OUTPUT_DIR.glob("*.html"))
    except OSError as e:
        logger.error(f"Error accessing directory {CRAWL_OUTPUT_DIR}: {e}")
        return

    if not files_to_upload:
        logger.warning(f"No HTML files found in {CRAWL_OUTPUT_DIR}. Nothing to upload.")
        return

    logger.info(f"Found {len(files_to_upload)} HTML files to upload.")

    success_count = 0
    failure_count = 0

    for file_path in files_to_upload:
        object_key = file_path.name  # Use the filename as the key in R2
        logger.debug(f"Attempting to upload {file_path} to {settings.r2_bucket_name}/{object_key}")
        try:
            # upload_file handles opening/reading the file
            s3_client.upload_file(
                Filename=str(file_path),
                Bucket=settings.r2_bucket_name,
                Key=object_key,
                ExtraArgs={"ContentType": "text/html"},  # Set content type
            )
            logger.info(f"Successfully uploaded {object_key}")
            success_count += 1
        except ClientError as e:
            logger.error(f"Failed to upload {object_key}: {e}")
            failure_count += 1
        except FileNotFoundError:
            logger.error(f"File not found during upload attempt: {file_path}")
            failure_count += 1
        except Exception as e:
            logger.error(f"An unexpected error occurred uploading {object_key}: {e}")
            failure_count += 1

    logger.info("----- Upload Summary -----")
    logger.info(f"Successful uploads: {success_count}")
    logger.info(f"Failed uploads:    {failure_count}")
    logger.info("--------------------------")


if __name__ == "__main__":
    logger.info("Starting R2 upload process...")
    # Basic check within the function handles missing settings
    upload_files_to_r2()
    logger.info("R2 upload process finished.")
