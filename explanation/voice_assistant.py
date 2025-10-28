# voice_assistant.py
"""
Handles all voice-related functionality on a separate, dedicated thread.
This includes:
- Text-to-Speech (speak)
- Speech-to-Text (listen)
- Command parsing and execution

This runs in the background so it never freezes the main camera (GUI) thread.
"""

import speech_recognition as sr
import pyttsx3
import threading
import os, psutil, webbrowser, pyautogui
from datetime import datetime
import time
import config # For APPS dictionary
import queue # For thread-safe communication

class VoiceController:
    """
    Manages all voice I/O. An instance of this class is created in main.py
    and run on a separate thread using the 'start_listener_thread' method.
    """

    def __init__(self, shared_state):
        """
        Initializes the voice engine, recognizer, and shared state.
        
        Args:
            shared_state (dict): The dictionary from main.py used to communicate
                                 between the main thread and this one.
        """
        # Initialize the speech recognition engine
        self.recognizer = sr.Recognizer()
        
        # Initialize the text-to-speech (TTS) engine
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 170) # Set a comfortable speaking rate
        
        # Store the shared state dictionary (contains 'voice_active' and 'lock')
        self.state = shared_state
        # Store the thread lock from the shared state
        self.lock = shared_state['lock']
        
        # Create a thread-safe Queue.
        # The main thread will 'put' messages in here (non-blocking).
        # This voice thread will 'get' messages from here (blocking).
        self.speak_queue = queue.Queue()

    def speak(self, text):
        """
        Queues text to be spoken. This function is NON-BLOCKING.
        The main thread calls this, and it returns instantly,
        so the camera feed never freezes.
        """
        print(f"Assistant (Queued): {text}")
        # 'put' is thread-safe and adds the message to the queue
        self.speak_queue.put(text)

    def _listen_once(self, timeout=4, phrase_time_limit=5):
        """
        Listens for a single command. This function IS BLOCKING.
        It's designed to block the background voice thread, not the main thread.
        
        Returns:
            The recognized command as a string, or an empty string if it fails.
        """
        try:
            # Open the microphone
            with sr.Microphone() as source:
                # Adjust for ambient noise to improve accuracy
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print(" Listening for command...")
                # Listen for audio
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            
            # Use Google's Speech Recognition to convert audio to text
            command = self.recognizer.recognize_google(audio, language="en-in").lower()
            print(f" You said: {command}")
            return command
        
        # Handle cases where no speech was heard
        except sr.WaitTimeoutError:
            return ""
        # Handle cases where speech was unintelligible
        except sr.UnknownValueError:
            return ""
        # Handle any other exceptions (e.g., no internet connection)
        except Exception as e:
            print(f"Voice recognition error: {e}")
            return ""

    # --- Private Helper Functions for Executing Commands ---

    def _open_app(self, app_name):
        """Internal function to open an application from the config list."""
        path = config.APPS.get(app_name)
        if path:
            self.speak(f"Opening {app_name}") # Queue the feedback
            try:
                # 'start ms-settings:' is a shell command, not a file
                if path.startswith("start "):
                    os.system(path)
                # 'os.startfile' is for .exe files, documents, etc.
                else:
                    os.startfile(path)
            except Exception as e:
                self.speak(f"Failed to open {app_name}")
                print(f"Open error: {e}")
        else:
            self.speak(f"I don’t know how to open {app_name}")

    def _close_app(self, app_name):
        """Internal function to find and kill a running process by name."""
        # Special case for Windows Explorer
        if app_name == "explorer":
            os.system("taskkill /f /im explorer.exe")
            self.speak("Explorer closed.")
            return

        # Iterate over all running processes
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                # Get the process name
                proc_name = (proc.info['name'] or "").lower()
                # Check if our app_name is in the process name
                if app_name.lower() in proc_name or f"{app_name}.exe" in proc_name:
                    self.speak(f"Closing {app_name}")
                    proc.kill() # Terminate the process
                    return
            except Exception:
                # Ignore errors (e.g., process died before we could kill it)
                continue
        # If the loop finishes, no process was found
        self.speak(f"{app_name} is not running.")

    def _system_action(self, command):
        """Internal function to perform system actions like volume or hotkeys."""
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
        return True # Command was handled

    def _execute_command(self, command):
        """
        The main command "router".
        It parses the command string and decides which action to take.
        """
        if not command:
            return

        # --- 1. Check for App Commands (Open/Close) ---
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

        # --- 2. Check for Web/Info Commands ---
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

        # --- 3. Check for Mouse/Scroll Commands ---
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

        # --- 4. Fallback to System Actions ---
        # If no other command matched, see if it's a system action
        if not self._system_action(command):
            # Optional: Add a "command not understood" fallback
            pass

    def _voice_listener_loop(self):
        """
        THE CORE LOOP for the background voice thread.
        This loop has two jobs, prioritized in order:
        1. (High Priority) Check the speak_queue and say any pending messages.
        2. (Low Priority) If not speaking, check if 'voice_active' is True
           and listen for a new command.
        """
        # Queue the initial startup message
        self.speak("Voice assistant thread started.") 
        
        while True:
            # --- 1. Check Speak Queue (Highest Priority) ---
            try:
                # Check for a message *without* blocking (block=False)
                text_to_speak = self.speak_queue.get(block=False)
                
                # If we get one, speak it.
                # This *is* blocking (engine.runAndWait()), but it only
                # blocks this background thread, NOT the main camera thread.
                print(f"Assistant (Speaking): {text_to_speak}")
                with self.lock: # Use the lock to access the TTS engine
                    try:
                        self.engine.say(text_to_speak)
                        self.engine.runAndWait()
                    except Exception as e:
                        # Catch TTS errors
                        print(f"Pyttsx3 error: {e}")
                
                # Mark the queue task as done
                self.speak_queue.task_done()
                # Loop back to check the queue again immediately
                continue 
            
            except queue.Empty:
                # This is the normal case: No speech is queued.
                # We can now proceed to listening.
                pass 

            # --- 2. Check for Listening (Lower Priority) ---
            # Check the shared 'voice_active' flag in a thread-safe way
            with self.lock:
                active = self.state['voice_active']
            
            # If voice mode is not active, sleep briefly to save CPU
            if not active:
                time.sleep(0.1)
                continue
            
            # If active, listen for a command (this blocks this thread)
            command = self._listen_once(timeout=4, phrase_time_limit=4)
            
            # If we heard a command
            if command:
                cmd = command.lower()
                
                # --- Handle Special "Meta" Commands ---
                if "exit voice" in cmd or "stop listening" in cmd:
                    # Deactivate voice mode (thread-safe)
                    with self.lock:
                        self.state['voice_active'] = False
                    self.speak("Voice mode deactivated.")
                
                elif "quit assistant" in cmd or "shutdown assistant" in cmd:
                    self.speak("Shutting down assistant.")
                    # Give the assistant time to speak before exiting
                    time.sleep(2)
                    # os._exit(0) is a "hard exit" that stops the entire program
                    os._exit(0)
                
                # --- Handle Normal Commands ---
                else:
                    self._execute_command(cmd)
            else:
                # No command was heard (timeout, mumble, etc.)
                # Sleep briefly before looping back
                time.sleep(0.05)

    def start_listener_thread(self):
        """
        Starts the background voice listener loop.
        This is the *only* function in this class that main.py calls.
        """
        # Create a new thread targeting our '_voice_listener_loop' function
        # daemon=True: This ensures the thread will automatically
        # close when the main program (main.py) exits.
        t = threading.Thread(target=self._voice_listener_loop, daemon=True)
        t.start()