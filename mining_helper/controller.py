from pynput.mouse import Controller, Button

mouse = Controller()

def release_left_click():
    """Simulate left mouse button release."""
    mouse.release(Button.left)