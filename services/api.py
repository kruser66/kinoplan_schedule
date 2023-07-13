import requests
import services.config as config

from pprint import pprint


def get_kinoplan_token():
    '''Получение тоекна для работы с API Киноплана.
    https://api.kinoplan.ru/doc/#api-Authorization-GetApiAuthToken'''
    
    url = config.API_URL + '/auth/token'
    params = {
        'api_key': config.API_KEY,
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()

    return response.json()['request_token']


def get_week_schedule(date_start, date_end):
    '''Получить полное расписание кинотеатра за указанный период (неделю)
    https://api.kinoplan.ru/doc/#api-Schedule-GetSchedule'''
    
    url = config.API_URL + '/schedule'   
    token = get_kinoplan_token()
    
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


def get_release_info(token, film_id):
    '''Получить marketing_title ели есть такое'''
    url = config.API_URL + '/release/' + str(film_id) + '/full'
    
    headers = {
        'REQUEST-TOKEN': token,
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    return response.json()


def get_marketing_title(token, film_id):
    
    release_info = get_release_info(token, film_id)
    
    return release_info['marketing_title']