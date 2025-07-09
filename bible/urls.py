from django.urls import path
from .views import BibleVerseView

urlpatterns = [
    path('verses/<str:book>/<int:chapter>/<int:verse>/', BibleVerseView.as_view(), name='bible-verse'),
]
