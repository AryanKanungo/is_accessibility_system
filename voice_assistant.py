# voice_assistant.py
import os, webbrowser, time, threading, psutil, pyautogui
import speech_recognition as sr, pyttsx3
from datetime import datetime
from config import APP_PATHS

recognizer = sr.Recognizer()
engine = pyttsx3.init()
engine.setProperty('rate', 170)

voice_lock = threading.Lock()
voice_active = False

def speak(text):
    with voice_lock:
        print("Assistant:", text)
        engine.say(text)
        engine.runAndWait()

def listen_once(timeout=4, phrase_time_limit=5):
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print("Listening for command...")
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        return recognizer.recognize_google(audio, language="en-in").lower()
    except:
        return ""

def open_app(app):
    path = APP_PATHS.get(app)
    if path:
        speak(f"Opening {app}")
        os.startfile(path)
    else:
        speak(f"I don’t know how to open {app}")

def close_app(app):
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if app.lower() in (proc.info['name'] or "").lower():
                speak(f"Closing {app}")
                proc.kill()
                return
        except:
            continue
    speak(f"{app} not running")

def execute_command(command):
    if not command: return
    if "open" in command:
        for app in APP_PATHS:
            if app in command:
                open_app(app)
                return
        if "youtube" in command:
            speak("Opening YouTube")
            webbrowser.open("https://www.youtube.com")
            return
    elif "close" in command:
        for app in APP_PATHS:
            if app in command:
                close_app(app)
                return
    elif "time" in command:
        now = datetime.now().strftime("%I:%M %p")
        speak(f"The time is {now}")
        return
    elif "click" in command:
        pyautogui.click()
        speak("Clicked")
        return

def voice_loop():
    global voice_active
    speak("Voice assistant active.")
    while True:
        if not voice_active:
            time.sleep(0.2)
            continue
        cmd = listen_once()
        if cmd:
            if "stop listening" in cmd:
                voice_active = False
                speak("Voice deactivated.")
            else:
                execute_command(cmd)
