'''Note: This is the code used in the Hugging Face Space that is used to 
host the CNN Model to predict Lane Changing. Only added here for reference.'''

# app.py
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from PIL import Image
import io
import os

app = FastAPI()

MODEL = None
MODEL_PATH = "lane_cnn.pt"
USE_TORCH = False
if os.path.exists(MODEL_PATH):
    try:
        import torch
        import torchvision.transforms as transforms
        MODEL = torch.load(MODEL_PATH, map_location="cpu")
        MODEL.eval()
        USE_TORCH = True
        # example transforms 
        TRANSFORM = transforms.Compose([
            transforms.Resize((128, 128)),
            transforms.ToTensor(),
        ])
        print("Loaded model:", MODEL_PATH)
    except Exception as e:
        print("Failed loading model:", e)
        MODEL = None
        USE_TORCH = False

# Simple fallback heuristic 
def predict_with_model(image: Image.Image) -> str:
    if USE_TORCH and MODEL is not None:
        try:
            tensor = TRANSFORM(image).unsqueeze(0)  # [1,C,H,W]
            with __import__("torch").no_grad():
                out = MODEL(tensor)
                _, pred = out.max(1)
                idx = int(pred.item())
                return {0: "LEFT", 1: "RIGHT", 2: "FORWARD"}.get(idx, "FORWARD")
        except Exception as e:
            print("Model inference error:", e)
            return "FORWARD"
    # Fallback: always forward 
    return "FORWARD"

@app.get("/")
def index():
    return {"status": "ok", "note": "POST a JPEG body to /predict to get LEFT/RIGHT/FORWARD"}

# Accept raw JPEG bytes (ESP32 POSTs raw bytes with Content-Type image/jpeg)
@app.post("/predict", response_class=PlainTextResponse)
async def predict(request: Request):
    body = await request.body()
    if not body:
        return PlainTextResponse("FORWARD")
    try:
        img = Image.open(io.BytesIO(body)).convert("RGB")
    except Exception as e:
        print("Error decoding image:", e)
        return PlainTextResponse("FORWARD")
    decision = predict_with_model(img)
    return PlainTextResponse(decision)
