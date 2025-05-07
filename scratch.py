from pynput import keyboard
import threading
import time

paused = False
lock = threading.Lock()

def on_press(key):
    global paused
    print(f"Key {key} pressed")
    if key == keyboard.Key.space:
        with lock:
            paused = not paused
            print("Paused" if paused else "Resumed")

# Start the listener
listener = keyboard.Listener(on_press=on_press)
listener.start()

while True:
    with lock:
        if not paused:
            print("Running...")
    time.sleep(5)
