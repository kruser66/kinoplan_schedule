import os
from datetime import date, datetime
from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from schedule.models import Schedule, ScheduleImage
from make_schedule import fetch_next_week_dates, show_schedule, fetch_one_two_price
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

    schedule, _ = Schedule.objects.get_or_create(year=year, week=week)

    if request.method == 'POST':
        selection = []
        for day in range(7):
            selection.append(1 if request.POST.getlist(f'day-{day}') else 0)

        one_price = True if request.POST.getlist('fix_price') else False

        content_file = show_schedule(
            settings.TEMPLATE,
            year,
            week,
            selection,
            one_price
        )

        new_schedule_image, created = ScheduleImage.objects.update_or_create(title='schedule', schedule=schedule)
        new_schedule_image.image.save(
            f'schedule_{year}_{week}_{new_schedule_image.id}.jpg',
            content_file
        )

    context = {
        'kino_week': kino_week,
        'images': schedule.images.all(),
        'visibility': 'invisible',
        'year': year,
        'week': week
    }
    
    return render(request, 'index.html', context=context)