from django.shortcuts import render
from django.conf import settings
from make_schedule import fetch_next_week_dates, show_schedule

KINO_WEEK = ['ЧТ', 'ПТ', 'СБ', 'ВС', 'ПН', 'ВТ', 'СР']


def index(request):
    week_dates = fetch_next_week_dates()
    kino_week = list(zip(['-'.join(day.split('-')[::-1]) for day in week_dates], KINO_WEEK))

    context = {
        'kino_week': kino_week,
        'visibility': 'invisible'
    }

    if request.method == 'POST':
        week = []
        context['visibility'] = 'visible'
        for day in range(7):
            week.append(1 if request.POST.getlist(f'day-{day}') else 0)
        print(week)
        show_schedule(settings.API_URL, settings.API_KEY, settings.TEMPLATE, week)


    return render(request, 'index.html', context=context)
