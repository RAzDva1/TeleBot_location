import telebot
import database_api as db
from telebot import types
from collections import defaultdict
import os

try:
    import Image
except ImportError:
    from PIL import Image

PATH_TO_IMAGES = r''
TEXT_HELP = "I have several commands: \n " \
            "you can send me location and I save it for you.\n" \
            "/add I add your location. \n" \
            "/list: I send you all your location.\n" \
            "/reset: I delete all your location\n"
TOKEN = '1376189072:AAF3GYOqbTdNBFWNpblfSpFcRsZsI4OEzSc'
START, NAME, LOCATION, IS_PHOTO, PHOTO, ADD = range(6)
bot = telebot.TeleBot(TOKEN)

USER_STATE = defaultdict(lambda: START)
USER_PLACE = defaultdict(lambda: {})


def get_state(message):
    return USER_STATE[message.chat.id]


def update_state(message, state):
    USER_STATE[message.chat.id] = state


def update_user_place(user_id, key, value):
    USER_PLACE[user_id][key] = value


def get_user_place(user_id):
    return USER_PLACE[user_id]


def create_keyboard_is_photo():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(text=c, callback_data=c) for c in ["Yes", "No"]]
    keyboard.add(*buttons)
    return keyboard


@bot.message_handler(commands=['help'])
def send_welcome(message):
    bot.send_message(chat_id=message.chat.id, text=TEXT_HELP)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(chat_id=message.chat.id, text=TEXT_HELP)


@bot.message_handler(commands=['add'])
def location_handler(message):
    update_state(message, NAME)
    bot.send_message(chat_id=message.chat.id, text="Please, enter name of your place")


@bot.message_handler(func=lambda message: get_state(message) == NAME)
def location_handler(message):
    update_user_place(message.chat.id, 'location_name', message.text)
    bot.send_message(chat_id=message.chat.id, text="Okay, now send the location.")
    update_state(message, LOCATION)


@bot.message_handler(content_types=["sticker", "pinned_message", "photo", "audio", "location", "text"],
                     func=lambda message: get_state(message) == LOCATION)
def location_handler(message):
    if message.content_type == "location":
        update_user_place(message.chat.id, 'longitude', message.location.longitude)
        update_user_place(message.chat.id, 'latitude', message.location.latitude)
        keyboard = create_keyboard_is_photo()
        bot.send_message(chat_id=message.chat.id, text="Okay, do you want to add photo?",
                         reply_markup=keyboard)
        update_state(message, IS_PHOTO)
    else:
        bot.send_message(chat_id=message.chat.id, text="Please, enter location")


@bot.callback_query_handler(func=lambda x: get_state(x.message) == IS_PHOTO)
def callback_handler_photo(callback_query):
    message = callback_query.message
    text = callback_query.data
    if text == "Yes":
        bot.send_message(chat_id=message.chat.id, text="Send photo")
        update_state(message, PHOTO)
    else:
        bot.send_message(chat_id=message.chat.id, text="Ok, we add your location")
        update_state(message, ADD)
        update_user_place(message.chat.id, 'photo_path', '')
        adding_in_database(message)


@bot.message_handler(content_types=["sticker", "pinned_message", "audio", "location", "text", "document"],
                     func=lambda message: get_state(message) == PHOTO)
def photo_handler(message):
    bot.send_message(chat_id=message.chat.id, text="Please, send photo")


@bot.message_handler(content_types=["photo"],
                     func=lambda message: get_state(message) == PHOTO)
def photo_handler(message):
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    src = os.path.join(get_path_for_images(), message.photo[-1].file_id + '.jpg')
    with open(src, 'wb') as new_file:
        new_file.write(downloaded_file)
    update_state(message, ADD)
    update_user_place(message.chat.id, 'photo_path', str(message.photo[-1].file_id) + '.jpg')
    adding_in_database(message)


def adding_in_database(message):
    bot.send_message(chat_id=message.chat.id, text="You add your location!")
    db.add_user_location(user_id=message.chat.id,
                         longitude=get_user_place(message.chat.id)['longitude'],
                         latitude=get_user_place(message.chat.id)['latitude'],
                         comment=get_user_place(message.chat.id)['location_name'],
                         path_to_photo=get_user_place(message.chat.id)['photo_path'])
    update_state(message, START)


@bot.message_handler(commands=['list'])
def get_user_location(message):
    db_request = db.get_user_location(user_id=message.from_user.id)
    if db_request:
        for location in db_request:
            bot.send_message(chat_id=message.chat.id, text=location[2])
            bot.send_location(chat_id=message.chat.id, latitude=location[1], longitude=location[0])
            if location[3]:
                path = os.path.join(get_path_for_images(), str(location[3]))
                with open(path, 'rb') as read_file:
                    bot.send_photo(chat_id=message.chat.id, photo=read_file)
    else:
        bot.send_message(chat_id=message.chat.id, text="You don't have any location yet")


@bot.message_handler(commands=['get'])
def get_user_location(message):
    print(message.from_user.id)
    db_request = db.get_user_location(user_id=message.from_user.id)
    if db_request:
        for location in db_request:
            bot.send_location(chat_id=message.chat.id, latitude=location[1], longitude=location[0])
    else:
        bot.send_message(chat_id=message.chat.id, text="You don't have any location yet")


@bot.message_handler(commands=['reset'])
def delete_user_location(message):
    db.delete_user_location(user_id=message.from_user.id)


def set_dir_for_images():
    if not os.path.isdir("images"):
        os.mkdir("images")
    return os.path.join(os.getcwd(), r"images")


def get_path_for_images():
    return PATH_TO_IMAGES


if __name__ == '__main__':
    PATH_TO_IMAGES = set_dir_for_images()
    db.init_db()
    bot.polling()
