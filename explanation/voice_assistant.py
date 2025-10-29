# voice_assistant.py
"""
Handles all voice-related function on a separate, dedicated thread.
Includes:
Text-to-Speech (speak)
Speech-to-Text (listen)
Command parsing and execution

This runs in the background so it doesnt collide with the camera (GUI) thread.
"""

import speech_recognition as sr     #Library for converting speech to text
import pyttsx3                      #Library for converting text to speech
import threading                     #runs voice part on a different thread than main thread
import os, psutil, webbrowser, pyautogui #controls system,givesaction control sich as mouse keyboard
from datetime import datetime        #gives timestamp
import time
import config # gives a dictionary for Apps
import queue # For thread-safe TTS

class VoiceController:
    """
    Manages the voice control . A class is created in main.py
    and run on a separate thread using the 'start_listener_thread' method.
    """

    def __init__(self, shared_state):
        """
        Initializes the voice engine, recognizer, and shared state.
        shared_state is the dictionary from main.py used to interact between  main thread and this one.
        """
        
        self.recognizer = sr.Recognizer() # starts the speech recognition engine
        
        
        self.engine = pyttsx3.init() # starts the TTS engine
        self.engine.setProperty('rate', 170) # Set a comfortable speaking rate
        
        
        self.state = shared_state  # Store the shared state dictionary 
        self.lock = shared_state['lock']
        
        # Create a thread-safe Queue, The main thread will 'put' messages in here. This voice thread will 'get' messages from here.
        self.speak_queue = queue.Queue()

    def speak(self, text):
        """
        Queues text to be spoken. 
        """
        print(f"Assistant (Queued): {text}")
        self.speak_queue.put(text)

    def _listen_once(self, timeout=4, phrase_time_limit=5):
        """
        Listens for a single command. 
        designed to block the background voice thread, not the main thread. 
        Returns the recognized command as a string, or an empty string if it fails.
        """
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print(" Listening for command...")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit) # Use Google Speech Recognition to convert audio to text
           
            command = self.recognizer.recognize_google(audio, language="en-in").lower()
            print(f" You said: {command}")
            return command
        
        
        except sr.WaitTimeoutError: # in case no speech was heard
            return ""
        except sr.UnknownValueError:  # in case speech was garbled
            return ""
        except Exception as e:
            print(f"Voice recognition error: {e}")
            return ""

    # -- Executing Commands --

    def _open_app(self, app_name): """function to open an application from the config list."""
        path = config.APPS.get(app_name)
        if path:
            self.speak(f"Opening {app_name}") 
            try:
                if path.startswith("start "):
                    os.system(path)
                else:
                    os.startfile(path)  # this for 'os.startfile'such as ex- .exe files, documents, etc.
            except Exception as e:
                self.speak(f"Failed to open {app_name}")
                print(f"Open error: {e}")
        else:
            self.speak(f"I don’t know how to open {app_name}")

    def _close_app(self, app_name): """Internal function to find and close (kill) a running process by name."""
        # Special case
        if app_name == "explorer":
            os.system("taskkill /f /im explorer.exe")
            self.speak("Explorer closed.")
            return

        for proc in psutil.process_iter(['pid', 'name']):
            try:
                # Get the process name to be closed
                proc_name = (proc.info['name'] or "").lower()
                # Check if our app_name is in the process name
                if app_name.lower() in proc_name or f"{app_name}.exe" in proc_name:
                    self.speak(f"Closing {app_name}")
                    proc.kill() # Exit the process
                    return
            except Exception:
                continue
        self.speak(f"{app_name} is not running.")

    def _system_action(self, command): """Internal function to perform system actions like hotkeys."""
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
            return False # Command was not a system action
        return True # Command was execited

    def _execute_command(self, command): """It parses the command string and decides which action to take."""
        if not command:
            return

        # -- Check for App Commands (Open/Close) --
        if "open" in command:
            for app in config.APPS:
                if app in command:
                    self._open_app(app)
                    return
        if "close" in command:
            for app in config.APPS:
                if app in command:
                    self._close_app(app)
                    return
            # Fallback for "close window"
            if "window" in command:
                self._system_action("close window")
            return

        # -- Check for Web/Info Commands --
        if "search google for" in command:
            query = command.split("search google for", 1)[1].strip()
            if query:
                self.speak(f"Searching Google for {query}")
                webbrowser.open(f"https://www.google.com/search?q={query}")
                return
        if "youtube" in command and "open" in command:
            self.speak("Opening YouTube")
            webbrowser.open("https://www.youtube.com")
            return
        if "what time" in command or "time is it" in command:
            now = datetime.now().strftime("%I:%M %p")
            self.speak(f"The time is {now}")
            return

        # -- Check for Mouse Commands --
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

        # --Fallback to System Actions --
        if not self._system_action(command):
            
            pass

    def _voice_listener_loop(self):
                                    """The main loop for the background voice thread."""
        # Queue the initial startup message
        self.speak("Voice assistant thread started.") 
        
        while True:
            # --Check Speak Queue --
            try:
                text_to_speak = self.speak_queue.get(block=False)
                
                # If we get one, speak it.
                # blocks this background thread, NOT the main camera thread.
                print(f"Assistant (Speaking): {text_to_speak}")
                with self.lock: # helps access the TTS engine
                    try:
                        self.engine.say(text_to_speak)
                        self.engine.runAndWait()
                    except Exception as e:
                        #find errors
                        print(f"Pyttsx3 error: {e}")
                
                # Mark task as done
                self.speak_queue.task_done()
                continue 
            
            except queue.Empty:
                pass 

            # -- Check for Listening --
            with self.lock:
                active = self.state['voice_active']
            
            if not active:
                time.sleep(0.1)
                continue
            command = self._listen_once(timeout=4, phrase_time_limit=4)  # If active then listen for a command 
            
            # If we heard a command
            if command:
                cmd = command.lower()
                
                # --Handle Meta Commands --
                if "exit voice" in cmd or "stop listening" in cmd:
                    # Deactivate voice
                    with self.lock:
                        self.state['voice_active'] = False
                    self.speak("Voice mode deactivated.")
                
                elif "quit assistant" in cmd or "shutdown assistant" in cmd:
                    self.speak("Shutting down assistant.")
                    # Give the assistant time to speak before exiting
                    time.sleep(2)
                    os._exit(0)
                
                else:
                    self._execute_command(cmd)
            else:
                time.sleep(0.05)

    def start_listener_thread(self): """Starts the background voice listener loop.The ONLY function in this class that main.py calls."""
        # Create a new thread targeting our '_voice_listener_loop' function
        # automatically closes when we close the main program
        t = threading.Thread(target=self._voice_listener_loop, daemon=True)
        t.start()
