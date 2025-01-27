import os
import base64
import shutil
from openai import OpenAI
from dotenv import load_dotenv
import asyncio
from pyppeteer import launch
from utils import *
import sys

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_full_image_code(original_image_path, output_dir):
    full_image = encode_image(original_image_path)
    prompt = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        """This is an image of a website. Generate the code needed to create this website. 
                        If you can't create the exact code, please create a 
                        similar code that would generate a similar website based on the image. 
                        Do not return any text except the code itself in a single HTML file. 
                        Begin directly with <!DOCTYPE html>."""
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{full_image}"},
                },
            ],
        }
    ]

    response = client.chat.completions.create(model="gpt-4o", messages=prompt)
    full_image_code = response.choices[0].message.content.strip()
    # print(full_image_code[:500])

    start_index = full_image_code.find("```html")
    end_index = full_image_code.find("```", start_index + 6)
    if start_index != -1 and end_index != -1:
        full_image_code = full_image_code[start_index + 7 : end_index].strip()

    full_image_code_path = os.path.join(output_dir, "full_image_gen.html")
    with open(full_image_code_path, "w") as file:
        file.write(full_image_code)
    print(f"Full image code saved to {full_image_code_path}")

    full_image_gen_image_path = os.path.join(output_dir, "full_image_gen.png")
    try:
        asyncio.run(capture_screenshot(full_image_code_path, full_image_gen_image_path))
        print(
            f"Screenshot of the full image gen code saved to {full_image_gen_image_path}"
        )
    except Exception as e:
        print(f"Error while capturing screenshot: {e}")

    return full_image_code


def generate_segment_code(
    masked_image_path, original_image_path, segments_dir, output_dir
):
    masked_image = encode_image(masked_image_path)
    original_image = encode_image(original_image_path)
    component_files = [
        f for f in sorted(os.listdir(segments_dir)) if f.endswith(".png")
    ]

    messages = []

    # Step 1: generate base structure
    prompt = {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": (
                    """You are an expert web developer tasked with creating a website based on the provided wireframe.
                    Your task is to recreate a website with the highest level of detail to the best of your ability.
                    Recreate the style, layout, and structure of the website as accurately as possible.
                    
                    This is a blank wireframe for a website. There are multiple blocks with different colors 
                    to designate different components of the website. Generate the HTML and CSS code for the basic 
                    structure of the site, setting up a layout that allows individual components to be created 
                    and inserted into it later. Do not return any text except the code itself in a single HTML file."""
                ),
            },
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{masked_image}"},
            },
        ],
    }
    messages.append(prompt)

    response = client.chat.completions.create(model="gpt-4o", messages=messages)
    code = response.choices[0].message.content.strip()
    if code.startswith("```html") and code.endswith("```"):
        code = code[7:-3].strip()

    messages.append(
        {
            "role": "assistant",
            "content": [{"type": "text", "text": code}],
        }
    )

    # Step 2: Prompt the user for each component to generate
    components_code = []
    for idx, filename in enumerate(component_files):
        component_name = filename.split("_", 1)[-1].replace(".png", "")
        component_image_path = os.path.join(segments_dir, filename)

        print(
            f"Generating code for component {idx + 1}/{len(component_files)}: {component_name}"
        )
        component_image = encode_image(component_image_path)
        prompt = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"""This is a picture of the {component_name} for the website. Generate the HTML and CSS code needed to 
                            create this component, using the structured code you previously created in the base HTML file. 
                            Do not return any text except the code itself in a single HTML file."""
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{component_image}"},
                },
            ],
        }
        messages.append(prompt)

        response = client.chat.completions.create(model="gpt-4o", messages=messages)
        component_code = response.choices[0].message.content.strip()
        if component_code.startswith("```html") and component_code.endswith("```"):
            component_code = component_code[7:-3].strip()

        components_code.append(component_code)

        messages.append(
            {
                "role": "assistant",
                "content": [{"type": "text", "text": component_code}],
            }
        )

    # Step 3: Combine the base structure and component code
    print("Combining base structure and components code...")
    prompt = {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": (
                    f"""Combine the base structure of the website and the HTML/CSS code for its components.
                    Do not return any text except the combined HTML code itself."""
                ),
            },
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{component_image}"},
            },
        ],
    }
    messages.append(prompt)

    response = client.chat.completions.create(model="gpt-4o", messages=messages)
    full_code = response.choices[0].message.content.strip()
    if full_code.startswith("```html") and full_code.endswith("```"):
        full_code = full_code[7:-3].strip()

    messages.append(
        {
            "role": "assistant",
            "content": [{"type": "text", "text": full_code}],
        }
    )

    full_code_path = os.path.join(output_dir, "segment_gen.html")
    with open(full_code_path, "w") as file:
        file.write(full_code)

    segment_gen_image_path = os.path.join(output_dir, "segment_gen.png")
    try:
        asyncio.run(capture_screenshot(full_code_path, segment_gen_image_path))
        print(f"Screenshot of the segment gen code saved to {segment_gen_image_path}")
    except Exception as e:
        print(f"Error while capturing screenshot: {e}")

    # Step 4: Final verification and save using the original full image
    prompt = {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": (
                    """Here is an image of the final desired website and an image of what the code currently generates. 
                        Please verify that the code accurately represents the original image and is correctly structured with a very high level of accuracy. 
                        If there are any issues, make the necessary adjustments to the code.
                        
                        Do not return any text except the HTML code.
                        
                        Full website image:
                        """
                ),
            },
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{original_image}"},
            },
            {
                "type": "text",
                "text": "\nPreview of the code generated so far:",
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{encode_image(segment_gen_image_path)}"
                },
            },
        ],
    }
    messages.append(prompt)

    print("Verifying and finalizing code...")
    response = client.chat.completions.create(model="gpt-4o", messages=messages)
    final_segment_gen_code = response.choices[0].message.content.strip()
    if final_segment_gen_code.startswith("```html") and final_segment_gen_code.endswith(
        "```"
    ):
        final_segment_gen_code = final_segment_gen_code[7:-3].strip()

    final_segment_gen_code_path = os.path.join(output_dir, "final_segment_gen.html")
    with open(final_segment_gen_code_path, "w") as file:
        file.write(final_segment_gen_code)

    final_segment_gen_image_path = os.path.join(output_dir, "final_segment_gen.png")
    try:
        asyncio.run(
            capture_screenshot(
                final_segment_gen_code_path, final_segment_gen_image_path
            )
        )
        print(
            f"Screenshot of the final segment gen code saved to {final_segment_gen_image_path}"
        )
    except Exception as e:
        print(f"Error while capturing screenshot: {e}")

    return final_segment_gen_code


def process_project(project_name, tests):
    img_dir = "img"
    base_dir = os.path.join(img_dir, project_name)
    original_image_path = os.path.join(base_dir, f"{project_name}.png")
    masked_image_path = os.path.join(base_dir, f"{project_name}_segments_overlay.png")
    segments_dir = os.path.join(base_dir, "segments")
    output_dir = os.path.join("output", project_name)

    os.makedirs(output_dir, exist_ok=True)
    shutil.copy(original_image_path, output_dir)

    # Test Full Image Gen
    if "full_image" in tests:
        print("Generating code from full image...")

        generate_full_image_code(original_image_path, output_dir)

    # Test Segment Gen
    if "segment_gen" in tests:
        print("Generating code from image segments...")

        generate_segment_code(
            masked_image_path, original_image_path, segments_dir, output_dir
        )


# Main function to run the code generation
def main():
    tests = ["full_image", "segment_gen"]
    # tests = ["segment_gen"]

    # List image project directories in the "img" folder
    img_dir = "img"
    image_projects = [
        d for d in os.listdir(img_dir) if os.path.isdir(os.path.join(img_dir, d))
    ]

    if not image_projects:
        print("No image projects found in the 'img' directory.")
        return

    if len(sys.argv) > 1:
        project_name = sys.argv[1]
        if project_name in image_projects:
            print(f"Processing project: {project_name}")
            process_project(project_name, tests)
    else:
        print("Image projects found:")
        for idx, project in enumerate(image_projects):
            print(f"{idx}: {project}")

        # Prompt user to select an image project
        while True:
            try:
                selection = input(
                    "Enter the number of the image project you want to process or 'all': "
                )
                if selection == "all":
                    for project_name in image_projects:
                        print(f"Processing project: {project_name}")
                        process_project(project_name, tests)
                    break
                elif 0 <= int(selection) < len(image_projects):
                    process_project(image_projects[int(selection)], tests)
                    break
                else:
                    print("Invalid selection. Please enter a number from the list.")
            except ValueError:
                print("Invalid input. Please enter a number.")


if __name__ == "__main__":
    main()
