import os
import requests
from PIL import Image, ImageDraw, ImageFont
from environs import Env
from datetime import date, timedelta
from django.conf import settings
from collections import OrderedDict
from io import BytesIO
from django.core.files.base import ContentFile


MONTH = ['ЯНВАРЯ', 'ФЕВРАЛЯ', 'МАРТА', 'АПРЕЛЯ',
         'МАЯ', 'ИЮНЯ', 'ИЮЛЯ', 'АВГУСТА', 'СЕНТЯБРЯ',
         'ОКТЯБРЯ', 'НОЯБРЯ', 'ДЕКАБРЯ']
WEEKDAYS = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС']
UTC = 5
BASE_DIR = settings.BASE_DIR


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
        'dateStart': date_start,  # YYYY-MM-DD
        'dateEnd': date_end,  # YYYY-MM-DD
    }

    headers = {
        'REQUEST-TOKEN': token,
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    return response.json()


def fetch_next_week_dates(year: int, week: int, isoformat=False) -> list[str]:
    '''Возвращает список дней кинонедели, начиная с четверга в формате DD-MM-YYYY
    или YYYY-MM-DD если isoformat=True'''
    
    format_date = '%Y-%m-%d' if isoformat else '%d-%m-%Y'
    start_weekday = date(year, 1, 1) + timedelta(days=week*7)

    start_weekday += timedelta(days=(4 - start_weekday.isoweekday()))
    
    week_days = [
        (start_weekday + timedelta(days=day)).strftime(format_date) for day in range(7)
    ]

    return week_days


def dd_month(date: str):
    _, month, day = date.split('-')
    return f'{day} {MONTH[int(month) - 1]}'


def fetch_one_two_price(period):
    filters = [(date.fromisoformat(day).isoweekday() in (5, 6, 7)) for day in period]

    if all(filters):
        low = filters.index(True)
        high = -1
    elif not any(filters):
        low = filters.index(False)
        high = -1
    else:
        low = filters.index(False)
        high = filters.index(True)

    return low, high


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


def draw_schedule(template, period=None, schedule=None, fixprice=False):

    start_date = dd_month(period[0])
    end_date = dd_month(period[-1])

    low, high = fetch_one_two_price(period)

    one_price = False if high >= 0 else True

    if fixprice:
        one_price = True

    img = Image.open(template)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(os.path.join(BASE_DIR, 'static', "tahomabd.ttf"), 48)
    font_small = ImageFont.truetype(os.path.join(BASE_DIR, 'static', "tahomabd.ttf"), 38)
    font_long_25 = ImageFont.truetype(os.path.join(BASE_DIR, 'static', "tahomabd.ttf"), 36)
    font_long_35 = ImageFont.truetype(os.path.join(BASE_DIR, 'static', "tahomabd.ttf"), 30)
    font_text = ImageFont.truetype(os.path.join(BASE_DIR, 'static', "tahoma.ttf"), 36)

    draw.text((1280, 180), start_date, (0, 0, 0), font=font)
    draw.text((1280, 280), end_date, (0, 0, 0), font=font)

    if not one_price:
        draw.text((1400, 350), "ЧТ,ПН-СР", (0, 0, 0), font=font_text)
        draw.text((1580, 350), "ПТ-ВС", (0, 0, 0), font=font_text)

    start_halls = dict(zip(('1', '2', '3'), (410, 1060, 1720)))

    # fill one day schedule and price
    for hall, seances in schedule[period[low]].items():
        start = start_halls[hall]
        for index, seance in enumerate(seances):
            if len(seance) < 9:
                pos_y = start + index * 80
            else:
                pos_y = start + index * 70
            seance['name'] = seance['name'].split('.')[0]
            seance['name'] = seance['name'].split(':')[0]

            draw.text((180, pos_y), seance['start'], (0, 0, 0), font=font)
            if len(seance['name']) < 25:
                draw.text((380, pos_y), seance['name'], (0, 0, 0), font=font)
            elif len(seance['name']) >= 35:
                draw.text((380, pos_y + 8), seance['name'], (0, 0, 0), font=font_long_35)
            else:
                draw.text((380, pos_y + 5), seance['name'], (0, 0, 0), font=font_long_25)
            draw.text((1130, pos_y + 5), seance['rate'], (0, 0, 0), font=font_small)
            draw.text((1250, pos_y + 5), seance['chrono'], (0, 0, 0), font=font_small)
            if one_price:
                draw.text((1520, pos_y), seance['price'], (0, 0, 0), font=font)
            else:
                draw.text((1440, pos_y), seance['price'], (0, 0, 0), font=font)

    # fill weekend price
    if not one_price:
        for hall, seances in schedule[period[high]].items():
            start = start_halls[hall]
            for index, seance in enumerate(seances):
                pos_y = start + index * 80
                draw.text((1600, pos_y), seance['price'], (0, 0, 0), font=font)

    buffer = BytesIO()
    img.save(fp=buffer, format='JPEG')

    return ContentFile(buffer.getvalue())



def show_schedule(api_url, api_key, template, year, week, selected_day, fixprice=False):
    week_dates = fetch_next_week_dates(year, week, isoformat=True)
    start_date = week_dates[0]
    end_date = week_dates[-1]

    token = get_token(api_url, api_key)
    response = get_schedule(api_url, token, start_date, end_date)

    films, halls, schedule = OrderedDict(sorted(response.items())).values()

    serialized_films = {
        film['kinoplan_id']: [film['marketing_title'] if film.get('marketing_title') else film['name'], film['rate']] for film in films
    }

    schedule_by_date_by_hall = {day: {
            hall['title']: list(filter(lambda x: x['date'] == day and x['hall_id'] == hall['id'], schedule))
            for hall in halls
        } for day in week_dates}

    formatted_schedule = formate_schedule(schedule_by_date_by_hall, serialized_films)

    filtered_week = [day for index, day in enumerate(week_dates) if selected_day[index] == 1]

    return draw_schedule(template, filtered_week, formatted_schedule, fixprice)  # период 0 - четверг, 6 - среда


if __name__ == '__main__':
    env = Env()
    env.read_env()
    api_key = env.str('API_KEY')
    api_url = env.str('API_URL', 'http://ts.kinoplan24.ru/api')
    template = env.str('TEMPLATE', './assets/template.jpg')

    # show_schedule(api_url, api_key, template, [0, 0, 1, 1, 1, 1, 1])
    print(fetch_next_week_dates(2023, 55))