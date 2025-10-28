# main.py
from threading import Thread
from voice_assistant import voice_loop
from face_tracking import run_tracking

if __name__ == "__main__":
    print("Starting Head + Voice Mouse system...")
    t = Thread(target=voice_loop, daemon=True)
    t.start()
    run_tracking()
