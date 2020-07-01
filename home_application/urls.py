# -*- coding: utf-8 -*-

from django.conf.urls import url
from . import views

urlpatterns = (
    url(r'^$', views.home),
    url(r'^dev-guide/$', views.dev_guide),
    url(r'^contact/$', views.contact),
    url(r'^history/$', views.history),
    url(r'^api/search_business/$', views.search_business),
    url(r'^api/search_biz_inst_topo/$', views.search_biz_inst_topo),
    url(r'^api/search_host/$', views.search_host),
    url(r'^api/fast_execute_script/$', views.fast_execute_script),
    url(r'^api/execute_job/$', views.execute_job),
)
