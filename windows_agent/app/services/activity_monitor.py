
import time
import threading
from pynput import mouse, keyboard
import logging

logger = logging.getLogger("activity_monitor")

class ActivityMonitor:
    def __init__(self, on_activity_detected, idle_threshold_seconds=60):
        self._on_activity_detected = on_activity_detected
        self.idle_threshold = idle_threshold_seconds
        self.last_activity = time.time()
        self.is_idle = True # Start as idle to trigger on first activity
        
        self._stop_event = threading.Event()
        self._mouse_listener = None
        self._keyboard_listener = None
        self._check_thread = None

    def start(self):
        logger.info("Starting Activity Monitor...")
        self._stop_event.clear()
        
        # Setup listeners
        self._mouse_listener = mouse.Listener(
            on_move=self._on_input,
            on_click=self._on_input,
            on_scroll=self._on_input
        )
        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_input,
            on_release=self._on_input
        )
        
        self._mouse_listener.start()
        self._keyboard_listener.start()
        
        # Start background checker for idle state
        self._check_thread = threading.Thread(target=self._check_idle_loop, daemon=True)
        self._check_thread.start()

    def stop(self):
        logger.info("Stopping Activity Monitor...")
        self._stop_event.set()
        if self._mouse_listener:
            self._mouse_listener.stop()
        if self._keyboard_listener:
            self._keyboard_listener.stop()
        if self._check_thread:
            self._check_thread.join()

    def _on_input(self, *args):
        now = time.time()
        
        # If we were IDLE, and now we have input -> Transition to ACTIVE and Alert
        if self.is_idle:
            self.is_idle = False
            logger.info("User activity detected (transition from IDLE)")
            try:
                self._on_activity_detected()
            except Exception as e:
                logger.error(f"Error in activity callback: {e}")
        
        self.last_activity = now

    def _check_idle_loop(self):
        while not self._stop_event.is_set():
            time.sleep(5)
            now = time.time()
            if not self.is_idle and (now - self.last_activity > self.idle_threshold):
                self.is_idle = True
                logger.info(f"System considered IDLE (No activity for {self.idle_threshold}s)")
