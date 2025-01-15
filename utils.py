import base64
import os
from pyppeteer import launch


# Utility function to encode an image to base64
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


async def capture_screenshot(html_path, output_image_path, width=1920, height=1080):
    # Launch headless browser
    browser = await launch()
    page = await browser.newPage()

    await page.setViewport({"width": width, "height": height})

    # Convert HTML file path to file URL
    file_url = f"file:///{os.path.abspath(html_path)}"

    # Open the HTML file
    await page.goto(file_url, {"waitUntil": "networkidle0"})

    # Take a screenshot and save it
    await page.screenshot({"path": output_image_path, "fullPage": True})

    # Close the browser
    await browser.close()
