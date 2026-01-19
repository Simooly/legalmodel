
from django.contrib import admin
from django.urls import path
from difyapi import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('upload', views.upload_document_review, name='upload_document_review'),
]
