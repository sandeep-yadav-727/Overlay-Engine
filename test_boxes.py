import cv2, glob, os, numpy as np
base_dir = r'd:\mini\Image overlay'
img_paths = glob.glob(os.path.join(base_dir, 'images', '*.*'))
with open(os.path.join(base_dir, 'out_py2.txt'), 'w', encoding='utf-8') as f:
    for img_path in img_paths:
        f.write(f"Testing {os.path.basename(img_path)}\n")
        image = cv2.imread(img_path)
        if image is None: continue
        
        # Resize to work faster and have consistent params
        h_orig, w_orig = image.shape[:2]
        ratio = 800.0 / h_orig
        dim = (int(w_orig * ratio), 800)
        resized = cv2.resize(image, dim)
        
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, 11, 17, 17)
        edged = cv2.Canny(gray, 30, 200)
        
        contours, _ = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]
        
        screenCnt = None
        for c in contours:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.05 * peri, True) # More tolerance
            
            if len(approx) >= 4 and len(approx) <= 6:
                screenCnt = approx
                break
                
        if screenCnt is not None:
            c = screenCnt
            x, y, w, h = cv2.boundingRect(c)
            area = w*h
            f.write(f"  Found polygon (x, y, w, h, area): {x/ratio}, {y/ratio}, {w/ratio}, {h/ratio}, {area/(ratio*ratio)}\n")
        else:
            f.write("  No polygon found.\n")
