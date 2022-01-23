import json
from PIL import Image
import os
import json
from multiprocessing import Pool, cpu_count
import tqdm
import settings

def get_average_color(pipe_in):
    i, image_path = pipe_in
    tile = Image.open(image_path)

    if tile.height > tile.width:
        half = (tile.height - tile.width) // 2
        tile = tile.crop((0, half, tile.width, half+tile.width))
    else:
        half = (tile.width - tile.height) // 2
        tile = tile.crop((half, 0, half+tile.height, tile.height))

    tile = tile.resize((settings.TILE_WIDTH, settings.TILE_WIDTH))
    tile = tile.convert("RGB")
    out_name = f"tile_{i}.jpeg"
    temp_dir = settings.TILES_DIRECTORY+"_temp"
    tile.save(os.path.join(temp_dir, out_name))
    r, g, b = tile.resize((1, 1)).getpixel((0, 0))
    return [out_name, r, g, b]

def main():
    directory_list = os.listdir(settings.TILES_DIRECTORY)
    file_list = [os.path.join(settings.TILES_DIRECTORY, file_name)
                 for file_name in directory_list]
    file_list = list(filter(lambda path: os.path.isfile(path), file_list))

    temp_dir = settings.TILES_DIRECTORY+"_temp"
    if not os.path.isdir(temp_dir):
        os.makedirs(temp_dir)

    pool = Pool(cpu_count())
    results = tqdm.tqdm(pool.imap(get_average_color,
                        enumerate(file_list)), total=len(file_list))

    color_list = dict(w=settings.TILE_WIDTH, tiles={})
    color_list["tiles"] = {x[0]: x[1:] for x in results}

    tiles_data_path = os.path.join(temp_dir, "tiles_data.json")
    with open(tiles_data_path, "w") as f:
        json.dump(color_list, f)

    return color_list

if __name__ == "__main__":
    main()