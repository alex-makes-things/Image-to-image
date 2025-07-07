from PIL import Image, ImageTk
import threading
import struct
import numpy as np
from time import sleep
from tkinter import Tk, Frame, Button, Label,StringVar,ttk,Toplevel,IntVar,Checkbutton
from tkinter import filedialog
import tkinter.font as tkFont
import sys
import screeninfo
import os

import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)  # PER_MONITOR_AWARE
except:
    try:
        ctypes.windll.user32.SetProcessDPIAware()  # fallback for older Windows
    except:
        pass

colorspaceDict = {1: "Mono", 16 : "RGB565"}
screen1 = screeninfo.get_monitors()[0]
global window
open_previews = []

def generateImageArray(path):
    with open(path, "rb") as f:
        header = f.read(5)
        width, height, bpp = struct.unpack("<HHB", header)
        

        if bpp == 16:
            pixel_data = f.read(width * height * 2)
            pixels = np.frombuffer(pixel_data, dtype=np.uint16).reshape((height, width))

            # Convert RGB565 to RGB888
            def rgb565_to_rgb888(val):
                r = (val >> 11) & 0x1F
                g = (val >> 5) & 0x3F
                b = val & 0x1F
                return (
                    int(r * 255 / 31),
                    int(g * 255 / 63),
                    int(b * 255 / 31)
                )

            img_array = np.zeros((height, width, 3), dtype=np.uint8)
            for y in range(height):
                for x in range(width):
                    img_array[y, x] = rgb565_to_rgb888(pixels[y, x])

        elif bpp == 1:
            bytes_per_row = (width + 7) // 8
            total_bytes = bytes_per_row * height
            pixel_data = f.read(total_bytes)

            # Convert packed bits to pixel values
            img_array = np.zeros((height, width), dtype=np.uint8)
            byte_index = 0
            for y in range(height):
                for x in range(width):
                    if x % 8 == 0:
                        current_byte = pixel_data[byte_index]
                        byte_index += 1
                    bit = (current_byte >> (7 - (x % 8))) & 1
                    img_array[y, x] = 255 if bit else 0

            # Convert to 3-channel RGB for display
            img_array = np.stack([img_array]*3, axis=-1)  # grayscale → RGB

        else:
            raise ValueError(f"Unsupported color depth: {bpp} bpp")

        return Image.fromarray(img_array, "RGB"), bpp
def pack_mono_row(row):
    packed = bytearray()
    byte = 0
    bit_index = 0
    for i, bit in enumerate(row):
        if bit:  # pixel is "on" → 1
            byte |= (1 << (7 - bit_index))
        bit_index += 1
        if bit_index == 8:
            packed.append(byte)
            byte = 0
            bit_index = 0
    if bit_index > 0:
        packed.append(byte)  # Add remaining bits (padded with 0)
    return packed
def bmp_to_image(input_bmp, colorspace="RGB565"):
    image = Image.open(input_bmp).convert("RGB")
    width, height = image.size
    pixels = image.load()
    output_raw = (input_bmp.split(".")[0]+".image")

    if(colorspace=="RGB565"):
        with open(output_raw, "wb") as f:
            #  Write custom header
            f.write(struct.pack("<HHB", width, height, 16))
            #print(f'Width: {width}\nHeight: {height}\nBits per pixel: {16}')
            #  Write RGB565 pixel data

            for y in range(height):
                for x in range(width):
                    r, g, b = pixels[x, y]
                    rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                    f.write(struct.pack("<H", rgb565))

    if(colorspace == "MONO"):
        with open(output_raw, "wb") as f:
            #  Write custom header
            f.write(struct.pack("<HHB", width, height, 1))
            #print(f'Width: {width}\nHeight: {height}\nBits per pixel: {1}')
            for y in range(height):
                row_bits = []
                for x in range(width):
                    r, g, b = pixels[x, y]
                    # Convert to grayscale brightness
                    gray = (r + g + b) // 3
                    row_bits.append(1 if gray > 127 else 0)
                
                packed_row = pack_mono_row(row_bits)
                f.write(packed_row)

def make_draggable(win):
    def start_move(event):
        # Record the offset between mouse pointer and window top-left corner
        win._drag_start_x = event.x_root - win.winfo_x()
        win._drag_start_y = event.y_root - win.winfo_y()

    def do_move(event):
        x = event.x_root - win._drag_start_x
        y = event.y_root - win._drag_start_y
        win.geometry(f"+{x}+{y}")

    win.bind("<ButtonPress-1>", start_move)
    win.bind("<B1-Motion>", do_move)
def scale_to_fit(image, max_width=800, max_height=600):
    scale = min(max_width / image.width, max_height / image.height, 7.0)
    new_size = (int(image.width * scale), int(image.height * scale))
    return image.resize(new_size, Image.NEAREST)
def preview_image(image, bpp, index=0, isOpenWith=False):
    # Resize the image
    scaled_img = scale_to_fit(image)
    w, h = scaled_img.size
    #global preview
    
    

    preview = Toplevel()
    preview.title(f'W: {image.width} H:{image.height} BPP: {colorspaceDict[bpp]}')
    preview.iconbitmap(replacePathWith("paint_brush.ico"))
    preview.resizable(True, True)
    
    if(isOpenWith):
        def on_close():
    # Remove this preview window from the global list
            if preview in open_previews:
                open_previews.remove(preview)
            preview.destroy()
            # If no previews left and running in "Open with" mode, destroy root
            if len(open_previews) == 0 and len(sys.argv) > 1:
                window.destroy()
        x = int(screen1.width/2 - (w/2)-25)
        y = int(screen1.height/2 - (h/2)-25)
        preview.protocol("WM_DELETE_WINDOW", on_close)
        preview.bind("<Escape>", lambda e: on_close())
    else:
        x = window.winfo_rootx()
        y = window.winfo_rooty()
        preview.bind("<Escape>", lambda e: preview.destroy())
    preview.geometry(f"{w+5}x{h+5}+{x+25*(index)}+{y+25*(index)}")

    tk_img = ImageTk.PhotoImage(scaled_img)
    label = Label(preview, image=tk_img)
    label.image = tk_img  # prevent GC
    label.config(bd=0,highlightbackground="#3c3c3c", highlightthickness=5)
    label.pack()
    
    make_draggable(preview)
    preview.focus_force()
    open_previews.append(preview)

def view_image(path):
    image, bpp = generateImageArray(path)
    preview_image(image, bpp)
def convert_and_preview(image, root, bpp):
    root.after(0, lambda: preview_image(image, bpp))
def getFileName(path):
    data = path.split("/")
    name = data[len(data)-1]
    return name

def openFile():
    filename = filedialog.askopenfilename()
    selected_path.set(filename)
    if(filename!=""):
        selection.config(text=f'"{getFileName(filename)}" selected.')
    else:
        selection.config(text="Select your image...")
def convert():
    try:
        bmp_to_image(selected_path.get(), n.get())
        try:
            open_previews[0].destroy()
        except:
            pass
        if(showPreview.get()):
                view_image((selected_path.get().split(".")[0]+".image"))
    except:
        print("Invalid path / Null selection")
def remove_focus(event):
    event.widget.master.focus_set()  # Move focus to parent, or any other widget




def replacePathWith(file):
    path = __file__
    split = path.split("\\")
    split.pop()
    split.append(file)
    newpath = ""
    for word in split:
        newpath = newpath + word
        if(word != file):
            newpath = newpath + "/"
    return newpath


if len(sys.argv) > 1:  #If opened with "Open with"
    # Create a root Tk instance (hidden)
    window = Tk()
    window.tk.call('tk', 'scaling', 1.50)
    window.iconbitmap(replacePathWith("paint_brush.ico"))
    window.withdraw()
    helv16 = tkFont.Font(family='Helvetica', size=16, weight=tkFont.BOLD)
    helv8 = tkFont.Font(family='Helvetica', size=8, weight=tkFont.BOLD)

    filepaths = sys.argv[1:]
    for i, filepath in enumerate(filepaths):
        image, bpp = generateImageArray(filepath)
        preview_image(image, bpp, i, True)


    window.mainloop()
else:
    window = Tk()
    w = 380
    h = 320
    x = int(screen1.width/2 - (w/2))
    y = int(screen1.height/2 - (h/2))
    window.geometry(f'{w}x{h}+{x}+{y}')
    window.title("Image to .image")
    window.iconbitmap(replacePathWith("paint_brush.ico"))

    window.resizable(False, False)
    window.config(background="#1c1c1c",)
    window.tk.call('tk', 'scaling', 1.50)
    helv16 = tkFont.Font(family='Helvetica', size=16, weight=tkFont.BOLD)
    helv8 = tkFont.Font(family='Helvetica', size=8, weight=tkFont.BOLD)

    selected_path = StringVar(window, None)

    frame = Frame(window)
    frame.config(pady=15, background="#1c1c1c")
    frame.pack()

    labelText = StringVar(window)
    labelText.set("Test")

    n = StringVar()
    colorspaceSelection = ttk.Combobox(frame, width = 10, textvariable = n, state="readonly", takefocus=0)
    colorspaceSelection.bind("<<ComboboxSelected>>", remove_focus)
    colorspaceSelection['values'] = ('RGB565', 'MONO',)
    colorspaceSelection.grid(column=1, row=3)
    colorspaceSelection.current(0)

    button = Button(frame, text="Choose file", width= 20, height=2, borderwidth=5, font=helv16, command = openFile)
    button.config(bg='green')
    button.grid(column=1, pady=5, row=1)

    selection = Label(frame, text="Select your image...", font=("Arial", 10, ),fg="#ffffff", background="#1c1c1c")
    selection.grid(column=1, row=0)

    format = Label(frame, text="Select your desired format...", font=("Arial", 10, ),fg="#ffffff", background="#1c1c1c")
    format.grid(column=1, row=2)

    exitBTN = Button(frame, text="Convert", width= 20, height=2, borderwidth=5, font=helv16, command = convert)
    exitBTN.config(bg='#ff412b')
    exitBTN.grid(column=1, pady=(20,0), row=4)

    showPreview = IntVar(value=1)
    checkButton = Checkbutton(
        frame,
        text="Show preview",
        variable=showPreview,
        onvalue=1,
        offvalue=0,
        height=0,
        width=0,
        background="#1c1c1c",
        fg="#ffffff",
        font=("Arial", 10),
        selectcolor="#1c1c1c",
        activebackground="#1c1c1c",   # Prevent white highlight on press
        highlightthickness=0,          # Remove focus border
        activeforeground="#ffffff"
    )
    checkButton.grid(column=1, pady=0, row=5)

    window.mainloop()
