from django.urls import path
from . import views

urlpatterns = [
    path('upload', views.upload_document_review, name='upload_document_review'),
]