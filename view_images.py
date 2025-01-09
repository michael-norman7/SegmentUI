import os
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

def display_images(project_name):
    output_dir = f"output/{project_name}"
    image1_path = os.path.join(output_dir, f"{project_name}.png")
    image2_path = os.path.join(output_dir, "full_image_gen.png")
    image3_path = os.path.join(output_dir, "final_segment_gen.png")

    if os.path.exists(image1_path) and os.path.exists(image2_path) and os.path.exists(image3_path):
        img1 = mpimg.imread(image1_path)
        img2 = mpimg.imread(image2_path)
        img3 = mpimg.imread(image3_path)

        fig, axs = plt.subplots(1, 3, figsize=(15, 5))
        axs[0].imshow(img1)
        axs[0].axis("off")
        axs[0].set_title(f"{project_name}.png")
        axs[1].imshow(img2)
        axs[1].axis("off")
        axs[1].set_title("full_image_gen.png")
        axs[2].imshow(img3)
        axs[2].axis("off")
        axs[2].set_title("final_segment_gen.png")
        plt.tight_layout()
        plt.show()
    else:
        print(f"Images for project '{project_name}' not found.")


img_dir = "img"
image_projects = [
    d for d in os.listdir(img_dir) if os.path.isdir(os.path.join(img_dir, d))
]

if not image_projects:
    print("No image projects found in the 'img' directory.")
    quit()

print("Image projects found:")
for idx, project in enumerate(image_projects):
    print(f"{idx}: {project}")

# Prompt user to select an image project
while True:
    try:
        selection = int(
            input(
                "Enter the number of the image project you want to process: "
            )
        )
        if 0 <= selection < len(image_projects):
            display_images(image_projects[selection])
            break
        else:
            print("Invalid selection. Please enter a number from the list.")
    except ValueError:
        print("Invalid input. Please enter a number.")
