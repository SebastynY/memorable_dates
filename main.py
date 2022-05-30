from bs4 import BeautifulSoup
import bs4
import requests
import datetime
import shelve
import telebot
import textwrap as tw
from telebot import types


def get_today_date() -> str:
    now = datetime.datetime.now()
    return f'{now.month}-{now.day}'


def get_general_link() -> bs4.element.ResultSet:
    """get the main page where the events are located"""
    now_date = get_today_date()
    history_date = requests.get(f'https://www.calend.ru/events/{now_date}')
    html_code = BeautifulSoup(history_date.text, "html.parser")
    link_events = html_code.findAll('p', class_='descr descrFixed')
    return link_events


def get_events_link() -> list:
    """get events links from html and returns a list"""
    return [link.find('a').get('href') for link in get_general_link()]


def get_url_status() -> str:
    url = 'memorable_dates/user_data/status'
    return url


def create_file_status() -> None:
    """create a file that will store the status of links. By default, we start with the first"""
    with shelve.open(get_url_status()) as db:
        db['event_number'] = -1


def current_status() -> int:
    """return the state from the status file"""
    number: int
    with shelve.open(get_url_status()) as db:
        number = db.get('event_number')
    return number


def change_status() -> None:
    """changing the status values to go through the entire array of events"""
    with shelve.open(get_url_status()) as db:
        if current_status() < len(get_events_link()) - 1:
            db['event_number'] = current_status() + 1
        else:
            db['event_number'] = 0


def links_request() -> BeautifulSoup:
    """making a request using the event link"""

    events = get_events_link()
    link_status = current_status()
    event_link = requests.get(events[link_status])
    event_html = BeautifulSoup(event_link.text, "html.parser")
    change_status()
    return event_html


def get_event_info() -> str:
    """
    :param: accepts html page
    :return: returns the html page information as a string
    """
    html = links_request()
    title = html.find('h1', {'class': 'h101'})
    main_text = html.find('div', {'class': 'maintext'})
    date_time = html.find('span', {'class': 'addInfo'})
    image = html.find('p', {'class': 'float'})
    shortened_main_text = tw.shorten(main_text.text, width=500, placeholder="...")
    content = (
        f'{date_time.text}\n\n {title.text}\n\n {shortened_main_text}\n {image.img.get("src")}'
    )
    return content


bot = telebot.TeleBot('5378299384:AAEnU0jD3ml6ZxntdNb69b5omRR1uaKLDN4')


@bot.message_handler(commands=["start"])
def start(m, res=False):
    create_file_status()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button = types.KeyboardButton("Показать событие")
    markup.add(button)
    bot.send_message(m.chat.id,
                     f'Если хотите узнать, какое событие произошло {datetime.datetime.now().day} числа нажмите на кнопку `Показать событиe`',
                     reply_markup=markup)


@bot.message_handler(content_types=["text"])
def handle_text(message):
    if message.text.strip() == 'Показать событие':
        bot.send_message(message.chat.id, get_event_info())
        if current_status() < len(get_events_link()) - 1:
            bot.send_message(message.chat.id,
                             f'Вы просмотрели {current_status() + 1} событие')
        else:
            bot.send_message(message.chat.id,
                             'Вы посмотрели все новости! \n Чтобы посмотреть их ещё раз нажмите "Показать событие"')


bot.polling(none_stop=True, interval=0)
