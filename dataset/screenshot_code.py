import asyncio
import os
import sys
import base64

# Add parent directory to path to import utils module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import capture_screenshot
from datasets import load_dataset


# Utility function to encode an image to base64
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


async def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(script_dir, "input")
    # output_dir = os.path.abspath(os.path.join(script_dir, "..", "full_images"))
    output_dir = os.path.join(script_dir, "output")

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


# if __name__ == "__main__":
#     asyncio.run(main())


def download_ui_reasoning_dataset():

    # Load the dataset
    dataset = load_dataset("smirki/UI_Reasoning_Dataset")
    
    # Make sure input directory exists
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(script_dir, "input")
    
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
    
    # Loop through the dataset and save each answer as an HTML file
    for i, example in enumerate(dataset["train"]):
        answer = example.get("answer", "")
        if answer:
            output_path = os.path.join(input_dir, f"example_{i}.html")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(answer)
    
    print(f"Saved {i+1} HTML files to {input_dir}")


def rename_html_files():
    """Rename HTML files based on the first word of their title element and clean HTML content."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("BeautifulSoup not found. Installing...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "beautifulsoup4"])
        from bs4 import BeautifulSoup
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(script_dir, "input")
    
    if not os.path.exists(input_dir):
        print(f"Directory {input_dir} does not exist.")
        return
    
    files = os.listdir(input_dir)
    first_word_counts = {}  # Track how many times each first word has been used
    
    for file in files:
        if not file.endswith('.html'):
            continue
        
        file_path = os.path.join(input_dir, file)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Clean content that appears before <!DOCTYPE html>
            doctype_idx = content.find('<!DOCTYPE html>')
            if doctype_idx > 0:  # If there's content before DOCTYPE
                cleaned_content = content[doctype_idx:]
                content = cleaned_content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(cleaned_content)
                print(f"Removed content before <!DOCTYPE html> from {file}")
            
            # Clean HTML by removing content after </html> tag
            html_end_idx = content.rfind('</html>')
            if html_end_idx != -1:
                cleaned_content = content[:html_end_idx + 7]  # +7 to include '</html>'
                
                # Write cleaned content back to file if changed
                if cleaned_content != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(cleaned_content)
                    print(f"Cleaned extraneous content from {file}")
                content = cleaned_content
            
            # Parse HTML
            soup = BeautifulSoup(content, 'html.parser')
            title_tag = soup.find('title')
            
            if title_tag and title_tag.text:
                title = title_tag.text
                
                # Extract only first word from title
                first_word = title.split()[0]
                
                # Convert to filename base
                base_filename = first_word.lower()
                base_filename = ''.join(c for c in base_filename if c.isalnum())
                
                # Handle duplicate filenames
                if base_filename in first_word_counts:
                    first_word_counts[base_filename] += 1
                    new_filename = f"{base_filename}{first_word_counts[base_filename]}.html"
                else:
                    first_word_counts[base_filename] = 1
                    new_filename = f"{base_filename}.html"
                
                # Check if the new filename already exists (from previous runs)
                while os.path.exists(os.path.join(input_dir, new_filename)) and os.path.join(input_dir, new_filename) != file_path:
                    if base_filename in first_word_counts:
                        first_word_counts[base_filename] += 1
                    else:
                        first_word_counts[base_filename] = 2
                    new_filename = f"{base_filename}{first_word_counts[base_filename]}.html"
                
                new_file_path = os.path.join(input_dir, new_filename)
                
                # Rename file
                if file != new_filename:
                    os.rename(file_path, new_file_path)
                    print(f"Renamed: {file} → {new_filename}")
                else:
                    print(f"Skipped: {file} (already correct)")
            else:
                print(f"Error: No title found in {file}")
        
        except Exception as e:
            print(f"Error processing {file}: {e}")

if __name__ == "__main__":
    # download_ui_reasoning_dataset()
    # rename_html_files()  # Add this line to rename files after downloading
    asyncio.run(main())  # Uncomment to also run screenshot capture


