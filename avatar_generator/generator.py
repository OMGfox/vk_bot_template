import os
import random

from PIL import Image

SIZE = 128

DEFAULT_COLORS = (
    0x81bef1,
    0xad8bf2,
    0xbff288,
    0xde7878,
    0xa5aac5,
    0x6ff2c5,
    0xf0da5e,
    0xeb5972,
    0xf6be5d,
)

while "avatar_generator" not in os.listdir("./"):
    os.chdir("../")

PATH_TO_FACE_PARTS = os.path.join("avatar_generator", "face_parts")


def random_part(part: str):
    parts_path = os.path.join(PATH_TO_FACE_PARTS, part)
    part_name = random.choice(os.listdir(parts_path))
    image = Image.open(os.path.join(parts_path, part_name), mode="r")
    return image.resize((SIZE, SIZE))


def create_random_avatar() -> Image:
    image = Image.new(mode="RGB", size=(SIZE, SIZE), color=random.choice(DEFAULT_COLORS))
    eyes = random_part(part="eyes")
    nose = random_part(part="nose")
    mouth = random_part(part="mouth")
    image.paste(eyes, (0, 0), eyes)
    image.paste(eyes, (0, 0), nose)
    image.paste(eyes, (0, 0), mouth)
    return image


create_random_avatar()

