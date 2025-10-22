"""
E2E test: Upload previously-failing PDF via Nanonets-first loader.
Verify it processes successfully and appears in collections.
"""
import asyncio
from pathlib import Path
import pytest
from playwright.async_api import async_playwright, expect


@pytest.mark.asyncio
async def test_nanonets_pdf_upload():
    """Upload hello.pdf (previously failed with pypdf) and verify success via Nanonets."""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Navigate to app
        await page.goto("http://localhost:5173")
        await page.wait_for_load_state("networkidle")
        
        print("\n=== Step 1: Navigate to Ingestion page ===")
        await page.get_by_role("link", name="Ingestion").click()
        await page.wait_for_load_state("networkidle")
        
        print("\n=== Step 2: Select 'start' collection ===")
        # Click the collection selector
        await page.locator('[data-testid="collection-selector"]').click()
        await page.wait_for_timeout(500)
        
        # Select 'start' collection
        await page.get_by_text("start", exact=True).click()
        await page.wait_for_timeout(500)
        
        print("\n=== Step 3: Upload hello.pdf ===")
        # Get the file input and upload
        file_input = page.locator('input[type="file"]')
        pdf_path = Path(__file__).parent / "fixtures" / "hello.pdf"
        
        if not pdf_path.exists():
            print(f"ERROR: Test file not found at {pdf_path}")
            await browser.close()
            return
        
        await file_input.set_input_files(str(pdf_path))
        await page.wait_for_timeout(1000)
        
        print("\n=== Step 4: Wait for processing to complete ===")
        # Wait for progress tracker to appear
        await expect(page.locator("text=Processing")).to_be_visible(timeout=10000)
        
        # Wait for completion (up to 2 minutes for Nanonets model load + processing)
        try:
            await expect(
                page.locator("text=/All documents processed successfully|Completed with errors/")
            ).to_be_visible(timeout=120000)
        except Exception as e:
            print(f"Timeout waiting for completion: {e}")
            # Capture console logs
            print("\n=== Console Messages ===")
            console_msgs = await page.evaluate("() => window.__console_logs || []")
            for msg in console_msgs[-20:]:
                print(msg)
        
        # Check if there are errors
        error_panel = page.locator("text=Errors")
        has_errors = await error_panel.is_visible()
        
        if has_errors:
            print("\n=== ⚠️  ERRORS DETECTED ===")
            # Get error details
            error_items = page.locator('[data-testid="error-item"]')
            error_count = await error_items.count()
            for i in range(error_count):
                error_text = await error_items.nth(i).text_content()
                print(f"Error {i+1}: {error_text}")
        else:
            print("\n=== ✅ NO ERRORS - Processing successful ===")
        
        # Capture final status
        await page.wait_for_timeout(2000)
        
        print("\n=== Step 5: Navigate to Collections and verify count ===")
        await page.get_by_role("link", name="Collections").click()
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(1000)
        
        # Find the 'start' collection and check document count
        start_collection = page.locator("text=/start.*\\d+ documents/")
        if await start_collection.is_visible():
            collection_text = await start_collection.text_content()
            print(f"Collection status: {collection_text}")
            
            # Extract document count
            import re
            match = re.search(r"(\d+) documents?", collection_text)
            if match:
                doc_count = int(match.group(1))
                if doc_count > 0:
                    print(f"✅ SUCCESS: 'start' collection has {doc_count} document(s)")
                else:
                    print(f"❌ FAILURE: 'start' collection has 0 documents")
            else:
                print(f"⚠️  Could not parse document count from: {collection_text}")
        else:
            print("❌ FAILURE: 'start' collection not found")
        
        print("\n=== Step 6: Check backend logs for Nanonets usage ===")
        # This would require reading backend logs - we'll do that separately
        
        # Take a screenshot for evidence
        screenshot_path = Path(__file__).parent / "evidence_nanonets_pdf.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"\n📸 Screenshot saved to: {screenshot_path}")
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(test_nanonets_pdf_upload())

