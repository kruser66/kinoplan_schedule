# Generated by Django 4.1.6 on 2023-03-01 09:11

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Schedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.SmallIntegerField(verbose_name='Год')),
                ('week', models.SmallIntegerField(verbose_name='Неделя')),
                ('image', models.ImageField(upload_to='', verbose_name='Расписание')),
            ],
            options={
                'verbose_name': 'расписание на неделю',
                'verbose_name_plural': 'расписания на неделю',
            },
        ),
    ]
