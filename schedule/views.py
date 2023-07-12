import os
from datetime import date, datetime
from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.core.files.storage import default_storage

from schedule.models import Schedule, ScheduleImage
from make_schedule import fetch_next_week_dates, show_schedule, fetch_one_two_price


KINO_WEEK = ['ЧТ', 'ПТ', 'СБ', 'ВС', 'ПН', 'ВТ', 'СР']


def index(request):
    year = date.today().year
    week = date.today().isocalendar().week
    print(fetch_next_week_dates(year, week - 1))

    return HttpResponseRedirect(reverse('week_schedule', args=(year, week,)))


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
            year,
            week,
            selection,
            one_price
        )

        if default_storage.exists(content_file.name):
            default_storage.delete(content_file.name)
        
        title = content_file.name.split('.')[0]
        ScheduleImage.objects.update_or_create(title=title, schedule=schedule, defaults={'image': content_file})

    context = {
        'kino_week': kino_week,
        'images': schedule.images.all(),
        'visibility': 'invisible',
        'year': year,
        'week': week
    }
    
    return render(request, 'index.html', context=context)


def delete_image(request, pk):
    
    try:
        image_for_deletion = ScheduleImage.objects.get(id=pk)
        filename = image_for_deletion.title + '.jpg'
        if default_storage.exists(filename):
            default_storage.delete(filename)
        image_for_deletion.delete()
    except:
        pass
    
    return HttpResponseRedirect(request.GET['next'])