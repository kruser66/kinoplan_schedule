import requests
import services.config as config


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
