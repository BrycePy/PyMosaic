from PIL import Image
import json
import random
from multiprocessing import Pool, cpu_count
import tqdm
import settings
import os
import calculate_tile

def generate_row(pipe_in):
    image_raw, tile_data, tile_directory = pipe_in
    tile_colors = tile_data.get("tiles")
    TWIDTH = tile_data.get("w")

    output_w = TWIDTH * image_raw.width
    output_h = TWIDTH

    pixel_reference = image_raw.convert("RGB")
    frame_buffer = Image.new("RGB", (output_w, output_h))

    used = set()

    def calculate_error(color1, color2):
        if not color1: return 999999999
        r_diff = abs(color1[0] - color2[0])
        g_diff = abs(color1[1] - color2[1])
        b_diff = abs(color1[2] - color2[2])
        w_diff = (r_diff + g_diff + b_diff)
        error = r_diff**2 + g_diff**2 + b_diff**2 + w_diff**2
        return error

    def get_nearest_color(target_color):
        if (settings.AVOID_ROW_DUPE): 
            colors = [(calculate_error(tile_colors[tile], target_color), tile) for tile in tile_colors if tile not in used]
        else:
            colors = [(calculate_error(tile_colors[tile], target_color), tile) for tile in tile_colors]
        best = min(colors)
        boundary = max(settings.NOISE_LEVEL, best[0]*2)
        colors = [x for x in colors if x[0] <= boundary]
        tile = random.choice(colors)[1]
        used.add(tile)
        return tile

    random_order = list(range(pixel_reference.width))
    random.shuffle(random_order)
    for x in random_order:
        target_color = pixel_reference.getpixel((x, 0))
        tile_name = get_nearest_color(target_color)
        paste_position = (x*TWIDTH, 0)
        tile_path = os.path.join(tile_directory, tile_name)
        tile = Image.open(tile_path)
        frame_buffer.paste(tile, paste_position)
    frame_buffer.resize((output_w, output_h))
    return frame_buffer, used

def render(input_file, n, tile_directory, output_file="output.jpeg"):
    color_data_path = os.path.join(tile_directory, "tiles_data.json")
    if not(os.path.isdir(tile_directory)) or not(os.path.isfile(color_data_path)):
        print("generating tiles...")
        tile_data = calculate_tile.main()
        tile_width = tile_data.get("w")

    with open(color_data_path, "r") as f:
        tile_data = json.load(f)
        tile_width = tile_data.get("w")

    if tile_width != settings.TILE_WIDTH:
        print("generating tiles...")
        tile_data = calculate_tile.main()
        tile_width = tile_data.get("w")

    image_raw = Image.open(input_file)

    if image_raw.width > image_raw.height:
        lr_w, lr_h = n, int(n*(image_raw.height/image_raw.width))
    else:
        lr_w, lr_h = int(n*(image_raw.width/image_raw.height)), n

    pixel_reference = image_raw.resize((lr_w, lr_h)).convert("RGB")


    works = []
    for i in range(pixel_reference.height-1):
        strip = pixel_reference.crop((0, i, pixel_reference.width, i+1))
        works.append((strip, tile_data, tile_directory))

    print("rendering rows....")
    pool = Pool(cpu_count())
    strips = tqdm.tqdm(pool.imap(generate_row, works), total=len(works))
    strips = list(strips)
    output_w = lr_w * tile_width
    output_h = lr_h * tile_width
    frame_buffer = Image.new("RGB", (output_w, output_h))

    print("combining rows....")
    used_tiles = []
    for i, result in tqdm.tqdm(enumerate(strips), total=len(strips)):
        strip, used = result
        frame_buffer.paste(strip, (int((i%2/2-0.25)*tile_width), i*tile_width))
        used_tiles.extend(list(used))
    
    used_tiles = set(used_tiles)
    print(len(used_tiles), "unique tile used.")
    print("saving to file....")

    frame_buffer.save(output_file, optimize=settings.OUTPUT_OPTIMIZE)

if __name__ == '__main__':
    render( settings.INPUT_FILE,
            settings.MAX_TILES, 
            settings.TILES_DIRECTORY+"_temp", 
            settings.OUTPUT_FILE)