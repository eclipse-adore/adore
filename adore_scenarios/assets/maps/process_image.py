import cv2
import numpy as np
import os


MAX_NUM_COLORS = 15

hue_weight = 1.0
saturation_weight = 1.0
brightness_weight = 0.20

def process_images(img_dict): # similar to original but does in batches
    img_dict = {filename: denoise_image(img) for filename, img in img_dict.items()}
    # img_dict = {filename: white_balance_opencv(img) for filename, img in img_dict.items()}
    img_dict = quantize_colors_combined(img_dict)
    # img_dict = {filename: white_balance_opencv(img) for filename, img in img_dict.items()}
    return img_dict 


def apply_white_balance_to_clusters(centers):
    """Use OpenCV's auto white balance function on an image with one pixel per cluster center, converting to BGR first."""
    print(centers)
    # Convert HSV centers to BGR for proper white balancing
    centers_bgr = cv2.cvtColor(np.expand_dims(centers, axis=0).astype(np.uint8), cv2.COLOR_HSV2BGR)

    print(centers_bgr)
    
    # Apply OpenCV white balance
    wb = cv2.xphoto.createSimpleWB()
    balanced_image = wb.balanceWhite(centers_bgr)
    
    # Convert back to HSV to extract the adjusted centers
    adjusted_centers_hsv = cv2.cvtColor(balanced_image, cv2.COLOR_BGR2HSV)[0]

    print(adjusted_centers_hsv)
    
    return adjusted_centers_hsv.astype(np.uint8)

def quantize_colors_combined(img_dict):
    """Compute global color clusters and apply them to all images."""
    all_data = []
    for img in img_dict.values():
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        data = np.stack([h.flatten() * hue_weight, s.flatten() * saturation_weight, v.flatten() * brightness_weight], axis=1)
        all_data.append(data)
    
    all_data = np.vstack(all_data).astype(np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
    _, _, centers = cv2.kmeans(all_data, MAX_NUM_COLORS, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    
    # Apply white balance to clusters before assigning pixels
    moved_centers = apply_white_balance_to_clusters(centers)

    processed_images = {}
    for filename, img in img_dict.items():
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        data = np.stack([h.flatten() * hue_weight, s.flatten() * saturation_weight, v.flatten() * brightness_weight], axis=1).astype(np.float32)
        
        # Assign each pixel to the closest cluster center
        labels = np.argmin(np.linalg.norm(data[:, None] - centers[None, :], axis=2), axis=1)
        
        # Replace cluster colors with their corresponding adjusted colors
        clustered_pixels = moved_centers[labels]
        
        # Reshape into image format
        clustered_h = clustered_pixels[:, 0].reshape(h.shape).astype(np.uint8)
        clustered_s = clustered_pixels[:, 1].reshape(s.shape).astype(np.uint8)
        clustered_v = clustered_pixels[:, 2].reshape(v.shape).astype(np.uint8)
        clustered_hsv = cv2.merge([clustered_h, clustered_s, clustered_v])
        
        processed_images[filename] = cv2.cvtColor(clustered_hsv, cv2.COLOR_HSV2BGR)

    return processed_images


def process_image(img):

    img = denoise_image(img)
    img = quantize_colors(img) 
    img = white_balance_opencv(img)

    return img


def denoise_image(img):
    """Apply strong denoising to remove thin diagonal lines and noise."""
    blur = cv2.GaussianBlur(img, (7, 7), 0)
    blur = cv2.GaussianBlur(blur, (3, 3), 0)

    denoised_image = cv2.fastNlMeansDenoisingColored(blur, None, 10, 10, 7, 21)
    
    return denoised_image

def white_balance_opencv(img):
    wb = cv2.xphoto.createSimpleWB()
    return wb.balanceWhite(img)

def quantize_colors(img, k=MAX_NUM_COLORS):
    """Cluster colors based primarily on hue similarity while considering saturation and brightness."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    
    # Stack hue, but weight saturation and brightness lower in clustering
    data = np.stack([h.flatten() * hue_weight, (s.flatten() * saturation_weight ), (v.flatten() * brightness_weight)], axis=1).astype(np.float32)
    
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
    _, labels, centers = cv2.kmeans(data, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    
    # Ensure strict assignment to only k colors
    centers = np.uint8(centers)
    clustered_pixels = centers[labels.flatten()]  # Replace each pixel with its cluster center
    
    # Reshape back into separate channels
    clustered_h = (clustered_pixels[:, 0] / hue_weight ).reshape(h.shape)
    clustered_s = (clustered_pixels[:, 1] / saturation_weight ).reshape(s.shape)  # Undo scaling
    clustered_v = (clustered_pixels[:, 2] / brightness_weight ).reshape(v.shape)  # Undo scaling
    
    # Merge back with restored saturation and brightness
    clustered_hsv = cv2.merge([clustered_h, clustered_s, clustered_v])
    clustered_hsv = clustered_hsv.astype(np.uint8)
    clustered_bgr = cv2.cvtColor(clustered_hsv, cv2.COLOR_HSV2BGR)
    return clustered_bgr


def count_unique_colors(img):
    """Count the number of unique colors in an image."""
    reshaped = img.reshape(-1, 3)
    unique_colors = np.unique(reshaped, axis=0)
    print(len(unique_colors) , " unique colors")
    return len(unique_colors)

def save_images(img_dict):
    """Save all images in the dictionary to the current directory."""
    for filename, img in img_dict.items():
        output_path = os.path.splitext(filename)[0] + ".png" # Change extension to .png
        cv2.imwrite(output_path, img, [cv2.IMWRITE_PNG_COMPRESSION, 0])  # Lossless PNG
        print(f"Processed image saved at: {output_path}")

def process_images_in_folder(folder_path):
    """Process all .jpg images in the folder, skipping already processed ones."""
    all_original_images = {}
    for filename in os.listdir(folder_path):
        if filename.endswith(".jpg"):
            image_path = os.path.join(folder_path, filename)
            output_path = os.path.join(folder_path, filename)
            
            original_image = cv2.imread(image_path)
            
            if original_image is None:
                print(f"Skipping {filename}, could not load image.")
                continue

            all_original_images[filename] = original_image
    
    all_processed_images = process_images(all_original_images)
      
    save_images(all_processed_images)



# Run processing on all images in the current directory
process_images_in_folder(".")
