
from django.contrib.auth.models import User
from rest_framework import serializers


from boards_app.models import Board, Task


def members_field():
    """Return a write-only field that accepts a list of user ids."""
    return serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all(),
        write_only=True,
        required=False,
    )

class BoardSerializer(serializers.ModelSerializer):
    """Board summary used for listing user boards."""

    owner_id = serializers.ReadOnlyField()
    members = serializers.ListField(
        child=serializers.EmailField(), write_only=True, required=False
    )
    member_count = serializers.SerializerMethodField()
    ticket_count = serializers.SerializerMethodField()
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = [
            "id",
            "title",
            "members", 
            "member_count",
            "ticket_count",
            "tasks_to_do_count",
            "tasks_high_prio_count",
            "owner_id",
        ]

    def validate_members(self, value):
        """Ensure all provided member emails exist in the database."""
        existing_users = User.objects.filter(email__in=value)
        if len(existing_users) != len(value):
            raise serializers.ValidationError("Some user emails are invalid.")
        
        return existing_users
    
    def get_member_count(self, obj):
        """Return the number of board members."""
        return obj.members.count()

    def get_ticket_count(self, obj):
        """Return the total number of tasks on the board."""
        return obj.tasks.count()

    def get_tasks_to_do_count(self, obj):
        """Return the number of tasks with status to-do."""
        return obj.tasks.filter(status=Task.Status.TO_DO).count()

    def get_tasks_high_prio_count(self, obj):
        """Return the number of tasks with high priority."""
        return obj.tasks.filter(priority=Task.Priority.HIGH).count()
