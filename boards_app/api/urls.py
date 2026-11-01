
from django.urls import path
from boards_app.api.views import BoardListView , BoardDetailView, AssignedTasksListView
urlpatterns = [
    path('boards/', BoardListView.as_view(), name='board-list'),
    path('boards/<int:board_id>/', BoardDetailView.as_view(), name='board-detail'),
    path('tasks/assigned-to-me/', AssignedTasksListView.as_view(), name='assigned-tasks'),
]
