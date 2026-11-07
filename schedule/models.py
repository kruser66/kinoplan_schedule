from django.db import models


class Schedule(models.Model):
    year = models.SmallIntegerField('Год')
    week = models.SmallIntegerField('Неделя')

    class Meta:
        verbose_name = 'расписание'
        verbose_name_plural = 'расписания'
        # одна запись на неделю: без ограничения параллельные запросы
        # плодили дубликаты (на проде набежало >100k строк)
        constraints = [
            models.UniqueConstraint(fields=('year', 'week'), name='unique_year_week'),
        ]

    def __str__(self):
        return f'{self.week} неделя {self.year} год'


class ScheduleImage(models.Model):
    schedule = models.ForeignKey(Schedule, related_name='images', on_delete=models.CASCADE)
    title = models.CharField('Период расписания', max_length=50)
    image = models.ImageField('Заполненный шаблон расписания')
    created_at = models.DateTimeField('Создана', auto_now_add=True, null=True, blank=True,
                                      db_index=True)

    class Meta:
        verbose_name = 'картинка расписания'
        verbose_name_plural = 'картинки расписания'

    def __str__(self):
        return self.title
    