# code_generation.py

import os
import base64
import shutil
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# Utility function to encode an image to base64
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def generate_full_image_code(original_image_path):
    base64_image = encode_image(original_image_path)
    prompt = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        """This is an image of a website design. Generate the code needed to recreate 
                        this entire design, including all components and layout elements. Do not return any text except 
                        the code itself in a single HTML file. Begin directly with <!DOCTYPE html>. You MUST 
                        generate this code in this manner."""
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                },
            ],
        }
    ]

    response = client.chat.completions.create(
        model="gpt-4o", messages=prompt, max_tokens=1000
    )
    full_image_code = response.choices[0].message.content.strip()
    start_index = full_image_code.find("```html")
    end_index = full_image_code.find("```", start_index + 6)
    if start_index != -1 and end_index != -1:
        full_image_code = full_image_code[start_index + 6:end_index].strip()

    return full_image_code


def generate_base_structure(masked_image_path, output_dir, num_components):
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
                        and inserted into it later. Do not return any text except the code itself in a single HTML file."""
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                },
            ],
        }
    ]

    response = client.chat.completions.create(
        model="gpt-4o", messages=prompt, max_tokens=1000
    )
    base_structure_code = response.choices[0].message.content.strip()
    if base_structure_code.startswith("```html") and base_structure_code.endswith(
        "```"
    ):
        base_structure_code = base_structure_code[7:-3].strip()

    return base_structure_code


# Function to generate HTML and CSS code for each individual component
def generate_component_code(component_image_path, component_name, output_dir):
    base64_image = encode_image(component_image_path)
    prompt = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"This is a picture of the {component_name} for the website. Generate the HTML and CSS code needed to "
                        f"create this component, using the structured code you previously created in the base HTML file."
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                },
            ],
        }
    ]

    response = client.chat.completions.create(
        model="gpt-4o", messages=prompt, max_tokens=1000
    )
    component_code = response.choices[0].message.content.strip()

    # Save component HTML/CSS as a separate file
    component_path = os.path.join(output_dir, f"{component_name}.html")
    with open(component_path, "w") as file:
        file.write(component_code)
    print(f"{component_name} code saved to {component_path}")
    return component_code


def verify_and_finalize_code(
    full_image_path, base_html_path, components_code, output_dir
):
    base64_image = encode_image(full_image_path)

    # Load the base structure HTML
    with open(base_html_path, "r") as base_file:
        final_code = base_file.read()

    # Replace each placeholder div with its corresponding component code
    for idx, component_code in enumerate(components_code):
        placeholder = f'<div id="component_{idx}"></div>'
        component_injection = f'<div id="component_{idx}">\n{component_code}\n</div>'
        final_code = final_code.replace(placeholder, component_injection)

    # Verify with GPT if the final layout is correct (optional step)
    prompt = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "This is a picture of the entire website. Please review the HTML/CSS code you have generated, "
                        "including the base structure and each component, and ensure that the final output code accurately "
                        "recreates this image. Make any adjustments needed for correct alignment, spacing, and styling "
                        "to match the provided image."
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                },
            ],
        }
    ]

    # Save the final HTML with all component code inserted
    final_html_path = os.path.join(output_dir, "final_website.html")
    with open(final_html_path, "w") as file:
        file.write(final_code)
    print(f"Final verified HTML saved to {final_html_path}")
    return final_html_path


# Main function to run the code generation
def main():
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
            selection = int(
                input("Enter the number of the image project you want to process: ")
            )
            if 0 <= selection < len(image_projects):
                project_name = image_projects[selection]
                break
            else:
                print("Invalid selection. Please enter a number from the list.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    # Define paths based on selected project
    base_dir = os.path.join(img_dir, project_name)
    original_image_path = os.path.join(base_dir, f"{project_name}.png")
    masked_image_path = os.path.join(base_dir, f"{project_name}_segments_overlay.png")
    segments_dir = os.path.join(base_dir, "segments")
    output_dir = os.path.join("output", project_name)

    os.makedirs(output_dir, exist_ok=True)

    # Get component files and count them
    component_files = [
        f for f in sorted(os.listdir(segments_dir)) if f.endswith(".png")
    ]
    num_components = len(component_files)

    # Test Full Image Gen
    full_image_code = generate_full_image_code(original_image_path)

    # Save the full image HTML/CSS as a separate file
    full_image_code_path = os.path.join(output_dir, "full_image_gen.html")
    with open(full_image_code_path, "w") as file:
        file.write(full_image_code)
    print(f"Full image code saved to {full_image_code_path}")

    # Generate base structure with the appropriate number of placeholders
    base_structure_code = generate_base_structure(
        masked_image_path, output_dir, num_components
    )
    base_structure_code_path = os.path.join(output_dir, "base_structure.html")
    with open(base_structure_code_path, "w") as file:
        file.write(base_structure_code)
    print(f"Base structure code saved to {base_structure_code_path}")

    # # Step 2: Prompt the user for each component to generate
    # component_files = [
    #     f for f in sorted(os.listdir(segments_dir)) if f.endswith(".png")
    # ]
    # components_code = []
    # for idx, filename in enumerate(component_files):
    #     component_name = filename.split("_", 1)[-1].replace(".png", "")
    #     component_image_path = os.path.join(segments_dir, filename)

    #     print(
    #         f"Generating code for component {idx + 1}/{len(component_files)}: {component_name}"
    #     )
    #     component_code = generate_component_code(
    #         component_image_path, component_name, output_dir
    #     )
    #     components_code.append(component_code)

    # # Step 3: Final verification and save using the original full image
    # final_html_path = verify_and_finalize_code(
    #     original_image_path, base_html_path, components_code, output_dir
    # )
    # print(f"Website code generation complete. Final HTML located at: {final_html_path}")


if __name__ == "__main__":
    main()
