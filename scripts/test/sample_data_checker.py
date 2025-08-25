#!/usr/bin/env python3
"""
Simple URL checker script for Recipe Robot sample data.
Checks URLs in the sample data and reports any that result in errors.
Uses asyncio.gather() for concurrent URL checking.
"""

import asyncio
import aiohttp
import sys
import yaml
from pathlib import Path
from urllib.parse import urlparse


def load_sample_data(file_path):
    """Load sample data from YAML file."""
    try:
        with open(file_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading sample data: {e}")
        return []


def is_url(path):
    """Check if a path is a URL (not a local file path)."""
    parsed = urlparse(path)
    return parsed.scheme in ("http", "https")


async def check_url(session, url, timeout=10):
    """Check if a URL is accessible asynchronously."""
    try:
        async with session.get(
            url, timeout=aiohttp.ClientTimeout(total=timeout)
        ) as response:
            return True, response.status, None
    except aiohttp.ClientError as e:
        return False, None, f"Client Error: {str(e)}"
    except asyncio.TimeoutError:
        return False, None, f"Timeout after {timeout} seconds"
    except Exception as e:
        return False, None, f"Unexpected error: {str(e)}"


async def check_urls_concurrently(urls_data):
    """Check multiple URLs concurrently using asyncio.gather()."""
    connector = aiohttp.TCPConnector(limit=20)  # Limit concurrent connections
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        # Create tasks for all URL checks
        tasks = []
        for url, app_name in urls_data:
            task = check_url(session, url)
            tasks.append((task, url, app_name))

        print(f"Checking {len(tasks)} URLs concurrently...")
        print("-" * 80)

        # Use asyncio.gather to run all checks concurrently
        task_list = [task for task, _, _ in tasks]
        results = await asyncio.gather(*task_list, return_exceptions=True)

        # Process and display results
        checked_results = []
        for i, result in enumerate(results):
            _, url, app_name = tasks[i]

            if isinstance(result, Exception):
                success, status_code, error_msg = (
                    False,
                    None,
                    f"Exception: {str(result)}",
                )
            elif isinstance(result, tuple) and len(result) == 3:
                success, status_code, error_msg = result
            else:
                success, status_code, error_msg = (
                    False,
                    None,
                    f"Unexpected result: {result}",
                )

            checked_results.append((app_name, url, success, status_code, error_msg))

            # Print result immediately
            print(f"Checking: {app_name}")
            print(f"  URL: {url}")
            if success:
                print(f"  ✓ OK (Status: {status_code})")
            else:
                print(f"  ✗ ERROR: {error_msg}")
            print()

        return checked_results


async def main_async():
    """Main async function to check URLs in sample data."""
    # Get the script directory and find sample data
    script_dir = Path(__file__).parent
    sample_data_path = script_dir / "test" / "sample_data.yaml"

    if not sample_data_path.exists():
        print(f"Error: Sample data file not found at {sample_data_path}")
        return 1

    print("Loading sample data...")
    sample_data = load_sample_data(sample_data_path)

    if not sample_data:
        print("No sample data found or failed to load.")
        return 1

    print(f"Found {len(sample_data)} entries in sample data.")

    # Extract URLs from sample data
    urls_to_check = []
    for item in sample_data:
        if not isinstance(item, dict) or "input_path" not in item:
            continue

        input_path = item["input_path"]
        app_name = item.get("app_name", "Unknown")

        # Only check URLs, skip local file paths
        if is_url(input_path):
            urls_to_check.append((input_path, app_name))

    if not urls_to_check:
        print("No URLs found in sample data.")
        return 0

    # Check all URLs concurrently
    results = await check_urls_concurrently(urls_to_check)

    # Calculate summary
    total_urls = len(results)
    error_results = [
        (app_name, url, error_msg)
        for app_name, url, success, _, error_msg in results
        if not success
    ]
    error_count = len(error_results)

    print("-" * 80)
    print("Summary:")
    print(f"  Total URLs checked: {total_urls}")
    print(f"  Successful: {total_urls - error_count}")
    print(f"  Errors: {error_count}")

    if error_count > 0:
        print("\nError URLs:")
        for app_name, url, error_msg in error_results:
            print(f"  • {app_name}: {url}")
            print(f"    Error: {error_msg}")
        return 1
    else:
        print("\nAll URLs are accessible!")
        return 0


def main():
    """Main function wrapper for async execution."""
    return asyncio.run(main_async())


if __name__ == "__main__":
    sys.exit(main())
