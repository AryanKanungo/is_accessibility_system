# voice_assistant.py
"""
Handles all voice-related functionality:
- Text-to-Speech (speak)
- Speech-to-Text (listen)
- Command parsing and execution
- Background listener thread
"""

import speech_recognition as sr
import pyttsx3
import threading
import os, psutil, webbrowser, pyautogui
from datetime import datetime
import time
import config # For APPS dictionary
import queue # <--- CHANGED: Import queue

class VoiceController:
    """Manages all voice I/O and command logic on a separate thread."""

    def __init__(self, shared_state):
        """Initializes the voice engine, recognizer, and shared thread state."""
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 170)
        
        self.state = shared_state
        self.lock = shared_state['lock']
        
        self.speak_queue = queue.Queue() # <--- CHANGED: Add a thread-safe queue

    # <--- CHANGED: This function is now non-blocking
    def speak(self, text):
        """Queues text to be spoken by the background thread (non-blocking)."""
        print(f"Assistant (Queued): {text}")
        self.speak_queue.put(text)

    def _listen_once(self, timeout=4, phrase_time_limit=5):
        """Listens once for a voice command and returns the text."""
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print(" Listening for command...")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            
            command = self.recognizer.recognize_google(audio, language="en-in").lower()
            print(f" You said: {command}")
            return command
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except Exception as e:
            print(f"Voice recognition error: {e}")
            return ""

    def _open_app(self, app_name):
        """Opens an application based on the config.APPS dictionary."""
        path = config.APPS.get(app_name)
        if path:
            self.speak(f"Opening {app_name}") # This now queues the speech
            try:
                if path.startswith("start "): # For commands like "start ms-settings:"
                    os.system(path)
                else:
                    os.startfile(path)
            except Exception as e:
                self.speak(f"Failed to open {app_name}")
                print(f"Open error: {e}")
        else:
            self.speak(f"I don’t know how to open {app_name}")

    def _close_app(self, app_name):
        """Finds and terminates a running process by its name."""
        if app_name == "explorer":
            os.system("taskkill /f /im explorer.exe")
            self.speak("Explorer closed.")
            return

        for proc in psutil.process_iter(['pid', 'name']):
            try:
                proc_name = (proc.info['name'] or "").lower()
                if app_name.lower() in proc_name or f"{app_name}.exe" in proc_name:
                    self.speak(f"Closing {app_name}")
                    proc.kill()
                    return
            except Exception:
                continue
        self.speak(f"{app_name} is not running.")

    def _system_action(self, command):
        """Executes system-level commands like volume, shutdown, or hotkeys."""
        if "close window" in command:
            pyautogui.hotkey("alt", "f4")
            self.speak("Window closed.")
        elif "lock" in command:
            self.speak("Locking the system.")
            os.system("rundll32.exe user32.dll,LockWorkStation")
        elif "shutdown" in command:
            self.speak("Shutting down.")
            os.system("shutdown /s /t 1")
        elif "restart" in command:
            self.speak("Restarting system.")
            os.system("shutdown /r /t 1")
        elif "screenshot" in command:
            pyautogui.screenshot(f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            self.speak("Screenshot saved.")
        elif "volume up" in command:
            pyautogui.press("volumeup")
            self.speak("Volume up.")
        elif "volume down" in command:
            pyautogui.press("volumedown")
            self.speak("Volume down.")
        elif "mute" in command:
            pyautogui.press("volumemute")
            self.speak("Volume muted.")
        elif "show desktop" in command or "minimize all" in command:
            pyautogui.hotkey("win", "d")
            self.speak("Showing desktop.")
        else:
            return False 
        return True 

    def _execute_command(self, command):
        """The main command router; parses text and calls the correct action function."""
        if not command:
            return
        # --- Check for 'open' commands ---
        if "open" in command:
            for app in config.APPS:
                if app in command:
                    self._open_app(app)
                    return
        # --- Check for 'close' commands ---
        if "close" in command:
            for app in config.APPS:
                if app in command:
                    self._close_app(app)
                    return
            if "window" in command:
                self._system_action("close window")
            return
        # --- Check for 'search' commands ---
        if "search google for" in command:
            query = command.split("search google for", 1)[1].strip()
            if query:
                self.speak(f"Searching Google for {query}")
                webbrowser.open(f"https://www.google.com/search?q={query}")
                return
        # --- Check for other web/info commands ---
        if "youtube" in command and "open" in command:
            self.speak("Opening YouTube")
            webbrowser.open("https://www.youtube.com")
            return
        if "what time" in command or "time is it" in command:
            now = datetime.now().strftime("%I:%M %p")
            self.speak(f"The time is {now}")
            return
        # --- Check for mouse/scroll commands ---
        if "click" in command and "double" not in command:
            pyautogui.click()
            self.speak("Clicked.")
            return
        if "double click" in command or "double-click" in command:
            pyautogui.doubleClick()
            self.speak("Double clicked.")
            return
        if "scroll up" in command:
            pyautogui.scroll(500)
            self.speak("Scrolled up.")
            return
        if "scroll down" in command:
            pyautogui.scroll(-500)
            self.speak("Scrolled down.")
            return
        # --- Fallback to system actions ---
        if not self._system_action(command):
            pass

    # <--- CHANGED: This whole loop is modified
    def _voice_listener_loop(self):
        """The main loop for the background thread; handles both speaking and listening."""
        self.speak("Voice assistant thread started.") 
        
        while True:
            # --- 1. (High Priority) Check the speak queue and speak any messages.
            try:
                text_to_speak = self.speak_queue.get(block=False)
                
                print(f"Assistant (Speaking): {text_to_speak}")
                with self.lock: # Use the lock just for the engine
                    try:
                        self.engine.say(text_to_speak)
                        self.engine.runAndWait()
                    except Exception as e:
                        print(f"Pyttsx3 error: {e}")
                
                self.speak_queue.task_done()
                continue # Go back to check queue immediately
            
            except queue.Empty:
                pass # No speech queued, continue to listening

            # --- 2. (Low Priority) If not speaking, check if voice is active.
            with self.lock:
                active = self.state['voice_active']
            
            if not active:
                time.sleep(0.1) # Sleep if not active and no speech
                continue
            
            # --- 3. If active, block this thread to listen for a command.
            command = self._listen_once(timeout=4, phrase_time_limit=4)
            
            # --- 4. If a command was heard, process it.
            if command:
                cmd = command.lower()
                # --- Handle meta-commands (exit, quit) ---
                if "exit voice" in cmd or "stop listening" in cmd:
                    with self.lock:
                        self.state['voice_active'] = False
                    self.speak("Voice mode deactivated.")
                
                elif "quit assistant" in cmd or "shutdown assistant" in cmd:
                    self.speak("Shutting down assistant.")
                    time.sleep(2)
                    os._exit(0) # Force exit the entire application
                
                # --- Handle all other commands ---
                else:
                    self._execute_command(cmd)
            else:
                # --- No command heard, sleep briefly ---
                time.sleep(0.05)

    def start_listener_thread(self):
        """Starts the _voice_listener_loop in a new daemon thread."""
        t = threading.Thread(target=self._voice_listener_loop, daemon=True)
        t.start()