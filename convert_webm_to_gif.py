import cv2
from PIL import Image

input_path = "/config/.gemini/antigravity/brain/74fd45dc-2299-4b87-982b-9ac6a381c395/demo_recording.webm"
output_path = "/config/Desktop/Session1/tv-series-admin/demo.gif"

cap = cv2.VideoCapture(input_path)
frames = []

fps = cap.get(cv2.CAP_PROP_FPS) or 25
step = int(fps / 5) or 4

count = 0
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    if count % step == 0:
        h, w, _ = frame.shape
        new_w = 800
        new_h = int(h * (new_w / w))
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        im = Image.fromarray(rgb)
        im_quant = im.quantize(colors=128, method=2)
        frames.append(im_quant)
    count += 1

cap.release()

if frames:
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=200,
        loop=0
    )
    print(f"Successfully created GIF: {output_path} ({len(frames)} frames)")
else:
    print("Failed to extract frames.")
