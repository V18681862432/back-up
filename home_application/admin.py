# -*- coding: utf-8 -*-
from django.contrib import admin

# Register your models here.
from home_application.models import BackUp


class BackUpAdmin(admin.ModelAdmin):
    list_display = ['ip', 'user_name', 'file', 'count', 'size', 'back_time']


admin.site.register(BackUp, BackUpAdmin)
