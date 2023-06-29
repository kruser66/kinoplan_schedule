from django.contrib import admin
from schedule.models import Schedule, ScheduleImage


class ScheduleImageInline(admin.TabularInline):
    model = ScheduleImage
    extra = 0

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    inlines = [
        ScheduleImageInline
    ]
