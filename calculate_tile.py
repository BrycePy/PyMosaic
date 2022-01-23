import json
from PIL import Image
import os
import json
from multiprocessing import Pool, cpu_count
import tqdm

TWIDTH = 120  # this is width and height of a tile

base_path = "tiles"
temp_path = "tiles_temp"


def get_average_color(pipe_in):
    i, image_path = pipe_in
    tile = Image.open(image_path)

    if tile.height > tile.width:
        half = (tile.height - tile.width) // 2
        tile = tile.crop((0, half, tile.width, half+tile.width))
    else:
        half = (tile.width - tile.height) // 2
        tile = tile.crop((half, 0, half+tile.height, tile.height))

    tile = tile.resize((TWIDTH, TWIDTH))
    tile = tile.convert("RGB")
    target_path = os.path.join(temp_path, f"tile_{i}.png")
    tile.save(target_path, format="png")
    r, g, b = tile.resize((1, 1)).getpixel((0, 0))
    return [target_path, r, g, b]


if __name__ == "__main__":
    directory_list = os.listdir(base_path)
    file_list = [os.path.join(base_path, file_name)
                 for file_name in directory_list]
    file_list = list(filter(lambda path: os.path.isfile(path), file_list))

    pool = Pool(cpu_count())
    results = tqdm.tqdm(pool.imap(get_average_color,
                        enumerate(file_list)), total=len(file_list))

    color_list = dict(w=TWIDTH, tiles={})
    color_list["tiles"] = {x[0]: x[1:] for x in results}

    tiles_data_path = os.path.join(temp_path, "tiles_data.json")
    with open(tiles_data_path, "w") as f:
        json.dump(color_list, f)
