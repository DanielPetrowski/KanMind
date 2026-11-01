
from django.urls import path
from boards_app.api.views import BoardListView , BoardDetailView, AssignedTasksListView , ReviewingTasksListView,  TaskCreateView, TaskDetailView
urlpatterns = [
    path('boards/', BoardListView.as_view(), name='board-list'),
    path('boards/<int:board_id>/', BoardDetailView.as_view(), name='board-detail'),
    path('tasks/assigned-to-me/', AssignedTasksListView.as_view(), name='assigned-tasks'),
    path('tasks/reviewing/', ReviewingTasksListView.as_view(), name='reviewing-tasks'),
    path('tasks/', TaskCreateView.as_view(), name='task-create'),
    path("tasks/<int:task_id>/", TaskDetailView.as_view(), name="task-detail"),
]
