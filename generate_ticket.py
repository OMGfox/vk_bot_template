from io import BytesIO

from PIL import Image, ImageDraw, ImageFont
from avatar_generator.generator import create_random_avatar


BLACK = (0, 0, 0, 255)
DEPARTURE_CITY_OFFSET = (350, 95)
DESTINATION_CITY_OFFSET = (350, 120)
DATE_OFFSET = (445, 140)
SEATS_OFFSET = (435, 165)
FONT_PATH = "fonts/Roboto-Bold.ttf"
FONT_SIZE = 18


def generate_ticket(departure_city, destination_city, date, seats):
    avatar = create_random_avatar()
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    background = Image.open("images/ticket_template.png")
    background.paste(avatar, (95, 40))
    draw = ImageDraw.Draw(background)
    draw.text(DEPARTURE_CITY_OFFSET, departure_city, font=font, fill=BLACK)
    draw.text(DESTINATION_CITY_OFFSET, destination_city, font=font, fill=BLACK)
    draw.text(DATE_OFFSET, date, font=font, fill=BLACK)
    draw.text(SEATS_OFFSET, seats, font=font, fill=BLACK)
    temp_file = BytesIO()
    background.save(temp_file, 'png')
    temp_file.seek(0)

    return temp_file
