from ckeditor.fields import RichTextField
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import Collection, Post, SavedPost, Follow

User = get_user_model()


class FollowSerializer(serializers.ModelSerializer):
    following = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    
    class Meta:
        model = Follow
        fields = ('following',)


class FollowUserSerializer(serializers.Serializer):
    following = serializers.IntegerField()

    def create(self, validated_data):
        request = self.context['request']
        follower = request.user
        following = validated_data['following']

        if follower.id == following:
            raise serializers.ValidationError(f"Provide valid id, You can't follow yourself.")

        if follower.is_authenticated or following:
            if Follow.objects.filter(follower=follower, following=User.objects.get(pk=following)).exists():
                raise serializers.ValidationError(f"You alread following that user.")
            return Follow.objects.create(follower=follower, following=User.objects.get(pk=following))
        else:
            raise serializers.ValidationError(f"Not valid data! Missing value for following or not authenticate.")

class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'profile_picture']


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ['id', 'label']


class SimplePostSerializer(serializers.ModelSerializer):
    owner = SimpleUserSerializer(read_only=True)
    views = serializers.IntegerField(read_only=True)
    collection = CollectionSerializer()

    class Meta:
        model = Post
        fields = ['post_id', 'title', 'description', 'collection', 'views', 'owner']


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['post_id', 'title', 'description', 'content', 'thumbnail', 'is_private', 'collection', 'collection_name', 'views', 'likes_count', 'liked_status', 'created_at', 'owner']

    content = RichTextField()
    collection_name = serializers.StringRelatedField(source='collection', read_only=True)
    views = serializers.IntegerField(read_only=True)
    liked_status = serializers.SerializerMethodField(read_only=True, method_name='get_liked_status')
    likes_count = serializers.IntegerField(read_only=True)
    owner = SimpleUserSerializer(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    def get_liked_status(self, post: Post) -> bool:
        if hasattr(post, 'liked') and post.liked is True:
            return True
        return False

    def create(self, validated_data):
        owner_id = self.context['owner_id']
        if validated_data.get('is_private') == False:
            validated_data['is_private'] = True
            validated_data['status'] = Post.REQUESTED
        return Post.objects.create(owner_id=owner_id, **validated_data)
    
    def update(self, instance, validated_data):
        if 'thumbnail' not in validated_data:
            validated_data['thumbnail'] = instance.thumbnail

        if instance.title != validated_data['title'] \
            or instance.description != validated_data['description'] \
            or instance.content != validated_data['content'] \
            or instance.thumbnail != validated_data['thumbnail'] \
            or instance.is_private != validated_data['is_private']:

            if validated_data.get('is_private') == True and instance.status in [Post.APPROVED, Post.REQUESTED, Post.DECLINED]:
                validated_data['status'] = Post.NOT_REQUESTED

            if validated_data.get('is_private') != True:
                validated_data['is_private'] = True
                validated_data['status'] = Post.REQUESTED

        return super().update(instance, validated_data)
    

class SavedPostSerializer(serializers.ModelSerializer):
    post = PostSerializer()  

    class Meta:
        model = SavedPost
        fields = ('id', 'user', 'post', 'created_at')
