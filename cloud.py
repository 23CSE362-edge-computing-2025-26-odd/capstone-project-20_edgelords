from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from io import BytesIO
from PIL import Image
import torch
import torchvision.transforms as transforms

app = FastAPI()

# Loading CNN Model
model = torch.load("lane_cnn.pt", map_location="cpu")
model.eval()

transform = transforms.Compose([
    transforms.Resize((128, 128)),
    transforms.ToTensor()
])

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    image = Image.open(BytesIO(await file.read())).convert("RGB")
    tensor = transform(image).unsqueeze(0)
    
    with torch.no_grad():
        outputs = model(tensor)
        _, predicted = torch.max(outputs, 1)

    # Map class index to action
    actions = {0: "LEFT", 1: "RIGHT", 2: "KEEP"}
    decision = actions[int(predicted.item())]

    return JSONResponse({"decision": decision})
