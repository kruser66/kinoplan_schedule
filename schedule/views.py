from datetime import date
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.core.files.storage import default_storage
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

from schedule.models import Schedule, ScheduleImage
from make_schedule import fetch_next_week_dates, show_schedule

from wiki.models import Article, Category


KINO_WEEK = ['ЧТ', 'ПТ', 'СБ', 'ВС', 'ПН', 'ВТ', 'СР']


@login_required
def index(request):
    """Портал: выбор раздела — расписание или база знаний."""
    return render(request, 'home.html', {
        'wiki_article_count': Article.objects.filter(is_draft=False).count(),
        'wiki_category_count': Category.objects.count(),
    })


@login_required
def current_week(request):
    """Текущая кинонеделя — пункт «Расписание» с портала и LOGIN_REDIRECT."""
    year = date.today().year
    week = date.today().isocalendar().week
    return HttpResponseRedirect(reverse('week_schedule', args=(year, week,)))


@csrf_exempt
@login_required
def week_schedule(request, year, week):
    week_dates = fetch_next_week_dates(year, week)
    kino_week = list(zip(week_dates, KINO_WEEK))

    # Просмотр — только чтение: записи недели может и не быть.
    schedule = Schedule.objects.filter(year=year, week=week).first()

    if request.method == 'POST':
        # Запись недели создаётся только при генерации картинки (POST).
        # Просто просмотр страницы — только чтение: иначе health-чекеры
        # и листание стрелок наплодили 100k+ пустых строк на проде.
        schedule, _ = Schedule.objects.get_or_create(year=year, week=week)

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
        'images': schedule.images.all() if schedule else ScheduleImage.objects.none(),
        'visibility': 'invisible',
        'year': year,
        'week': week
    }
    
    return render(request, 'index.html', context=context)

@csrf_exempt
@login_required
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