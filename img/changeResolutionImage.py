import os
from PIL import Image

# Set the root directory where the folders (e.g., nama1, nama2) are located
root_dir = "raw/"

# Function to resize an image while maintaining the aspect ratio
def resize_image(image_path, new_width):
    with Image.open(image_path) as img:
        width_percent = (new_width / float(img.size[0]))
        new_height = int((float(img.size[1]) * float(width_percent)))
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        img.save(image_path)  # Overwrite the original image

# Iterate over all folders and files
for folder_name in os.listdir(root_dir):
    folder_path = os.path.join(root_dir, folder_name)
    if os.path.isdir(folder_path):
        for file_name in os.listdir(folder_path):
            if file_name.lower().endswith(('png', 'jpg', 'jpeg')):
                file_path = os.path.join(folder_path, file_name)
                resize_image(file_path, 500)

print("All images have been resized.")
