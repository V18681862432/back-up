# -*- coding: utf-8 -*-
from django.db import models


# Create your models here.
class BackUp(models.Model):
    ip = models.CharField(max_length=32, verbose_name='主机ip')
    file = models.CharField(max_length=256, verbose_name='文件列表')
    count = models.IntegerField(default=0, verbose_name='文件数量')
    size = models.CharField(max_length=32, verbose_name='文件大小')
    back_time = models.DateTimeField(auto_now_add=True, verbose_name='备份时间')
    user_name = models.CharField(max_length=16, verbose_name='备份人')

    class Meta:
        db_table = 'back_up_detail'
