import time
import json
import threading
import numpy as np
import mss
import cv2
from pynput import mouse
from controller import release_left_click

CONFIG_FILE = "roi_config.json"
DEFAULT_DELAY = 0.4        # Increased delay to let bar fade in
POLL_INTERVAL = 0.001
RELEASE_DELAY = 0.02
RESET_TIMEOUT = 3.0

DOT_GRAY = 146
FILL_GRAY = 37
CRITICAL_GRAY = 228
TOLERANCE = 10


class Detector:
    def __init__(self, log_func=print):
        self.log = log_func
        self.running = False
        self.mouse_pressed = False
        self.stop_requested = False
        self.listener = mouse.Listener(on_click=self.on_click)
        self.listener.start()
        self.load_roi()

    def load_roi(self):
        try:
            with open(CONFIG_FILE, 'r') as f:
                self.roi = json.load(f)
        except Exception as e:
            self.log(f"[ERROR] Failed to load ROI config: {e}")
            self.roi = {"x": 500, "y": 500, "width": 200, "height": 50}

    def on_click(self, x, y, button, pressed):
        if button == mouse.Button.left:
            self.mouse_pressed = pressed
            if pressed:
                threading.Thread(target=self.handle_mouse_hold, daemon=True).start()

    def handle_mouse_hold(self):
        time.sleep(DEFAULT_DELAY)
        if not self.mouse_pressed or self.stop_requested:
            return
    
        self.log("[INFO] Left click detected. Starting ROI polling.")
        start_time = time.time()
        max_crit_ratio = 0.0
        triggered = False
    
        while self.mouse_pressed and not self.stop_requested:
            frame = self.capture_roi()
            if frame is None:
                continue
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
            dot_ratio = self.gray_ratio(gray, DOT_GRAY)
            fill_ratio = self.gray_ratio(gray, FILL_GRAY)
            crit_ratio = self.gray_ratio(gray, CRITICAL_GRAY)
    
            self.log(f"[DEBUG] GrayMatch % — Dot: {dot_ratio:.2%}, Fill: {fill_ratio:.2%}, Critical: {crit_ratio:.2%}")
    
            if crit_ratio > max_crit_ratio:
                max_crit_ratio = crit_ratio
    
            if dot_ratio > 0.01 and fill_ratio > 0.01:
                drop_from_peak = max_crit_ratio - crit_ratio
                if drop_from_peak >= 0.005 and max_crit_ratio > 0.01 and not triggered:
                    self.log(f"[ACTION] Critical drop from peak: {max_crit_ratio:.2%} → {crit_ratio:.2%}")
                    release_left_click()
                    triggered = True
                    return
    
            if time.time() - start_time > RESET_TIMEOUT:
                self.log("[INFO] Timeout: no critical zone triggered.")
                return
    
            time.sleep(POLL_INTERVAL)



    def capture_roi(self):
        try:
            x, y, w, h = self.roi['x'], self.roi['y'], self.roi['width'], self.roi['height']
            with mss.mss() as sct:
                monitor = {"top": y, "left": x, "width": w, "height": h}
                sct_img = sct.grab(monitor)
                frame = np.array(sct_img)[:, :, :3]  # Drop alpha
                return frame
        except Exception as e:
            self.log(f"[ERROR] Failed to capture ROI: {e}")
            return None

    def gray_ratio(self, gray_img, target, tolerance=TOLERANCE):
        mask = (gray_img >= (target - tolerance)) & (gray_img <= (target + tolerance))
        return np.count_nonzero(mask) / mask.size

    def run_forever(self):
        self.running = True
        self.log("[INFO] Detector armed. Holding for clicks...")
        try:
            while not self.stop_requested:
                time.sleep(0.1)
        except Exception as e:
            self.log(f"[ERROR] Detector exception: {e}")
        self.log("[INFO] Detector loop terminated.")

    def stop(self):
        self.stop_requested = True
        if self.listener:
            self.listener.stop()
        self.log("[INFO] Detector listener stopped.")
