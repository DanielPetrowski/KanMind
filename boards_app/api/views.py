
from django.db.models import Q,Count
from django.contrib.auth.models import User
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from boards_app.api.permissions import IsBoardOwnerOrMember , IsBoardOwnerOnly , IsTaskBoardMember,  IsTaskCreatorOrBoardOwner, IsCommentAuthor
from boards_app.api.serializers import BoardSerializer , BoardDetailSerializer ,  BoardUpdateSerializer, AssignedTaskSerializer, TaskCreateSerializer, TaskDetailSerializer ,TaskUpdateSerializer, CommentSerializer, is_board_member
from boards_app.models import Board, Task, Comment
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError


class BoardListView(generics.ListCreateAPIView):
    """API view to retrieve and create boards for the active user."""

    serializer_class = BoardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter boards to show only those related to the active user."""
        user = self.request.user
        return (
            Board.objects.filter(Q(owner=user) | Q(members=user))
            .annotate(
                member_count=Count("members", distinct=True),
                ticket_count=Count("tasks", distinct=True),
                tasks_to_do_count=Count("tasks", filter=Q(tasks__status="to-do"), distinct=True),
                tasks_high_prio_count=Count("tasks", filter=Q(tasks__priority="high"), distinct=True),
            )
            .distinct()
        )

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
    lookup_field = "id"
    lookup_url_kwarg = "task_id"

    def get_permissions(self):
        """Use strict creator/owner check for DELETE, member check for others."""
        if self.request.method == "DELETE":
            return [IsAuthenticated(), IsTaskCreatorOrBoardOwner()]
        return [IsAuthenticated(), IsTaskBoardMember()]

    def get_object(self):
        """Validate task_id format before querying to ensure 400 on bad data."""
        task_id = self.kwargs.get("task_id")
        if not str(task_id).isdigit():
            raise ValidationError("Die übermittelte Task-ID ist fehlerhaft.")
        return super().get_object()

    def get_serializer_class(self):
        """Use read-only detail serializer for GET, update serializer for PATCH."""
        if self.request.method == "GET":
            return TaskDetailSerializer
        return TaskUpdateSerializer

class TaskCommentsView(generics.ListCreateAPIView):
    """API view to list all comments belonging to a specific task."""

    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Ensure task exists, user has access, and return ordered comments."""
        task = self._get_task()
        return task.comments.all().order_by("created_at")

    def perform_create(self, serializer):
        """Save comment with authenticated user and the associated task."""
        task = self._get_task()
        serializer.save(author=self.request.user, task=task)

    def _get_task(self):
        """Fetch task and verify user membership in its board."""
        task_id = self.kwargs.get("task_id")
        try:
            task = Task.objects.select_related("board").get(id=task_id)
        except (Task.DoesNotExist, ValueError):
            raise NotFound("Task nicht gefunden.")
        if not is_board_member(self.request.user, task.board):
            raise PermissionDenied("Du musst Mitglied des Boards sein.")
        return task

# 🟢 NEU: Endpunkt zum Löschen eines Kommentars (DELETE)
class TaskCommentDetailView(generics.DestroyAPIView):
    """API view to delete a specific comment from a task."""

    permission_classes = [IsAuthenticated, IsCommentAuthor]

    def get_object(self):
        """Retrieve comment ensuring task and comment exist and match."""
        task_id = self.kwargs.get("task_id")
        comment_id = self.kwargs.get("comment_id")
        self._validate_ids(task_id, comment_id)
        self._validate_task_exists(task_id)
        comment = self._get_comment(comment_id, task_id)
        self.check_object_permissions(self.request, comment)
        return comment

    def _validate_ids(self, task_id, comment_id):
        """Validate ID formats to reject non-numeric values with 400."""
        if not str(task_id).isdigit() or not str(comment_id).isdigit():
            raise ValidationError("Ungültige Anfragedaten.")

    def _validate_task_exists(self, task_id):
        """Ensure task exists or raise NotFound."""
        if not Task.objects.filter(id=task_id).exists():
            raise NotFound("Task nicht gefunden.")

    def _get_comment(self, comment_id, task_id):
        """Fetch comment belonging to task or raise NotFound."""
        try:
            return Comment.objects.get(id=comment_id, task_id=task_id)
        except Comment.DoesNotExist:
            raise NotFound("Kommentar nicht gefunden.")