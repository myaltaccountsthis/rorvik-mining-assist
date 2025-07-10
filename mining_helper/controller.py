from pynput.mouse import Controller, Button

mouse = Controller()

def release_left_click():
    """Simulate left mouse button release."""
    mouse.release(Button.left)

"""
PRETTY MUCH UNUSED NOW, BUT LEFT HERE BECAUSE IT MIGHT BE USEFUL LATER
ALL IT DOES IS RELEASE THE LEFT MOUSE BUTTON LOL
"""