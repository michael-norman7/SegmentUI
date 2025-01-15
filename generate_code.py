import os
import base64
import shutil
from openai import OpenAI
from dotenv import load_dotenv
import asyncio
from pyppeteer import launch
from utils import *

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_full_image_code(original_image_path):
    full_image = encode_image(original_image_path)
    prompt = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        """This is an image of a website. Generate the code needed to create this website to be displayed on a 1920x1080p display. 
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

    return full_image_code


def generate_base_structure(masked_image_path, num_components):
    base64_image = encode_image(masked_image_path)
    prompt = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        """This is a blank wireframe for a website. There are multiple blocks with different colors 
                        to designate different components of the website. Generate the HTML and CSS code for the basic 
                        structure of the site, setting up a layout that allows individual components to be created 
                        and inserted into it later. Do not return any text except the code itself in a single HTML file.
                        This website should be formatted for a 1920x1080p display."""
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                },
            ],
        }
    ]

    response = client.chat.completions.create(model="gpt-4o", messages=prompt)
    base_structure_code = response.choices[0].message.content.strip()
    if base_structure_code.startswith("```html") and base_structure_code.endswith(
        "```"
    ):
        base_structure_code = base_structure_code[7:-3].strip()

    return base_structure_code


# Function to generate HTML and CSS code for each individual component
def generate_component_code(component_image_path, component_name):
    component_image = encode_image(component_image_path)
    prompt = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"""This is a picture of the {component_name} for the website. Generate the HTML and CSS code needed to 
                        create this component, using the structured code you previously created in the base HTML file. 
                        This website should be formatted for a 1920x1080p display.
                        Do not return any text except the code itself in a single HTML file."""
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{component_image}"},
                },
            ],
        }
    ]

    response = client.chat.completions.create(model="gpt-4o", messages=prompt)
    component_code = response.choices[0].message.content.strip()
    if component_code.startswith("```html") and component_code.endswith("```"):
        component_code = component_code[7:-3].strip()

    return component_code


def combine_components(base_structure_code, components_code):
    prompt = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        """Here is the base structure of a website and the HTML/CSS code for its components. 
                        Please combine them into a single HTML file, ensuring that each component is placed correctly 
                        within the base structure. 
                        This website should be formatted for a 1920x1080p display.
                        Do not return any text except the combined HTML code itself."""
                    ),
                },
                {
                    "type": "text",
                    "text": base_structure_code,
                },
            ],
        }
    ]

    for idx, component_code in enumerate(components_code):
        prompt[0]["content"].append(
            {
                "type": "text",
                "text": f"Component {idx + 1}:\n{component_code}",
            }
        )

    response = client.chat.completions.create(model="gpt-4o", messages=prompt)
    combined_code = response.choices[0].message.content.strip()
    if combined_code.startswith("```html") and combined_code.endswith("```"):
        combined_code = combined_code[7:-3].strip()

    return combined_code


def verify_and_finalize_code(full_image, preview_image, segment_gen_code):
    prompt = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        """Here is an image of the desired website, the generated code so far, and an image of what the code currently generates. 
                        Please verify that the final code accurately represents the original image and is correctly structured. 
                        If there are any issues, make the necessary adjustments to the code. 
                        If you can't create the exact code, create a similar code that would generate a similar website based on the image. 
                        
                        Return only the code in a single HTML file, starting with <!DOCTYPE html>.
                        """
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{encode_image(full_image)}"
                    },
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{encode_image(preview_image)}"
                    },
                },
                {
                    "type": "text",
                    "text": segment_gen_code,
                },
            ],
        }
    ]

    response = client.chat.completions.create(model="gpt-4o", messages=prompt)
    final_segment_gen_code = response.choices[0].message.content.strip()

    start_index = final_segment_gen_code.find("```html")
    end_index = final_segment_gen_code.find("```", start_index + 6)
    if start_index != -1 and end_index != -1:
        final_segment_gen_code = final_segment_gen_code[
            start_index + 7 : end_index
        ].strip()

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

    # Get component files and count them
    component_files = [
        f for f in sorted(os.listdir(segments_dir)) if f.endswith(".png")
    ]
    num_components = len(component_files)

    # Test Full Image Gen
    if "full_image" in tests:
        full_image_code = generate_full_image_code(original_image_path)
        full_image_code_path = os.path.join(output_dir, "full_image_gen.html")
        with open(full_image_code_path, "w") as file:
            file.write(full_image_code)
        print(f"Full image code saved to {full_image_code_path}")

        full_image_gen_image_path = os.path.join(output_dir, "full_image_gen.png")
        try:
            asyncio.run(
                capture_screenshot(full_image_code_path, full_image_gen_image_path)
            )
            print(
                f"Screenshot of the full image gen code saved to {full_image_gen_image_path}"
            )
        except Exception as e:
            print(f"Error while capturing screenshot: {e}")

    # Test Segment Gen
    if "segment_gen" in tests:
        # Generate base structure with the appropriate number of placeholders
        base_structure_code = generate_base_structure(masked_image_path, num_components)

        # Step 2: Prompt the user for each component to generate
        component_files = [
            f for f in sorted(os.listdir(segments_dir)) if f.endswith(".png")
        ]
        components_code = []
        for idx, filename in enumerate(component_files):
            component_name = filename.split("_", 1)[-1].replace(".png", "")
            component_image_path = os.path.join(segments_dir, filename)

            print(
                f"Generating code for component {idx + 1}/{len(component_files)}: {component_name}"
            )
            component_code = generate_component_code(
                component_image_path, component_name
            )
            components_code.append(component_code)

        # Step 3: Combine the base structure and component code
        combined_code = combine_components(base_structure_code, components_code)

        combined_code_path = os.path.join(output_dir, "segment_gen.html")
        with open(combined_code_path, "w") as file:
            file.write(combined_code)
        print(f"Segment gen code saved to {combined_code_path}")

        # Step 4: Capture screenshot of the generated code
        segment_gen_image_path = os.path.join(output_dir, "preview_segment_gen.png")
        try:
            asyncio.run(capture_screenshot(combined_code_path, segment_gen_image_path))
            print(
                f"Screenshot of the segment gen code saved to {segment_gen_image_path}"
            )
        except Exception as e:
            print(f"Error while capturing screenshot: {e}")

        # Step 5: Final verification and save using the original full image
        final_segment_gen_code = verify_and_finalize_code(
            original_image_path, segment_gen_image_path, combined_code
        )
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

        print(
            f"Website code generation complete. Final HTML located at: {final_segment_gen_code_path}"
        )


# Main function to run the code generation
def main():
    tests = ["full_image", "segment_gen"]

    # List image project directories in the "img" folder
    img_dir = "img"
    image_projects = [
        d for d in os.listdir(img_dir) if os.path.isdir(os.path.join(img_dir, d))
    ]

    if not image_projects:
        print("No image projects found in the 'img' directory.")
        return

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
