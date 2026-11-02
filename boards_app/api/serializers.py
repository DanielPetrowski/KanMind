
from django.contrib.auth.models import User
from rest_framework import serializers
from boards_app.models import Board, Task, Comment  
from auth_app.api.serializers import UserSummarySerializer
from boards_app.api.permissions import is_board_member


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
    members = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all(), write_only=True, required=False
    )
    member_count = serializers.IntegerField(read_only=True, default=0)
    ticket_count = serializers.IntegerField(read_only=True, default=0)
    tasks_to_do_count = serializers.IntegerField(read_only=True, default=0)
    tasks_high_prio_count = serializers.IntegerField(read_only=True, default=0)

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
        """Ensure provided user IDs are valid, otherwise raise a clear error."""
       
        return value
    
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

class BoardTaskSerializer(serializers.ModelSerializer):
    """Task representation inside the board detail view."""

    assignee = UserSummarySerializer(read_only=True)
    reviewer = UserSummarySerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "reviewer",
            "due_date",
            "comments_count",
        ]

    def get_comments_count(self, obj):
        """Return the number of comments of the task."""
        return obj.comments.count()


class BoardDetailSerializer(serializers.ModelSerializer):
    """Detailed board representation with all members and tasks included."""

    owner_id = serializers.ReadOnlyField()
    members = UserSummarySerializer(many=True, read_only=True)
    tasks = BoardTaskSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = ["id", "title", "owner_id", "members", "tasks"]

class BoardUpdateSerializer(serializers.ModelSerializer):
    """Serializer matching the exact PATCH specification from documentation."""

    members = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all(), write_only=True
    )
    
    owner_data = UserSummarySerializer(
        source="owner", read_only=True
    )
    members_data = UserSummarySerializer(
        source="members", many=True, read_only=True
    )
    class Meta:
        model = Board
        fields = ["id", "title", "members", "owner_data", "members_data"]

    def validate_members(self, value):
        """Strictly validate that all provided member instance IDs exist."""
       
        input_ids = self.initial_data.get("members", [])
        if len(value) != len(input_ids):
            raise serializers.ValidationError("Einige Benutzer-IDs sind ungültig.")
        return value

    def update(self, instance, validated_data):
        if "title" in validated_data:
            instance.title = validated_data["title"]
        if "members" in validated_data:
            instance.members.set(validated_data["members"])
        instance.save()
        return instance

class AssignedTaskSerializer(serializers.ModelSerializer):
    """Serializer matching the exact specification for tasks assigned to the user."""

    assignee = UserSummarySerializer(read_only=True)
    reviewer = UserSummarySerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id",
            "board",  
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "reviewer",
            "due_date",
            "comments_count",
        ]

    def get_comments_count(self, obj):
        """Return the number of comments of the task."""
        return obj.comments.count()

class TaskCreateSerializer(serializers.ModelSerializer):
    """Serializer used for creating tasks, resolving user IDs cleanly into database instances."""

    
    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source="assignee",  
        required=False, 
        allow_null=True
    )
    reviewer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source="reviewer", 
        required=False, 
        allow_null=True
    )

    class Meta:
        model = Task
        fields = [
            "id",
            "board",
            "title",
            "description",
            "status",
            "priority",
            "assignee_id",
            "reviewer_id",
            "due_date",
        ]

    def to_representation(self, instance):
        """Use AssignedTaskSerializer for response representation to include full user data."""
        return AssignedTaskSerializer(instance, context=self.context).data


class TaskDetailSerializer(serializers.ModelSerializer):
    """Detailed representation of a task matching the doc response."""

    assignee = UserSummarySerializer(read_only=True)
    reviewer = UserSummarySerializer(read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "reviewer",
            "due_date",
        ]


class TaskUpdateSerializer(serializers.ModelSerializer):
    """Handles partial task updates with strict board membership validation."""

    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="assignee",
        required=False,
        allow_null=True,
    )
    reviewer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="reviewer",
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "status",
            "priority",
            "assignee_id",
            "reviewer_id",
            "due_date",
        ]

    def validate(self, attrs):
        """Ensure board cannot be updated and users are board members."""
        if "board" in self.initial_data:
            raise serializers.ValidationError(
                {"board": "Das Ändern des Boards ist nicht erlaubt."}
            )
        board = self.instance.board
        self._validate_member(attrs.get("assignee"), board, "assignee_id")
        self._validate_member(attrs.get("reviewer"), board, "reviewer_id")
        return attrs

    def _validate_member(self, user, board, field_name):
        """Ensure user is a member of the given board."""
        if user and not is_board_member(user, board):
            raise serializers.ValidationError(
                {field_name: "Benutzer ist kein Mitglied des Boards."}
            )

    def to_representation(self, instance):
        """Return full nested user representations on response."""
        return TaskDetailSerializer(instance, context=self.context).data

class CommentSerializer(serializers.ModelSerializer):
    """Serializer for comments displaying author's full name as a string."""

    author = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ["id", "created_at", "author", "content"]

        read_only_fields = ["id", "created_at", "author"]

    def validate_content(self, value):
        """Ensure comment content is not empty or pure whitespace."""
        if not value or not value.strip():
            raise serializers.ValidationError("Inhalt darf nicht leer sein.")
        return value

    def get_author(self, obj):
        """Return author's full name, fallback to username if empty."""
        full_name = f"{obj.author.first_name} {obj.author.last_name}".strip()
        return full_name if full_name else obj.author.username