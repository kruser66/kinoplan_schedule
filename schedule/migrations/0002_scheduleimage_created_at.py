from django.db import migrations, models

# Изначально здесь был RunPython-бэкфилт «возраста по кинонеделе», но он
# мёртвый: AddField с auto_now_add заполняет существующие строки «сейчас»
# на уровне schema editor (Django base/schema.py _effective_default), и
# фильтр created_at__isnull=True не матчит ни одной строки. Реальный
# бэкфилт делает 0003_created_at_from_week.


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='scheduleimage',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, blank=True, null=True,
                                       verbose_name='Создана'),
        ),
    ]
