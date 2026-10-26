# 1. Standardbibliothek

# 2. Drittanbieter
from rest_framework import permissions

# 3. Lokale Importe (eigene Module)


def is_board_member(user, board):
    """Check if a user is the owner or a member of a board."""
    if board.owner == user:
        return True
    return board.members.filter(id=user.id).exists()


class IsBoardOwnerOrMember(permissions.BasePermission):
    """Permission to allow access only to board owners or members."""

    def has_object_permission(self, request, view, obj):
        """Check if the requesting user has access to the board object."""
        return is_board_member(request.user, obj)


class IsBoardOwnerOnly(permissions.BasePermission):
    """Permission to allow access only strictly to the board owner."""

    def has_object_permission(self, request, view, obj):
        """Check if the requesting user is the absolute owner of the board."""
        return obj.owner == request.user