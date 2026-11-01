
from django.db.models import Q
from django.contrib.auth.models import User
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from boards_app.api.permissions import IsBoardOwnerOrMember , IsBoardOwnerOnly , IsTaskBoardMember
from boards_app.api.serializers import BoardSerializer , BoardDetailSerializer ,  BoardUpdateSerializer, AssignedTaskSerializer, TaskCreateSerializer, TaskDetailSerializer ,TaskUpdateSerializer
from boards_app.models import Board, Task
from rest_framework.exceptions import PermissionDenied, NotFound


class BoardListView(generics.ListCreateAPIView):
    """API view to retrieve and create boards for the active user."""

    serializer_class = BoardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter boards to show only those related to the active user."""
        user = self.request.user
        return Board.objects.filter(Q(owner=user) | Q(members=user)).distinct()

    def perform_create(self, serializer):
        """Automatically set the logged-in user as the board owner."""
        serializer.save(owner=self.request.user)

class BoardDetailView(generics.RetrieveUpdateDestroyAPIView):
    """API view to retrieve details of a specific board, including tasks."""

    queryset = Board.objects.all()
    serializer_class = BoardDetailSerializer
    permission_classes = [IsAuthenticated, IsBoardOwnerOrMember]
    lookup_field = "id"
    lookup_url_kwarg = "board_id"

    def get_serializer_class(self):
        """Return update serializer for PATCH/PUT and detail for GET."""
        if self.request.method in ["PATCH", "PUT"]:
            return BoardUpdateSerializer
        return BoardDetailSerializer


class AssignedTasksListView(generics.ListAPIView):
    """API view to retrieve tasks assigned to the active user as assignee or reviewer."""

    serializer_class = AssignedTaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter tasks where the user is either the assignee or the reviewer."""
        user = self.request.user
        return Task.objects.filter(Q(assignee=user) | Q(reviewer=user)).distinct()

class ReviewingTasksListView(generics.ListAPIView):
    """API view to retrieve tasks where the active user is set as the reviewer."""

    serializer_class = AssignedTaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter tasks where the user is the reviewer."""
        return Task.objects.filter(reviewer=self.request.user).distinct()

class TaskCreateView(generics.CreateAPIView):
    """API view to handle task creation with strict board membership verification."""

    serializer_class = TaskCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """Verify board existence and user membership before saving."""
        board_id = self.request.data.get("board")
        
        try:
            board = Board.objects.get(id=board_id)
        except Board.DoesNotExist:
            raise NotFound("Das angegebene Board existiert nicht.")

        
        is_owner = board.owner == self.request.user
        is_member = board.members.filter(id=self.request.user.id).exists()
        
        if not (is_owner or is_member):
            raise PermissionDenied("Du musst Mitglied des Boards sein, um eine Task zu erstellen.")
            
        serializer.save(created_by=self.request.user)

class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    """API view to retrieve, update or delete a specific task."""

    queryset = Task.objects.all()
    serializer_class = TaskUpdateSerializer
    permission_classes = [IsAuthenticated, IsTaskBoardMember]
    lookup_field = "id"
    lookup_url_kwarg = "task_id"

    def get_serializer_class(self):
        """Use read-only detail serializer for GET, update serializer for PATCH."""
        if self.request.method == "GET":
            return TaskDetailSerializer
        return TaskUpdateSerializer