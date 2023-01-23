import os
import time

import requests
from PIL import Image, ImageDraw, ImageFont
from environs import Env
from datetime import datetime, date, timedelta
from pprint import pprint
from collections import OrderedDict


MONTH = ['ЯНВАРЯ', 'ФЕВРАЛЯ', 'МАРТА', 'АПРЕЛЯ',
         'МАЯ', 'ИЮНЯ', 'ИЮЛЯ', 'АВГУСТА', 'СЕНТЯБРЯ',
         'ОКТЯБРЯ', 'НОЯБРЯ', 'ДЕКАБРЯ']
WEEKDAYS = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС']
UTC = 5

def get_token(api_url, api_key):
    url = api_url + '/auth/token'
    params = {
        'api_key': api_key,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()

    return response.json()['request_token']


def get_schedule(api_url, token, date_start, date_end):
    url = api_url + '/schedule'

    params = {
        'dateStart': date_start, # YYYY-MM-DD
        'dateEnd': date_end, # YYYY-MM-DD
    }

    headers = {
        'REQUEST-TOKEN': token,
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    return response.json()


def fetch_next_week_dates(date) -> list[str]: # format dates YYYY-MM-DD

    delta_for_thursday =  4 - date.isoweekday()

    start_date = date + timedelta(days=delta_for_thursday)
    week_dates = []
    for day in range(7):
        week_dates.append(str(start_date + timedelta(days=day)))

    return week_dates


def dd_month(str_date):
    _, month, day = str_date.split('-')
    return f'{day} {MONTH[int(month) - 1]}'


def formate_schedule(schedule, films):

    formatted_schedule = {}
    for day, schedule_day in schedule.items():
        formatted_schedule[day] = {}
        for hall, schedule_hall in schedule_day.items():
            seances = []
            for seance in schedule_hall:
                hh, mm = seance['start'].split(':')
                seance_start = f'{(int(hh) + UTC):02}:{mm}'
                name, rate = films[seance['film_id']]
                chrono = f'{(seance["length"] // 60):01}:{(seance["length"] % 60):02}'
                if '3D' in seance['formats']:
                    name += ' 3D'
                seances.append(
                    {
                        'start': seance_start,
                        'name': name,
                        'rate': f'{rate:>4}',
                        'chrono': chrono,
                        'price': str(seance['sale']['price_max'])
                    }
                )
            formatted_schedule[day][hall] = seances

    return formatted_schedule


def draw_text_schedule(template, period=None, schedule=None):
    start_date = dd_month(period[0])
    end_date = dd_month(period[-1])

    img = Image.open(template)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("tahomabd.ttf", 48)
    font_small = ImageFont.truetype("tahomabd.ttf", 38)
    font_long_25= ImageFont.truetype("tahomabd.ttf", 36)
    font_long_35= ImageFont.truetype("tahomabd.ttf", 30)
    font_text = ImageFont.truetype("tahoma.ttf", 36)

    draw.text((1280, 180), start_date, (0, 0, 0), font=font)
    draw.text((1280, 280), end_date, (0, 0, 0), font=font)

    draw.text((1400, 350), "ЧТ,ПН-СР", (0, 0, 0), font=font_text)
    draw.text((1580, 350), "ПТ-ВС", (0, 0, 0), font=font_text)

    start_halls = dict(zip(('1','2','3'), (410, 1060, 1720)))

    # fill one day schedule and price
    for hall, seances in schedule[week_dates[0]].items():
        start = start_halls[hall]
        for index, seance in enumerate(seances):
            pos_y = start + index * 80
            draw.text((180, pos_y), seance['start'], (0, 0, 0), font=font)
            if len(seance['name']) < 25:
                draw.text((380, pos_y), seance['name'], (0, 0, 0), font=font)
            elif len(seance['name']) >= 35:
                draw.text((380, pos_y + 8), seance['name'], (0, 0, 0), font=font_long_35)
            else:
                draw.text((380, pos_y + 5), seance['name'], (0, 0, 0), font=font_long_25)
            draw.text((1130, pos_y + 5), seance['rate'], (0, 0, 0), font=font_small)
            draw.text((1250, pos_y + 5), seance['chrono'], (0, 0, 0), font=font_small)
            draw.text((1440, pos_y), seance['price'], (0, 0, 0), font=font)

    # fill weekend price
    for hall, seances in schedule[week_dates[2]].items():
        start = start_halls[hall]
        for index, seance in enumerate(seances):
            pos_y = start + index * 80
            draw.text((1600, pos_y), seance['price'], (0, 0, 0), font=font)

    img.save('test.jpg')
    img.show()


if __name__ == '__main__':

    env = Env()
    env.read_env()
    api_key = env.str('API_KEY')
    api_url = env.str('API_URL')
    template = env.str('TEMPLATE')

    week_dates = fetch_next_week_dates(date.today())
    start_date = week_dates[0]
    end_date = week_dates[-1]

    # draw_text_schedule(template)
    # exit()

    token = get_token(api_url, api_key)
    response = get_schedule(api_url, token, start_date, end_date)
    # pprint((response))
    # exit()
    films, halls, schedule = OrderedDict(sorted(response.items())).values()

    serialized_films = {
        film['kinoplan_id']: [film['name'], film['rate']] for film in films
    }

    schedule_by_date_by_hall = { day: {
            hall['title']: list(filter(lambda x: x['date'] == day and x['hall_id'] == hall['id'], schedule))
                for hall in halls
        } for day in week_dates}

    formatted_schedule = formate_schedule(schedule_by_date_by_hall, serialized_films)

    draw_text_schedule(template, week_dates, formatted_schedule)


