import os
import sys
import time
from playwright.sync_api import sync_playwright

def main():
    artifact_dir = "/config/.gemini/antigravity/brain/74fd45dc-2299-4b87-982b-9ac6a381c395"
    video_dir = os.path.join(artifact_dir, "video_tmp")
    os.makedirs(video_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        context = browser.new_context(
            record_video_dir=video_dir,
            record_video_size={"width": 1280, "height": 720},
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()

        print("Navigating to app...")
        page.goto("http://localhost:8080/")
        page.wait_for_timeout(2000)

        # Prompt 1: Show all TV series
        print("Sending Prompt 1...")
        page.fill("#input", "Show all TV series in the database")
        page.click("button")
        
        print("Waiting for Prompt 1 reply...")
        page.wait_for_timeout(8000)

        # Prompt 2: Richer prompt showing tool call & database lookup + show stats calculation
        print("Sending Prompt 2...")
        page.fill("#input", "Search for Sci-Fi series in Firestore and calculate show stats for Cosmic Horizons")
        page.click("button")

        print("Waiting for Prompt 2 reply...")
        page.wait_for_timeout(10000)

        print("Finished interaction, closing context...")
        context.close()
        browser.close()

    files = [f for f in os.listdir(video_dir) if f.endswith(".webm")]
    if files:
        src = os.path.join(video_dir, files[0])
        dest = os.path.join(artifact_dir, "demo_recording.webm")
        if os.path.exists(dest):
            os.remove(dest)
        os.rename(src, dest)
        print(f"SUCCESS: Video saved to {dest}")
    else:
        print("No video file generated.")

if __name__ == "__main__":
    main()
