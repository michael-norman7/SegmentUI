import os
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import sys


def display_images(project_name):
    output_dir = f"output/{project_name}"
    image1_path = os.path.join(output_dir, f"{project_name}.png")
    image2_path = os.path.join(output_dir, "full_image_gen.png")
    image3_path = os.path.join(output_dir, "llm_final_segment_gen.png")
    image4_path = os.path.join(output_dir, "set_final_segment_gen.png")
    image5_path = os.path.join(output_dir, "overlap_final_segment_gen.png")

    # output_dir = f"img/{project_name}"
    # image1_path = os.path.join(output_dir, f"{project_name}.png")
    # image2_path = os.path.join(output_dir, f"{project_name}_bounding_boxes.png")
    # image3_path = os.path.join(output_dir, f"{project_name}_bounding_boxes.png")
    # image4_path = os.path.join(output_dir, f"{project_name}_set_bounding_boxes.png")
    # image5_path = os.path.join(output_dir, f"{project_name}_overlap_bounding_boxes.png")

    if (
        os.path.exists(image1_path)
        and os.path.exists(image2_path)
        and os.path.exists(image3_path)
        and os.path.exists(image4_path)
        and os.path.exists(image5_path)
    ):
        img1 = mpimg.imread(image1_path)
        img2 = mpimg.imread(image2_path)
        img3 = mpimg.imread(image3_path)
        img4 = mpimg.imread(image4_path)
        img5 = mpimg.imread(image5_path)

        fig, axs = plt.subplots(1, 5, figsize=(15, 10))
        axs[0].imshow(img1)
        axs[0].axis("off")
        axs[0].set_title(f"{project_name}.png")
        axs[1].imshow(img2)
        axs[1].axis("off")
        axs[1].set_title("full_image_gen.png")
        axs[2].imshow(img3)
        axs[2].axis("off")
        axs[2].set_title("llm_segment_gen.png")
        axs[3].imshow(img4)
        axs[3].axis("off")
        axs[3].set_title("set_segment_gen.png")
        axs[4].imshow(img5)
        axs[4].axis("off")
        axs[4].set_title("overlap_segment_gen.png")
        plt.tight_layout()

        # Create comparisons directory if it doesn't exist
        comparisons_dir = "comparisons"
        os.makedirs(comparisons_dir, exist_ok=True)

        # Save the comparison plot
        save_path = os.path.join(comparisons_dir, f"{project_name}_comparison.png")
        plt.savefig(save_path, bbox_inches="tight", dpi=300)
        print(f"Comparison image saved to: {save_path}")

        plt.show()
    else:
        print(f"Images for project '{project_name}' not found.")

def main():
    img_dir = "img"
    image_projects = [
        d for d in os.listdir(img_dir) if os.path.isdir(os.path.join(img_dir, d))
    ]

    if not image_projects:
        print("No image projects found in the 'img' directory.")
        quit()

    # If project name is provided via command line
    if len(sys.argv) > 1:
        project_name = sys.argv[1]
        if project_name in image_projects:
            display_images(project_name)
        else:
            print(f"Project '{project_name}' not found. Available projects:")
            for project in image_projects:
                print(f"  - {project}")
        return

    # If no project name provided, prompt user to select one
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
                display_images(image_projects[selection])
                break
            else:
                print("Invalid selection. Please enter a number from the list.")
        except ValueError:
            print("Invalid input. Please enter a number.")


if __name__ == "__main__":
    main()
