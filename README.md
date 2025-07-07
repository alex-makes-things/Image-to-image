# Image-to-image
This is my newest Image conversion tool, which is meant to replace and retire [Image-to-LCD](https://github.com/alex-makes-things/Image-to-LCD).

This tool is mainly meant for use on a microcontroller with a filesystem. I will probably be publishing reader libraries, but for now if you want to use these files you can make your own parser, which given the simplicity of the format, it's not a hard task.





## Why did I make this format?

I decided to create this custom format out of stress, I am developing an ESP32-targeted fast UI graphics library ([esp32-ui](https://github.com/alex-makes-things/esp32-ui)), and I found myself stressing about the fact that there is no easy way to store images and use them seamlessly with other libraries.

- "Damn I just want the data, why is this so complicated?!??!"


## Features
- GUI-based using Tkinter.
- Conversion of PIL-compatible image formats to .image.
- Visualization of .image files.
- "Open with" windows feature support for visualization of .image files (multiple files at once supported).
- Currently supports conversion to monochrome or RGB565.



## How the format is laid out

|   Address    |        Information       |    Type    |
| ------------ | -------------------------|------------|
| 0x0          | Width                    | uint16_t   |
| 0x2          | Height                   | uint16_t   |
| 0x4          | Bits per pixel           | uint8_t    |
| 0x5          | First byte of pixel array

You can get the colorspace from the bits per pixel:

|Bits per pixel|  Colorspace  |
| ------------ | -------------|
| 1            | Monochrome   |
| 16           | RGB565       |
| Etc...

#### IMPORTANT NOTE: 
#### Pixel bytes are little endian and the monochrome colorspace packs the pixels in bytes, meaning each byte contains 8 pixels, with the first pixel being on the left, padding is added to the last byte to complete the 8 bits.

Each pixel is placed sequentially in the array, without endline blocks, so it is your job to iterate correctly through the array using the width and height values accordingly.

## Installation

There are 2 ways to run the converter the first one is cloning the repository, and running the script directly, and the second one is downloading the latest release executable.

If you want to run the actual script, you're gonna need to have Python installed on your system along with these dependencies:
 - Pillow
 - Screeninfo
 - Tkinter (if you didn't install it with python)

To install these dependencies just run the following commands in your command prompt:

```
pip install Pillow
```
```
pip install screeninfo
```
And if you haven't installed Tkinter bundled with Python:
```
pip install tk
```

A reason that might make you want to install the executable is that I've baked in functionality for Windows' "Open with" file explorer feature, which lets you visualize .image files.

    
## Supported Platforms

- Windows

Currently, the converter only supports windows, that is because I don't have access to devices with other OSs installed I can develop and test on. For now, I won't be adding support for MacOS and Linux, but you're free to create a pull request to add support if you're interested in doing so.

