
from django.urls import path
from boards_app.api.views import BoardListView

urlpatterns = [
    path('boards/', BoardListView.as_view(), name='board-list'),
]
