from rest_framework import serializers
from .models import MediaFile
from behaviors.models import BehaviorLog
from activities.models import ActivityLog

ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/gif"]
ALLOWED_VIDEO_TYPES = ["video/mp4", "video/quicktime", "video/x-msvideo", "video/x-matroska"]
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

class MediaFileSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.StringRelatedField(read_only=True)
    file_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    behavior_log = serializers.PrimaryKeyRelatedField(queryset=BehaviorLog.objects.all(), required=False, allow_null=True)
    activity_log = serializers.PrimaryKeyRelatedField(queryset=ActivityLog.objects.all(), required=False, allow_null=True)

    class Meta:
        model = MediaFile
        fields = ['id', 'file', 'file_url', 'thumbnail_url', 'media_type', 'description', 'uploaded_by', 'behavior_log', 'activity_log', 'created_at']
        read_only_fields = ['id', 'uploaded_by', 'created_at', 'file_url', 'thumbnail_url']

    def get_file_url(self, obj):
        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url

    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.thumbnail.url)
            return obj.thumbnail.url
        return None

    def validate_file(self, file):
        if file.size > MAX_FILE_SIZE:
            raise serializers.ValidationError(
                f"File size exceeds the maximum allowed size of {MAX_FILE_SIZE / (1024 * 1024):.0f}MB."
            )
        return file

    def validate(self, data):
        file = data.get('file')
        if file:
            content_type = file.content_type
            if content_type in ALLOWED_IMAGE_TYPES:
                data['media_type'] = 'image'
            elif content_type in ALLOWED_VIDEO_TYPES:
                data['media_type'] = 'video'
            else:
                raise serializers.ValidationError(
                    f"Unsupported file type: {content_type}. Allowed types: {', '.join(ALLOWED_IMAGE_TYPES + ALLOWED_VIDEO_TYPES)}"
                )
        return data

    def create(self, validated_data):
        validated_data['uploaded_by'] = self.context['request'].user
        return super().create(validated_data) 