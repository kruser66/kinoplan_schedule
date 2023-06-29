from django.db import models


class Schedule(models.Model):
    year = models.SmallIntegerField('Год')
    week = models.SmallIntegerField('Неделя')

    class Meta:
        verbose_name = 'расписание'
        verbose_name_plural = 'расписания'

    def __str__(self):
        return f'{self.week} неделя {self.year} год'


class ScheduleImage(models.Model):
    schedule = models.ForeignKey(Schedule, related_name='images', on_delete=models.CASCADE)
    title = models.CharField('Период расписания', max_length=50)
    image = models.ImageField('Заполненный шаблон расписания')

    class Meta:
        verbose_name = 'картика расписания'
        verbose_name_plural = 'картинки расписания'

    def __str__(self):
        return self.title
    