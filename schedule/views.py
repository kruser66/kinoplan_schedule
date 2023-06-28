import os
from datetime import date, datetime
from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from schedule.models import Schedule
from make_schedule import fetch_next_week_dates, show_schedule
from django.views.decorators.cache import cache_control

KINO_WEEK = ['ЧТ', 'ПТ', 'СБ', 'ВС', 'ПН', 'ВТ', 'СР']


def index(request):
    year = date.today().year
    week = date.today().isocalendar().week
    print(fetch_next_week_dates(year, week - 1))

    return HttpResponseRedirect(reverse('week_schedule', args=(year, week,)))

@cache_control(max_age=0, no_cache=True, no_store=True, must_revalidate=True)
def week_schedule(request, year, week):
    week_dates = fetch_next_week_dates(year, week)
    kino_week = list(zip(week_dates, KINO_WEEK))

    context = {
        'kino_week': kino_week,
        'visibility': 'invisible',
        'year': year,
        'week': week
    }
    schedule = Schedule.objects.filter(year=year, week=week)
    if schedule:
        context.update(image=schedule[0].image, visibility='visible')

    if request.method == 'POST':
        week_select = []
        for day in range(7):
            week_select.append(1 if request.POST.getlist(f'day-{day}') else 0)

        fix_price = True if request.POST.getlist('fix_price') else False

        content_file = show_schedule(
            settings.API_URL,
            settings.API_KEY,
            settings.TEMPLATE,
            year,
            week,
            week_select,
            fix_price
        )

        new_schedule, created = Schedule.objects.update_or_create(year=year, week=week)

        if not created:
            os.remove(os.path.join(settings.MEDIA_ROOT, f'schedule_{year}_{week}.jpg'))

        new_schedule.image.save(
            f'schedule_{year}_{week}.jpg',
            content_file
        )
        context.update(image=new_schedule.image, visibility='visible')

    return render(request, 'index.html', context=context)