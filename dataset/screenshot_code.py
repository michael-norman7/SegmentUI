import asyncio
import os
import sys
import base64

# Add parent directory to path to import utils module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import capture_screenshot


# Utility function to encode an image to base64
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


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
