import base64
from openai import OpenAI
import ast
import os
import shutil
import random
from PIL import Image, ImageDraw

client = OpenAI(
    api_key=""
)


# Function to encode the image to base64
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


# Function to crop and save components based on coordinates
def crop_and_save_components(image_path, components, segments_dir):
    image = Image.open(image_path)
    width, height = image.size

    for idx, component in enumerate(components):
        # Extract component name and coordinates
        component_name = component["component_name"]
        x, y, w, h = component["coordinates"]

        # Validate and adjust coordinates
        x = max(0, x)
        y = max(0, y)
        w = max(0, w)
        h = max(0, h)

        if w == 0 or h == 0:
            print(f"Skipping {component_name} due to zero width or height.")
            continue

        if x + w > width:
            w = width - x
        if y + h > height:
            h = height - y

        # Crop the image
        cropped_image = image.crop((x, y, x + w, y + h))

        # Save the cropped image into the segments directory
        filename = f"{component_name}_{idx}.png"
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

    for component in components:
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

        # Generate a random vibrant color
        color = (
            random.randint(128, 255),  # Red
            random.randint(128, 255),  # Green
            random.randint(128, 255),  # Blue
        )

        # Draw a solid rectangle over the segment
        draw.rectangle([x, y, x + w, y + h], fill=color)

    # Save the image with segments marked
    draw_image.save(output_path)
    print(f"Saved segmented image with boxes: {output_path}")


def split_image(image_path):
    # Get the base name without extension
    base_name = os.path.splitext(os.path.basename(image_path))[0]

    # Create the output directory named after the input file
    output_dir = "img/" + base_name

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Move the input file into the output directory
    new_image_path = os.path.join(output_dir, os.path.basename(image_path))
    if not os.path.exists(new_image_path):
        shutil.move(image_path, new_image_path)
        print(f"Moved {image_path} to {new_image_path}")
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

    # Craft the prompt
    prompt = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Identify the UI components in the provided webpage image. "
                        "For each component (e.g., menubar, sub-navigation bar, main content area, footer), "
                        "provide the bounding box coordinates in pixels as integers in the format:\n"
                        '{"component_name": "menubar", "coordinates": [x, y, width, height]}.\n'
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

    # Proceed to crop and save components
    crop_and_save_components(image_path, components, segments_dir)

    # Create an image with solid boxes over segments
    segmented_image_path = os.path.join(segments_dir, "segments_overlay.png")
    create_segmented_image(image_path, components, segmented_image_path)

    print("Components extracted and segmented image saved.")


split_image("webflow-full.png")
