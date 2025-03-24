import base64
import os
from pyppeteer import launch


# Utility function to encode an image to base64
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


async def capture_screenshot(html_path, output_image_path):
    try:
        browser = await launch()
        page = await browser.newPage()

        await page.setViewport({"width": 1280, "height": 800})

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
        return True
    
    except Exception as e:
        print(f"Error capturing screenshot for {html_path}: {str(e)}")
        try:
            if 'browser' in locals() and browser:
                await browser.close()
        except:
            pass
        return False
