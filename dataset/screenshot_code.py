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
    browser = await launch()
    page = await browser.newPage()

    await page.setViewport({"width": 1280, "height": 1000})

    file_url = f"file:///{os.path.abspath(html_path)}"
    await page.goto(file_url, {"waitUntil": "networkidle0"})

    dimensions = await page.evaluate(
        """() => {
        return {
            height: document.documentElement.offsetHeight,
            width: document.documentElement.offsetWidth
        }
    }"""
    )

    await page.setViewport(
        {"width": dimensions["width"], "height": dimensions["height"]}
    )

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

    print(f"Screenshot saved to {output_image_path}")

    await browser.close()


async def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(script_dir, "input")
    output_dir = os.path.abspath(os.path.join(script_dir, "output"))

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
