import asyncio
import os
from utils import capture_screenshot


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
