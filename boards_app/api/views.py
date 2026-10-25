
from django.db.models import Q
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

# 3. Lokale Importe (eigene Module)
from boards_app.api.serializers import BoardSerializer
from boards_app.models import Board


class BoardListView(generics.ListAPIView):
    """API view to retrieve all boards where the user is owner or member."""

    serializer_class = BoardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter boards to show only those related to the active user."""
        user = self.request.user
        return Board.objects.filter(Q(owner=user) | Q(members=user)).distinct()
