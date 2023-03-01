from django.db import models


class Schedule(models.Model):
    year = models.SmallIntegerField('Год')
    week = models.SmallIntegerField('Неделя')
    image = models.ImageField('Расписание')

    class Meta:
        verbose_name = 'расписание на неделю'
        verbose_name_plural = 'расписания на неделю'

    def __str__(self):
        return f'Schedule: {self.year}-{self.week}'