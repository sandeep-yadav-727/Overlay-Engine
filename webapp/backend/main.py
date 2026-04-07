from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import cv2
import numpy as np
import io
import zipfile

app = FastAPI()

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def find_black_board(image):
    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 70, 255, cv2.THRESH_BINARY_INV)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 40))
    thresh_closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(thresh_closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    valid_boxes = []
    for cnt in contours:
        x_box, y_box, w_box, h_box = cv2.boundingRect(cnt)
        aspect = float(w_box) / h_box
        area = w_box * h_box
        if (w * h * 0.02) < area < (w * h * 0.30):
            if x_box < (w * 0.4):
                if 0.5 < aspect < 2.5:
                    if y_box > (h * 0.05) and y_box < (h * 0.85):
                        roi = gray[y_box:y_box+h_box, x_box:x_box+w_box]
                        valid_boxes.append({
                            "rect": (x_box, y_box, w_box, h_box),
                            "mean": np.mean(roi)
                        })
                        
    if not valid_boxes:
        return None
    valid_boxes.sort(key=lambda b: b['mean'])
    best = valid_boxes[0]
    if best['mean'] > 120:
        return None
    return best["rect"]

@app.post("/api/process")
async def process_images(logo: UploadFile = File(...), images: list[UploadFile] = File(...)):
    # 1. Read Logo
    logo_bytes = await logo.read()
    logo_np = np.frombuffer(logo_bytes, np.uint8)
    logo_img = cv2.imdecode(logo_np, cv2.IMREAD_COLOR)
    
    if logo_img is None:
        return {"error": "Invalid logo image"}
        
    # 2. Prepare ZIP in memory
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for img_file in images:
            img_bytes = await img_file.read()
            img_np = np.frombuffer(img_bytes, np.uint8)
            image = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
            
            if image is None:
                continue
                
            box = find_black_board(image)
            if box is not None:
                x, y, w, h = box
                resized_logo = cv2.resize(logo_img, (w, h))
                image[y:y+h, x:x+w] = resized_logo
                
            # Convert back to bytes
            # Preserve extension
            ext = img_file.filename.split('.')[-1]
            if ext.lower() not in ['jpg', 'jpeg', 'png']:
                ext = 'jpg'
                
            success, encoded_image = cv2.imencode(f".{ext}", image)
            if success:
                zip_file.writestr(img_file.filename, encoded_image.tobytes())
                
    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer, 
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": "attachment; filename=processed_images.zip"}
    )
