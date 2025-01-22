import base64
from openai import OpenAI
import ast
import os
import shutil
import random
from PIL import Image, ImageDraw
from dotenv import load_dotenv
from matplotlib import pyplot as plt
import io
from utils import *

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

colors = [
    (255, 0, 0),  # Red
    (0, 255, 0),  # Lime
    (0, 0, 255),  # Blue
    (255, 255, 0),  # Yellow
    (255, 0, 255),  # Magenta
    (0, 255, 255),  # Cyan
    (255, 165, 0),  # Orange
    (128, 0, 128),  # Purple
    (255, 192, 203),  # Pink
    (255, 105, 180),  # Hot Pink
    (173, 255, 47),  # Green Yellow
    (0, 128, 128),  # Teal
    (0, 0, 128),  # Navy
    (128, 128, 0),  # Olive
    (255, 69, 0),  # Orange Red
    (154, 205, 50),  # Yellow Green
    (138, 43, 226),  # Blue Violet
]
random.shuffle(colors)
colors_normalized = [(r / 255, g / 255, b / 255) for r, g, b in colors]

# Keep track of used colors to avoid duplication
used_colors = []


# Function to crop and save components based on coordinates
def crop_and_save_components(image_path, components, segments_dir):
    image = Image.open(image_path)
    width, height = image.size

    for idx, component in enumerate(components):
        # Extract component name and coordinates
        component_name = component["component_name"]
        x, y, w, h = component["coordinates"]

        # Add a 50px buffer around the cropped image
        buffer = 10
        x = max(0, x - buffer)
        y = max(0, y - buffer)
        w = min(width - x, w + 2 * buffer)
        h = min(height - y, h + 2 * buffer)

        if w == 0 or h == 0:
            print(f"Skipping {component_name} due to zero width or height.")
            continue

        # Crop the image
        cropped_image = image.crop((x, y, x + w, y + h))

        # Save the cropped image into the segments directory
        filename = f"{idx}_{component_name}.png"
        filepath = os.path.join(segments_dir, filename)
        cropped_image.save(filepath)
        print(f"Saved {filepath}")


# Function to create an image with solid boxes over segments
def create_segmented_image(image_path, components, output_path):
    # Open the image
    image = Image.open(image_path).convert("RGB")
    width, height = image.size

    # Create a copy of the image to draw on
    draw_image = image.copy()
    draw = ImageDraw.Draw(draw_image)

    for idx, component in enumerate(components):
        x, y, w, h = component["coordinates"]

        # Validate and adjust coordinates
        x = max(0, x)
        y = max(0, y)
        w = max(0, w)
        h = max(0, h)

        if w == 0 or h == 0:
            continue

        if x + w > width:
            w = width - x
        if y + h > height:
            h = height - y

        # Assign a color from the list without duplication
        if idx < len(colors_normalized):
            color = colors_normalized[idx]
        else:
            # If we run out of colors, reuse colors starting from the beginning
            color = colors_normalized[idx % len(colors_normalized)]

        # Draw a solid rectangle over the segment
        draw.rectangle([x, y, x + w, y + h], fill=tuple(int(c * 255) for c in color))

    # Save the image with segments marked
    draw_image.save(output_path)
    print(f"Saved segmented image with boxes: {output_path}")


# Function to create an image with transparent bounding boxes
def create_bounding_boxes_image(image_path, components, output_path):
    # Open the image
    image = Image.open(image_path).convert("RGBA")
    width, height = image.size

    # Create a transparent overlay
    overlay = Image.new("RGBA", image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    # Define a list of vibrant and easily distinguishable colors
    colors = [
        (255, 0, 0),  # Red
        (0, 255, 0),  # Lime
        (0, 0, 255),  # Blue
        (255, 255, 0),  # Yellow
        (255, 0, 255),  # Magenta
        (0, 255, 255),  # Cyan
        (255, 165, 0),  # Orange
        (128, 0, 128),  # Purple
        (255, 192, 203),  # Pink
        (255, 105, 180),  # Hot Pink
        (173, 255, 47),  # Green Yellow
        (0, 128, 128),  # Teal
        (0, 0, 128),  # Navy
        (128, 128, 0),  # Olive
        (255, 69, 0),  # Orange Red
        (154, 205, 50),  # Yellow Green
        (138, 43, 226),  # Blue Violet
    ]

    # Shuffle the colors to randomize assignment
    random.shuffle(colors)

    for idx, component in enumerate(components):
        x, y, w, h = component["coordinates"]

        # Validate and adjust coordinates
        x = max(0, x)
        y = max(0, y)
        w = min(w, width - x)
        h = min(h, height - y)

        if w == 0 or h == 0:
            continue

        # Assign a color from the list without duplication
        if idx < len(colors):
            color = colors[idx]
        else:
            # If we run out of colors, reuse colors starting from the beginning
            color = colors[idx % len(colors)]

        # Draw a rectangle outline with transparent fill
        draw.rectangle([x, y, x + w, y + h], outline=color + (255,), width=5)

    # Combine the original image with the overlay
    combined = Image.alpha_composite(image, overlay)
    combined.save(output_path)
    print(f"Saved image with bounding boxes: {output_path}")


# Function to encode PIL image to base64
def encode_pil_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def split_image(image_path, critique=False):
    if not os.path.exists(image_path):
        print(f"Image file '{image_path}' not found.")
        return

    # Get the base name without extension
    base_name = os.path.splitext(os.path.basename(image_path))[0]

    # Create the output directory named after the input file
    output_dir = "img/" + base_name

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
        print(f"Deleted existing directory: {output_dir}")

    os.makedirs(output_dir)

    # Move the input file into the output directory
    new_image_path = os.path.join(output_dir, os.path.basename(image_path))
    if not os.path.exists(new_image_path):
        shutil.copy2(image_path, new_image_path)
        print(f"Copied {image_path} to {new_image_path}")
        image_path = new_image_path  # Update image_path to new location
    else:
        print(f"{new_image_path} already exists.")
        image_path = new_image_path  # Ensure image_path is updated even if file exists

    # Create the 'segments' directory inside the output directory
    segments_dir = os.path.join(output_dir, "segments")
    if not os.path.exists(segments_dir):
        os.makedirs(segments_dir)

    # Encode the image (now from the new location)
    base64_image = encode_image(image_path)

    image = Image.open(image_path).convert("RGB")
    width, height = image.size

    # Initial attempt flag
    attempt = 1

    while True:
        print(f"\nAttempt {attempt} to generate bounding boxes.")

        # Encode the image (now from the new location)
        base64_image = encode_image(image_path)

        # Craft the prompt for initial bounding box generation
        prompt = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Identify the major UI components in the provided webpage image. "
                            "Do not include any text or logos in the components. "
                            f"The image has the dimensions {width}x{height} pixels.\n"
                            "For each component (e.g., menubar, sub-navigation bar, main content area, footer), "
                            "provide the bounding box coordinates in pixels as integers in the format:\n"
                            '{"component_name": "menubar", "coordinates": [x, y, width, height]}.\n'
                            "There does not need to be each type of component if the website is very simple. "
                            "There may only be a main content component. "
                            "Return the results as a JSON array."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                    },
                ],
            }
        ]

        # Send the request to GPT-4O
        response = client.chat.completions.create(
            model="gpt-4o", messages=prompt, max_tokens=500, temperature=0
        )

        # Extract the assistant's reply
        assistant_reply = response.choices[0].message.content

        # Parse the JSON output
        try:
            # Remove code block markers if present
            if assistant_reply.startswith("```json"):
                assistant_reply = assistant_reply.strip("```json").strip()
            elif assistant_reply.startswith("```"):
                assistant_reply = assistant_reply.strip("```").strip()

            # Safely evaluate the response as a Python literal
            components = ast.literal_eval(assistant_reply)
        except Exception as e:
            print("Failed to parse the model's response.")
            print(f"Error: {e}")
            print("Response was:")
            print(assistant_reply)
            exit(1)

        # Create an image with bounding boxes
        bounding_boxes_image_path = os.path.join(
            output_dir, base_name + "_bounding_boxes.png"
        )
        create_bounding_boxes_image(image_path, components, bounding_boxes_image_path)

        if not critique:
            break

        # Encode the image with bounding boxes to base64
        base64_bounding_boxes_image = encode_image(bounding_boxes_image_path)

        # display_image_with_bounding_boxes(image_path, components)
        # Display the image with bounding boxes
        plt.figure(figsize=(15, 10))  # Increase the figure size
        plt.imshow(Image.open(bounding_boxes_image_path))
        plt.axis("off")
        plt.show()

        # Ask GPT to critique the bounding boxes
        critique_prompt = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Please review the bounding boxes overlaid on the webpage image. "
                            "Do the bounding boxes accurately enclose the major UI components? "
                            "If not, please explain what needs to be corrected. If they are correct, simply respond 'The bounding boxes are correct.'"
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_bounding_boxes_image}"
                        },
                    },
                ],
            }
        ]

        # Send the critique request to GPT-4O
        critique_response = client.chat.completions.create(
            model="gpt-4o", messages=critique_prompt, max_tokens=200, temperature=0
        )

        critique_reply = critique_response.choices[0].message.content.strip()

        print(f"GPT Critique: {critique_reply}")

        if "bounding boxes are correct" in critique_reply.lower():
            print("Bounding boxes confirmed correct by GPT.")
            break
        else:
            print("GPT found issues with the bounding boxes. Regenerating...")
            attempt += 1
            if attempt > 3:
                print(
                    "Maximum attempts reached. Proceeding with current bounding boxes."
                )
                break

    # Proceed to crop and save components
    crop_and_save_components(image_path, components, segments_dir)

    # Create an image with solid boxes over segments
    segmented_image_path = os.path.join(output_dir, base_name + "_segments_overlay.png")
    create_segmented_image(image_path, components, segmented_image_path)

    print("Components extracted and segmented image saved.")


# List image files in the current directory
image_extensions = (".png", ".jpg", ".jpeg", ".bmp", ".gif")
files_in_directory = os.listdir("./full_images")
image_files = [f for f in files_in_directory if f.lower().endswith(image_extensions)]

if not image_files:
    print("No image files found in the current directory.")
    exit(1)

print("Image files found:")
for idx, filename in enumerate(image_files):
    print(f"{idx}: {filename}")

# Prompt the user to select an image file
while True:
    try:
        selection = int(input("Enter the number of the image you want to process: "))
        if 0 <= selection < len(image_files):
            image_path = "full_images/" + image_files[selection]
            break
        else:
            print("Invalid selection. Please enter a number from the list.")
    except ValueError:
        print("Invalid input. Please enter a number.")


split_image(image_path, critique=True)
