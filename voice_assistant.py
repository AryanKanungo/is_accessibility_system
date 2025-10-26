import speech_recognition as sr
import pyttsx3
import os
import pyautogui
import psutil
import time

# ========== INITIAL SETUP ==========
recognizer = sr.Recognizer()
engine = pyttsx3.init()
engine.setProperty('rate', 170)

def speak(text):
    print("Assistant:", text)
    engine.say(text)
    engine.runAndWait()

def listen():
    with sr.Microphone() as source:
        print("\n🎤 Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    try:
        command = recognizer.recognize_google(audio, language="en-in").lower()
        print(f"🗣️ You said: {command}")
        return command
    except Exception:
        speak("Sorry, I didn’t catch that.")
        return ""

# ========== APP DATABASE ==========
APPS = {
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "vscode": r"C:\Users\aryan\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "cmd": "cmd.exe",
    "notepad": "notepad.exe",
    "explorer": "explorer.exe",
    "settings": "start ms-settings:"
}

# ========== OPEN / CLOSE APPS ==========
def open_app(app_name):
    path = APPS.get(app_name)
    if path:
        speak(f"Opening {app_name}")
        os.startfile(path)
    else:
        speak(f"I don’t know how to open {app_name}")

def close_app(app_name):
    for proc in psutil.process_iter(['pid', 'name']):
        if app_name.lower() in proc.info['name'].lower():
            speak(f"Closing {app_name}")
            proc.kill()
            return
    speak(f"{app_name} is not running.")

# ========== SYSTEM ACTIONS ==========
def system_action(command):
    if "close window" in command:
        pyautogui.hotkey("alt", "f4")
        speak("Window closed.")
    elif "lock" in command:
        speak("Locking the system.")
        os.system("rundll32.exe user32.dll,LockWorkStation")
    elif "shutdown" in command:
        speak("Shutting down.")
        os.system("shutdown /s /t 1")
    elif "restart" in command:
        speak("Restarting system.")
        os.system("shutdown /r /t 1")
    elif "screenshot" in command:
        pyautogui.screenshot("screenshot.png")
        speak("Screenshot saved.")
    elif "volume up" in command:
        pyautogui.press("volumeup")
        speak("Volume up.")
    elif "volume down" in command:
        pyautogui.press("volumedown")
        speak("Volume down.")
    elif "mute" in command:
        pyautogui.press("volumemute")
        speak("Volume muted.")

# ========== EXECUTION LOGIC ==========
def execute_command(command):
    if "open" in command:
        for app in APPS:
            if app in command:
                open_app(app)
                return
        system_action(command)

    elif "close" in command:
        for app in APPS:
            if app in command:
                close_app(app)
                return
        system_action(command)

    else:
        system_action(command)

# ========== MAIN LOOP ==========
def main():
    speak("Voice assistant activated. Waiting for your command.")
    while True:
        command = listen()
        if command:
            if "exit" in command or "stop" in command or "quit" in command:
                speak("Goodbye!")
                break
            execute_command(command)

if __name__ == "__main__":
    main()
