import cv2
import numpy as np
import os
import glob

def find_black_board(image):
    h, w = image.shape[:2]
    
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 1. Dark pixel thresholding
    # The blackboard is dark. THRESH_BINARY_INV makes dark regions white mask.
    # Higher threshold to accommodate lighting/glare on the slate
    _, thresh = cv2.threshold(gray, 70, 255, cv2.THRESH_BINARY_INV)
    
    # 2. Morphological close to bridge gaps caused by white chalk text
    # A slightly smaller kernel avoids merging with nearby shadows
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 30))
    thresh_closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    # Erode slightly to shrink the detected boundary inward, ensuring it doesn't bleed out
    erode_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    thresh_closed = cv2.erode(thresh_closed, erode_kernel)
    
    # Find contours
    contours, _ = cv2.findContours(thresh_closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    valid_boxes = []
    
    for cnt in contours:
        x_box, y_box, w_box, h_box = cv2.boundingRect(cnt)
        area = w_box * h_box
        
        # 3. Size constraints: The board shouldn't be tiny or cover the whole image
        if (w * h * 0.02) < area < (w * h * 0.30):
            # 4. Location constraint: Left side of the image
            if x_box < (w * 0.4):
                # 5. Aspect ratio constraint: Roughly rectangular but not extremely thin
                aspect = float(w_box) / h_box
                if 0.5 < aspect < 2.5:
                    # 6. Position constraint: skip extreme top and bottom edges
                    if y_box > (h * 0.05) and y_box < (h * 0.85):
                        # Let's also ensure its mean intensity in grayscale is relatively dark
                        # so we don't pick up something bright by mistake
                        roi = gray[y_box:y_box+h_box, x_box:x_box+w_box]
                        mean_val = np.mean(roi)
                        valid_boxes.append({
                            "rect": (x_box, y_box, w_box, h_box),
                            "mean": mean_val,
                            "area": area
                        })
                    
    if not valid_boxes:
        return None
        
    # Pick the box that is darkest (lowest mean intensity)
    # Alternatively we could pick the largest area, but darkest is safest for a "black" board
    valid_boxes.sort(key=lambda b: b['mean'])
    best_box = valid_boxes[0]
    
    # If the darkest box is still quite bright, maybe we didn't find the board
    if best_box['mean'] > 120:
        return None
        
    return best_box["rect"]

def process_images(input_dir, output_dir, logo_path):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    logo = cv2.imread(logo_path)
    if logo is None:
        print(f"Error: Could not read logo image from {logo_path}")
        return
        
    image_paths = glob.glob(os.path.join(input_dir, '*.[jJ][pP][eE][gG]')) + \
                  glob.glob(os.path.join(input_dir, '*.[jJ][pP][gG]')) + \
                  glob.glob(os.path.join(input_dir, '*.[pP][nN][gG]'))
                  
    if not image_paths:
        print("No images found in input directory.")
        return
        
    for img_path in image_paths:
        filename = os.path.basename(img_path)
        print(f"Processing {filename}...")
        
        image = cv2.imread(img_path)
        if image is None:
            print(f"  Skipping {filename}: could not read.")
            continue
            
        box = find_black_board(image)
        if box is None:
            print(f"  No black board found in {filename}. Skipping.")
            cv2.imwrite(os.path.join(output_dir, filename), image) # Save unchanged
            continue
            
        x, y, w, h = box
        print(f"  Found black board at Rect(x:{x}, y:{y}, w:{w}, h:{h})")
        
        # Add a larger margin inset to keep the logo strictly inside the board
        margin_x = int(w * 0.08)
        margin_y = int(h * 0.10)
        x += margin_x
        y += margin_y
        w -= (margin_x * 2)
        h -= (margin_y * 2)
        
        # Resize logo to fit the inset bounding box
        resized_logo = cv2.resize(logo, (w, h))
        
        # Paste the logo
        image[y:y+h, x:x+w] = resized_logo
        
        # Save output
        output_path = os.path.join(output_dir, filename)
        cv2.imwrite(output_path, image)
        print(f"  Saved to {output_path}")

if __name__ == "__main__":
    base_dir = r"d:\mini\Image overlay"
    images_dir = os.path.join(base_dir, "images")
    output_images_dir = os.path.join(base_dir, "output_images")
    logo_file = os.path.join(base_dir, "Logo.jpeg")
    
    process_images(images_dir, output_images_dir, logo_file)
    print("Done!")
