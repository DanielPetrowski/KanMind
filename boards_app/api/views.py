
from django.db.models import Q
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from boards_app.api.serializers import BoardSerializer
from boards_app.models import Board


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
