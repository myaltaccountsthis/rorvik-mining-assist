from pynput import mouse, keyboard
from config_manager import load_settings, update_settings

mouse_controller = mouse.Controller()
keyboard_controller = keyboard.Controller()

def release_left_click():
    """Simulate left mouse button release."""
    mouse_controller.release(mouse.Button.left)

"""
PRETTY MUCH UNUSED NOW, BUT LEFT HERE BECAUSE IT MIGHT BE USEFUL LATER
ALL IT DOES IS RELEASE THE LEFT MOUSE BUTTON LOL
"""

remap_active = False
on_remap_complete = lambda: 0
on_keybind_pressed = lambda: 0
keybind = load_settings()['KEYBIND']

def on_mouse_click(x, y, button, pressed):
    global remap_active, keybind
    if pressed:
        if remap_active:
            keybind = str(button)
            update_settings({'KEYBIND': keybind})
            print(f"Keybind is now {keybind}")
            remap_active = False
            on_remap_complete()

        elif keybind == str(button):
            on_keybind_pressed()
            
def on_keyboard_press(key):
    global remap_active, keybind
    if remap_active:
        keybind = str(key)
        if keybind == "Key.esc":
            keybind = "None"
        update_settings({'KEYBIND': keybind})
        print(f"Keybind is now {keybind}")
        remap_active = False
        on_remap_complete()

    elif keybind == str(key):
        on_keybind_pressed()

def bind_remap(callback, keybind_callback):
    global on_remap_complete, on_keybind_pressed
    on_remap_complete = callback
    on_keybind_pressed = keybind_callback

def enable_remap():
    global remap_active
    remap_active = True

def get_keybind():
    return keybind

mouse_listener = mouse.Listener(on_click=on_mouse_click)
keyboard_listener = keyboard.Listener(on_press=on_keyboard_press)

mouse_listener.start()
keyboard_listener.start()