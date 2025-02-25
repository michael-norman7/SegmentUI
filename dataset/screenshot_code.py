import asyncio
import os

# from utils import capture_screenshot
import base64
import os
from pyppeteer import launch


# Utility function to encode an image to base64
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


async def capture_screenshot(html_path, output_image_path):
    # Launch headless browser
    browser = await launch()
    page = await browser.newPage()

    # Set viewport width to a standard desktop width
    await page.setViewport({"width": 1280, "height": 800})

    # Convert HTML file path to file URL
    file_url = f"file:///{os.path.abspath(html_path)}"

    # Open the HTML file
    await page.goto(file_url, {"waitUntil": "networkidle0"})

    # Get the actual height of the content
    dimensions = await page.evaluate(
        """() => {
        return {
            height: document.documentElement.offsetHeight,
            width: document.documentElement.offsetWidth
        }
    }"""
    )

    # Update viewport to match content dimensions
    await page.setViewport(
        {"width": dimensions["width"], "height": dimensions["height"]}
    )

    # Take a screenshot of only the visible content
    await page.screenshot(
        {
            "path": output_image_path,
            "fullPage": False,
            "clip": {
                "x": 0,
                "y": 0,
                "width": dimensions["width"],
                "height": dimensions["height"],
            },
        }
    )

    # Close the browser
    await browser.close()


async def main():
    input_dir = "./dataset/input"
    output_dir = "./dataset/output"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename in os.listdir(input_dir):
        if filename.endswith(".html"):
            html_path = os.path.join(input_dir, filename)
            output_image_path = os.path.join(
                output_dir, f"{os.path.splitext(filename)[0]}.png"
            )

            if not os.path.exists(output_image_path):
                await capture_screenshot(html_path, output_image_path)


if __name__ == "__main__":
    asyncio.run(main())
