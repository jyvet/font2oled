#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Font to OLED screen (font2oled)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Convert a font to a hexadecimal array for OLED screens.
Usage:
   >>> python font2oled.py <fontfile>

The script outputs a C declaration of a static array. Code output may be easily
included in source code managed by the Arduino IDE.

See full documentation in README.md
:copyright: (c) 2015 by Jean-Yves VET.
:license: MIT, see LICENSE for more details.
"""

from __future__ import print_function
import sys, re, os
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw


############################### Global Variables ###############################
nbCharacters = 256
minFontSize  = 4
maxFontSize  = 13


################################## Functions ###################################

## Find the proper font size to fit characters in a 8x8 pixels square.
# @param  fontName Path to the Font to use
# @return An image object containing font characters
def findSize(fontname):
    fontSize = maxFontSize
    oversized = True

    while (oversized) :
        oversized = False
        if (fontSize < minFontSize) :
            print("Error: an error happened while using the font", file=sys.stderr)
            exit(-1)

        # Initialize font
        fontSize -= 1
        font = ImageFont.truetype(fontname, fontSize)
        im = Image.new("1", (10,8*nbCharacters), (0,0,0))
        draw = ImageDraw.Draw(im)

        for i in range(nbCharacters):
            # Clear character
            for j in range (8) :
                for pixel in range (8) :
                    im.putpixel((j, i*8 + pixel), 0)

            # Draw character
            draw.text((0, i*8), str(unichr(i).encode('latin-1', 'replace')),
                (255,255,255),font=font)

            # Check if still oversized
            if (i>=0 and i<=128) :
                for pixel in range (8) :
                    if (im.getpixel((8, i*8 + pixel)) == 255) :
                        oversized = True
                        break

    draw = ImageDraw.Draw(im)
    return im


## Shift a character for horizontal alignement.
# @param  im      Image containing all characters
# @param  i       Index of the character to shift
# @param  stride  Number of pixels we need to shift the character
# @return An image object containing font characters
def shiftRight(im, i, stride):
    for j in range(7, -1, -1):
        if (j-stride >= 0) :
                for pixel in range(8):
                    im.putpixel((j, i*8 + pixel),
                        im.getpixel((j-stride, i*8 + pixel)))
        else :
            for pixel in range(8):
                im.putpixel((j, i*8 + pixel), 0)


## Check each characters if thez need to be centered.
# @param  im      Image containing all characters
# @return An image object containing font characters if nothing went wrong
def centerChar(im):
    for i in range(nbCharacters):
        wsize = 0

        # Do not center horizontally punctuations signs [!,.:;?]
        if (i!=33 and i!=44 and i!=46 and i!=58 and i!=59 and i!=63):
            for j in range(8):
                pixels = 0
                for pixel in range(8):
                    if (im.getpixel((j, i*8 + pixel)) == 255):
                        pixels += 1
                if (pixels != 0):
                    wsize += 1

            # Find strides
            spaces = (8-wsize)/2
            shiftRight(im, i, spaces)


## Check arguments and font file.
# @return An image object containing font characters if nothing went wrong
def checkArgs():
    # Check number of arguments
    if len(sys.argv) == 2:
        # Try to open the image
        try:
            font = ImageFont.truetype(sys.argv[1], 8)
        except:
            print("Error: unable to load Font", sys.argv[1], file=sys.stderr)
            exit(-1)

        # Generate image
        im = findSize(sys.argv[1])
        centerChar(im)
        im.save("font.png")

        return im
    else :
        print("Error: invalid number of arguments", file=sys.stderr)
        print("Usage:")
        print("python " + sys.argv[0] + " <fontfile>")
        exit(-1)


## Convert pixel values to bytes for OLED screens. In the same column, values in
#  consecutive rows (8 by 8) are aggregated in the same byte.
# @param pixels   Array containing pixel values
# @return An array containing the converted values
def convert(pixels) :
    data = [[0 for x in range(nbCharacters)] for x in range(8)]

    for i in range(8):
        for j in range(nbCharacters):
            for bit in range(8):
                data[i][j] |= (pixels[i][j*8 + bit] << bit)
    return data


## Convert image to binary (monochrome).
# @param im   A picture opened with PIL.
# @return A binary array
def toBinary(im):
    # Convert image to monochrome if necessary
    if (im.mode != "1"):
        im.convert("1")

    # Allocate array to hold binary values
    binary = [[0 for x in range(nbCharacters*8)] for x in range(8)]

    # Convert to binary values by using threshold
    for j in range(nbCharacters*8):
        for i in range(8):
            value = im.getpixel((i, j))
            # Set bit if the pixel contrast is below the threshold value
            binary[i][j] = int(value == 255)

    return binary


## Format data to output a string for C array declaration.
# @param data   Array containing binary values
# @return A string containing the array formated for C code.
def output(data):
    # Retrieve filename without the extension
    filename = os.path.basename(sys.argv[1])
    filename = os.path.splitext(filename)[0]
    filename = re.sub('[ -:,\?]', '', filename)

    # Generate the output with hexadecimal values
    s = "const char " + filename + "[][8] PROGMEM = {" + '\n'
    for j in range(nbCharacters):
        s+= "{"
        for i in range(8):
            s += format(data[i][j], '#04x')
            if (i%8 == 7):
                s += "}," + '\n'
            else:
                s += ", "
    s = s[:-2] + '\n};'

    return s


#################################### Main ######################################

if __name__ == '__main__':
    image = checkArgs()

    binary = toBinary(image)
    data = convert(binary)
    print(output(data))
