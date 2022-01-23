from PIL import Image
import json
import random
import settings

with open("tiles_temp/tiles_data.json", "r") as f:
    tile_data = json.load(f)
    tile_colors = tile_data.get("tiles")

TWIDTH = tile_data.get("w")

image_raw = Image.open("142072949-288-k241713.jpg")

n = 400
if image_raw.width > image_raw.height:
    lr_w, lr_h = n, int(n*(image_raw.height/image_raw.width))
else:
    lr_w, lr_h = int(n*(image_raw.width/image_raw.height)), n

output_w = lr_w * TWIDTH
output_h = lr_h * TWIDTH

pixel_reference = image_raw.resize((lr_w, lr_h)).convert("RGB")
frame_buffer = Image.new("RGB", (output_w, output_h))

def calculate_error(color1, color2):
    if not color1: return 999999999
    r_diff = abs(color1[0] - color2[0])
    g_diff = abs(color1[1] - color2[1])
    b_diff = abs(color1[2] - color2[2])
    w_diff = (r_diff + g_diff + b_diff)
    error = r_diff**2 + g_diff**2 + b_diff**2 + w_diff**2
    return error

last_color = None
last_list = None
def get_nearest_color(target_color):
    global last_list, last_color
    if calculate_error(last_color, target_color) < 1000:
        r = (random.randint(0, random.randint(3, 10)))
        return last_list[r][1]
    test = [(calculate_error(tile_colors[tile], target_color), tile) for tile in tile_colors]
    test = sorted(test)
    last_list = test[:100]
    last_color = target_color
    r = (random.randint(0, random.randint(3, 10)))
    return test[r][1]

for x in range(pixel_reference.width):
    for y in range(pixel_reference.height):
        target_color = pixel_reference.getpixel((x, y))
        tile_path = get_nearest_color(target_color)
        paste_position = (x*TWIDTH, y*TWIDTH)
        tile = Image.open(tile_path)
        frame_buffer.paste(tile, paste_position)
    print(x)

frame_buffer_2 = Image.new("RGBA", (output_w, output_h))
mask = image_raw.convert("RGBA").split()[-1].resize((output_w, output_h))
frame_buffer_2.paste(frame_buffer, (0,0), mask)

frame_buffer_2.save("output.png")
