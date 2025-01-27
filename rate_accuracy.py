from openai import OpenAI
import os
import base64
from dotenv import load_dotenv
import pandas as pd
import glob

# import sys
# import argparse

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def get_accuracy_score(original_image_path, generated_image_path):
    original_image = encode_image(original_image_path)
    generated_image = encode_image(generated_image_path)

    # prompt = f"""
    # I have two images of websites. One is the original website, and the other is the generated website.
    # I dont have access to the original images or fonts so I can't compare them directly.
    # Please provide an accuracy score between 0 and 100 on how close the generated website is to the original website.
    # Only return the number.
    # """
    prompt = f"""
    I have two images of websites. One is the original website, and the other is the generated website. 
    I dont have access to the original images or fonts so I can't compare them directly.
    Rate the similarity between the original and generated website on 3 criteria:
    1. Visual structural resemblance
    2. Content accuracy
    3. Expected functionality
    4. Overall
    
    Please provide an accuracy score between 0 and 100 for each category on how close the generated website is to the original website.
    Only return the 3 numbers in the format: Visual: 90, Content: 80, Functionality: 70, Overall: 80
    """

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    },
                    {
                        "type": "text",
                        "text": ("""Original Image: """),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{original_image}"},
                    },
                    {
                        "type": "text",
                        "text": ("""Generated Image: """),
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{generated_image}"
                        },
                    },
                ],
            }
        ],
        model="gpt-4o",
    )

    accuracy_score = chat_completion.choices[0].message.content
    return accuracy_score


def update_excel_with_scores(folder_path, excel_path, tests):
    # Load existing Excel file if it exists
    if os.path.exists(excel_path):
        existing_dfs = {}
        for sheet_name in [
            "Overall Scores",
            "Visual Scores",
            "Content Scores",
            "Functional Scores",
        ]:
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
            if "Image Name" not in df.columns:
                df["Image Name"] = ""
            existing_dfs[sheet_name] = df
    else:
        existing_dfs = {
            sheet_name: pd.DataFrame()
            for sheet_name in [
                "Overall Scores",
                "Visual Scores",
                "Content Scores",
                "Functional Scores",
            ]
        }
        for df in existing_dfs.values():
            df["Image Name"] = ""

    # Get all image names in the folder
    image_paths = glob.glob(f"{folder_path}/*.png")
    image_names = [os.path.basename(path).replace(".png", "") for path in image_paths]

    # Filter out image names that are already in the Excel file
    existing_image_names = set(existing_dfs["Overall Scores"]["Image Name"].tolist())
    image_names = [name for name in image_names if name not in existing_image_names]

    # Initialize data structures for each sheet
    overall_scores = []
    visual_scores = []
    content_scores = []
    functional_scores = []

    for image_name in image_names:
        # Initialize dictionaries to hold scores for each test
        overall_score_row = {"Image Name": image_name}
        visual_score_row = {"Image Name": image_name}
        content_score_row = {"Image Name": image_name}
        functional_score_row = {"Image Name": image_name}

        original_image_path = f"output/{image_name}/{image_name}.png"

        for test in tests:
            print(f"Getting scores for {image_name} on test {test}...")
            if test == "Full Image Gen":
                generated_image_path = f"output/{image_name}/full_image_gen.png"
            elif test == "Segment Gen":
                generated_image_path = f"output/{image_name}/final_segment_gen.png"
            else:
                continue

            cnt = 0
            while True:
                try:
                    accuracy_score = get_accuracy_score(
                        original_image_path, generated_image_path
                    )
                    scores = accuracy_score.split(", ")
                    visual_score = int(scores[0].split(": ")[1])
                    content_score = int(scores[1].split(": ")[1])
                    functional_score = int(scores[2].split(": ")[1])
                    overall_score = int(scores[3].split(": ")[1])

                    overall_score_row[test] = overall_score
                    visual_score_row[test] = visual_score
                    content_score_row[test] = content_score
                    functional_score_row[test] = functional_score
                    break
                except Exception as e:
                    print(f"Error: {e}")
                    print(f"Retrying {image_name} for test {test}...")
                    cnt += 1
                    if cnt == 3:
                        print(f"Failed to get scores for {image_name} on test {test}")
                        overall_score_row[test] = None
                        visual_score_row[test] = None
                        content_score_row[test] = None
                        functional_score_row[test] = None
                        break

        # Append score dictionaries to respective lists
        overall_scores.append(overall_score_row)
        print(overall_score_row)
        visual_scores.append(visual_score_row)
        content_scores.append(content_score_row)
        functional_scores.append(functional_score_row)

    # Create dataframes for each sheet
    overall_df = pd.DataFrame(overall_scores)
    visual_df = pd.DataFrame(visual_scores)
    content_df = pd.DataFrame(content_scores)
    functional_df = pd.DataFrame(functional_scores)

    # Write dataframes to Excel file
    with pd.ExcelWriter(excel_path) as writer:
        overall_df.to_excel(writer, sheet_name="Overall Scores", index=False)
        visual_df.to_excel(writer, sheet_name="Visual Scores", index=False)
        content_df.to_excel(writer, sheet_name="Content Scores", index=False)
        functional_df.to_excel(writer, sheet_name="Functional Scores", index=False)


# def add_single_image_scores_to_excel(
#     image_name, original_image_path, excel_path, tests
# ):
#     try:
#         new_rows = {
#             "Overall Scores": {"": image_name},
#             "Visual Scores": {"": image_name},
#             "Content Scores": {"": image_name},
#             "Functional Scores": {"": image_name},
#         }

#         for test in tests:
#             if test == "Full Image Gen":
#                 generated_image_path = f"output/{image_name}/full_image_gen.png"
#             elif test == "Segment Gen":
#                 generated_image_path = f"output/{image_name}/final_segment_gen.png"
#             else:
#                 continue

#             accuracy_score = get_accuracy_score(
#                 original_image_path, generated_image_path
#             )
#             scores = accuracy_score.split(", ")
#             visual_score = int(scores[0].split(": ")[1])
#             content_score = int(scores[1].split(": ")[1])
#             functional_score = int(scores[2].split(": ")[1])
#             overall_score = int(scores[3].split(": ")[1])

#             new_rows["Overall Scores"][test] = overall_score
#             new_rows["Visual Scores"][test] = visual_score
#             new_rows["Content Scores"][test] = content_score
#             new_rows["Functional Scores"][test] = functional_score

#         # Load existing Excel file and append new rows
#         # Read existing sheets
#         existing_dfs = {
#             sheet_name: pd.read_excel(excel_path, sheet_name=sheet_name)
#             for sheet_name in new_rows.keys()
#         }

#         # Append new rows to existing dataframes
#         for sheet_name, new_row in new_rows.items():
#             existing_dfs[sheet_name] = pd.concat(
#                 [existing_dfs[sheet_name], pd.DataFrame([new_row])], ignore_index=True
#             )

#         # Write updated dataframes back to the Excel file
#         with pd.ExcelWriter(excel_path, mode="w") as writer:
#             for sheet_name, df in existing_dfs.items():
#                 df.to_excel(writer, sheet_name=sheet_name, index=False)
#     except Exception as e:
#         print(f"Error: {e}")
#         print(f"Failed to add scores for {image_name}")


def main():
    excel_path = "accuracy_scores.xlsx"
    tests = ["Full Image Gen", "Segment Gen"]

    folder_path = "full_images"
    update_excel_with_scores(folder_path, excel_path, tests)
    print(f"Accuracy scores have been updated in {excel_path}")


if __name__ == "__main__":
    main()
