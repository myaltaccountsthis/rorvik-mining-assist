import time
import json
import threading
import numpy as np
import mss
import cv2
import pyautogui
from pynput import mouse
from controller import release_left_click
from config_manager import load_settings

ROI_CONFIG = "roi_config.json"

class Detector:
    def __init__(self, log_func=print, continuous=False):
        self.log = log_func
        self.continuous = continuous
        self.running = False
        self.settings = load_settings()

        self.mouse_pressed = False
        self.stop_requested = False
        self.mining_thread_active = False

        self.listener = mouse.Listener(on_click=self.on_click)
        self.listener.start()
        self.load_roi()

    def load_roi(self):
        try:
            with open(ROI_CONFIG, 'r') as f:
                self.roi = json.load(f)
        except Exception as e:
            self.log(f"[ERROR] Failed to load ROI config: {e}")
            self.roi = {"x": 500, "y": 500, "width": 200, "height": 50}

    def on_click(self, x, y, button, pressed):
        if button == mouse.Button.left:
            self.mouse_pressed = pressed
            if pressed and not self.mining_thread_active:
                threading.Thread(target=self.handle_mouse_hold, daemon=True).start()

    def handle_mouse_hold(self):
        if self.mining_thread_active:
            return
        self.mining_thread_active = True

        time.sleep(self.settings["DEFAULT_DELAY"])
        if not self.mouse_pressed or self.stop_requested:
            self.mining_thread_active = False
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

            dot_ratio = self.gray_ratio(gray, self.settings["DOT_GRAY"])
            fill_ratio = self.gray_ratio(gray, self.settings["FILL_GRAY"])
            crit_ratio = self.gray_ratio(gray, self.settings["CRITICAL_GRAY"])

            # self.log(f"[DEBUG] GrayMatch % — Dot: {dot_ratio:.2%}, Fill: {fill_ratio:.2%}, Critical: {crit_ratio:.2%}")

            if crit_ratio > max_crit_ratio:
                max_crit_ratio = crit_ratio

            if dot_ratio > 0.01 and fill_ratio > 0.01:
                drop_from_peak = max_crit_ratio - crit_ratio
                if drop_from_peak >= 0.005 and max_crit_ratio > 0.01 and not triggered:
                    self.log(f"[ACTION] Critical drop from peak: {max_crit_ratio:.2%} → {crit_ratio:.2%}")
                    release_left_click()
                    triggered = True
                    break

            if time.time() - start_time > self.settings["RESET_TIMEOUT"]:
                self.log("[INFO] Timeout: no critical zone triggered.")
                self.mining_thread_active = False
                return

            time.sleep(self.settings["POLL_INTERVAL"])

        if self.continuous and not self.stop_requested:
            self.monitor_for_next_ore()
        else:
            self.mining_thread_active = False

    def monitor_for_next_ore(self):
        attempts = 0

        while not self.stop_requested and attempts < self.settings["MAX_REENGAGE_ATTEMPTS"]:
            time.sleep(self.settings["RECHECK_GRACE_PERIOD"])
            self.log("[INFO] Re-engaging for continuous mining...")
            pyautogui.mouseDown()
            self.mouse_pressed = True

            frame = self.capture_roi()
            if frame is None:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            fill_ratio = self.gray_ratio(gray, self.settings["FILL_GRAY"])
            crit_ratio = self.gray_ratio(gray, self.settings["CRITICAL_GRAY"])

            # self.log(f"[DEBUG] Re-check ratios — Fill: {fill_ratio:.2%}, Critical: {crit_ratio:.2%}")

            if fill_ratio > 0.01 and crit_ratio > 0.01:
                self.log("[INFO] Bar detected. Continuing mining.")
                self.mining_thread_active = False
                threading.Thread(target=self.handle_mouse_hold, daemon=True).start()
                return
            else:
                self.log("[INFO] No valid bar detected. Rechecking...")
                attempts += 1

        pyautogui.mouseUp()
        self.mouse_pressed = False
        self.log("[INFO] Max attempts reached. Giving up re-engagement.")
        self.mining_thread_active = False

    def capture_roi(self):
        try:
            x, y, w, h = self.roi['x'], self.roi['y'], self.roi['width'], self.roi['height']
            with mss.mss() as sct:
                monitor = {"top": y, "left": x, "width": w, "height": h}
                sct_img = sct.grab(monitor)
                frame = np.array(sct_img)[:, :, :3]
                return frame
        except Exception as e:
            self.log(f"[ERROR] Failed to capture ROI: {e}")
            return None

    def gray_ratio(self, gray_img, target, tolerance=None):
        if tolerance is None:
            tolerance = self.settings["TOLERANCE"]
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
        pyautogui.mouseUp()
        self.mouse_pressed = False
        self.mining_thread_active = False
        self.log("[INFO] Detector listener stopped.")
