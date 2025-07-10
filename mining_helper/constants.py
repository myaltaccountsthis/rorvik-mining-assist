DEFAULT_SETTINGS = {
    "DEFAULT_DELAY": 0.2, # Initial delay before starting the mining process
    "POLL_INTERVAL": 0.01, # How often we check the ROI for changes, decresase if dot passes the critical zone constantly
    "RESET_TIMEOUT": 3.0, # Timeout for re-engaging the mining process if no critical zone is detected
    "RECHECK_GRACE_PERIOD": 0.18, # Time to wait after re-engaging before checking for critical zone again. Tricky value, increase/decrease if you hit every othger critical zone in an alternating pattern
    "MAX_REENGAGE_ATTEMPTS": 3, # Maximum attempts to re-engage mining after a critical zone is detected, do not make this too high, otherwise you might get stuck in a loop
    "DOT_GRAY": 146, # Gray value for the dot in the ROI, don't change
    "FILL_GRAY": 37, # Gray value for the fill in the ROI, don't change
    "CRITICAL_GRAY": 228, # Gray value for the critical zone in the ROI, don't change
    "TOLERANCE": 10 # Tolerance for gray value matching, increase if you have issues with gray values not matching correctly, might increase false positives if you change for some reason. Shouldn't need to be changed.
}
