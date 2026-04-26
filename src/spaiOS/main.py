import os
import subprocess
import tempfile
from pathlib import Path

import ollama


def check_ollama() -> bool:
    try:
        ollama.list()
        return True
    except Exception as e:
        print(f"[ERROR] Ollama not reachable: {e}")
        print("  Start it with: ollama serve")
        return False


def smoke_test() -> None:
    print("\n--- Smoke test: llama3.2:3b ---")
    response = ollama.chat(
        model="llama3.2:3b",
        messages=[{"role": "user", "content": "Say hi in exactly 5 words."}],
    )
    print("Response:", response["message"]["content"])


def vision_test() -> None:
    print("\n--- Vision test: moondream ---")

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        screenshot_path = Path(f.name)

    env = {**os.environ, "DISPLAY": ":0"}
    result = subprocess.run(
        ["scrot", "-o", str(screenshot_path)], capture_output=True, env=env
    )
    if result.returncode != 0:
        print(f"[ERROR] scrot failed: {result.stderr.decode()}")
        print("  Install with: sudo apt install scrot")
        return

    size = screenshot_path.stat().st_size
    if size == 0:
        print("[ERROR] scrot wrote an empty file — DISPLAY may not be accessible")
        screenshot_path.unlink()
        return

    print(f"  Screenshot captured: {size // 1024}KB")
    response = ollama.chat(
        model="moondream:latest",
        messages=[
            {
                "role": "user",
                "content": "Describe what you see on this screen in one sentence.",
                "images": [str(screenshot_path)],
            }
        ],
    )
    screenshot_path.unlink()
    print("Description:", response["message"]["content"])


def main() -> None:
    if not check_ollama():
        return

    smoke_test()
    vision_test()
    print("\n[OK] All tests passed.")


if __name__ == "__main__":
    main()
