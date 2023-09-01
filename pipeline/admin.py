from django.contrib import admin

from .models import OpenquakeHazardTask


class OpenquakeHazardTaskAdmin(admin.ModelAdmin):
    fields = ["general_task_id", "date", "notes", "config_info", "part_of"]
    list_display = ("general_task_id", "date", "notes", "config_info", "part_of")
    list_filter = ("date", "part_of")


admin.site.register(OpenquakeHazardTask, OpenquakeHazardTaskAdmin)
