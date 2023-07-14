from tkinter import Tk, Button

def on_button_click():
    print("Button clicked!")

root = Tk()

button = Button(root, text="Click me!", command=on_button_click)
button.pack()

root.mainloop()