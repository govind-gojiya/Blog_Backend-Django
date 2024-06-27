from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models import ExpressionWrapper, BooleanField, Value, Q, Subquery, OuterRef, Case, FloatField, When
from django.db.models.functions import Cast
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from hitcount.models import HitCount
from hitcount.utils import get_hitcount_model
from hitcount.views import HitCountMixin
from rest_framework import serializers, status, filters
from rest_framework.mixins import ListModelMixin, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, SAFE_METHODS
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet, ViewSet
from .filters import PostFilter, OwnPostFilter
from .models import Post, SavedPost, Collection, Follow
from .pagination import PostPagination, PopularPostPagination, FollowListPagination
from .permissions import IsOwnerOrReadOnly
from .serializers import PostSerializer, SimplePostSerializer, CollectionSerializer, SimpleUserSerializer, FollowUserSerializer, FollowSerializer

User = get_user_model()

class PostListViewSet(ListModelMixin, CreateModelMixin, GenericViewSet):
    serializer_class = PostSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = PostFilter
    pagination_class = PostPagination
    search_fields = ['title', 'description']

    def get_queryset(self):
        queryset = Post.objects \
                        .select_related('owner', 'collection') \
                        .annotate(views=Subquery(HitCount.objects.filter(content_type=ContentType.objects.get_for_model(Post), object_pk=OuterRef('pk')).values('hits'))) \
                        .order_by('-created_at', '-updated_at') \
        
        if self.request.user.is_authenticated:
            return queryset.filter(Q(is_private=False) | Q(owner=self.request.user))
        
        return queryset.filter(is_private=False)
    
    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return SimplePostSerializer
        return PostSerializer

    def get_serializer_context(self):
        if self.request.user.is_authenticated:
            return {
                'owner_id': self.request.user.id,
                'request': self.request
            }
        return {'request': self.request}

    def get_permissions(self):
        if self.request.method not in SAFE_METHODS:
            permission_classes = [IsAuthenticated()]  
        else:
            permission_classes = []  
        return permission_classes

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def get_saved_posts(self, request, pk=None):
        post = self.get_queryset()
        saved_posts = post.prefetch_related('savedpost').filter(savedpost__user__pk=request.user.id)
        collection_param = request.query_params.get('collection')
        if collection_param:
            saved_posts = saved_posts.filter(collection=collection_param)
        serializer = PostSerializer(saved_posts, many=True, context={'request': request}) 
        return Response(serializer.data)


class PostDetailViewSet(RetrieveModelMixin,
                   UpdateModelMixin,
                   DestroyModelMixin,
                   GenericViewSet):
    serializer_class = PostSerializer
    count_hit=True
    
    def get_object(self):
        obj =  super().get_object()
        object = get_object_or_404(Post, pk=obj.pk)
        context = {}
        hit_count = get_hitcount_model().objects.get_for_object(object)
        hits = hit_count.hits
        hitcontext = context['hitcount'] = {'pk': hit_count.pk}
        hit_count_response = HitCountMixin.hit_count(self.request, hit_count)
        if hit_count_response.hit_counted:
            hits = hits + 1
            obj.views = obj.views + 1 if obj.views else 1
        hitcontext['hit_counted'] = hit_count_response.hit_counted
        hitcontext['hit_message'] = hit_count_response.hit_message
        hitcontext['total_hits'] = hits
        return obj

    def get_queryset(self):
        queryset = Post.objects \
                        .select_related('owner', 'collection') \
                        .prefetch_related('liked_by') \
                        .annotate(views=Subquery(HitCount.objects.filter(content_type=ContentType.objects.get_for_model(Post), object_pk=OuterRef('pk')).values('hits'))) 

        if self.request.user.is_authenticated:
            liked_post_ids = Subquery(User.objects.filter(pk=self.request.user.id).values_list('liked_posts__post_id', flat=True))
            user_liked_post = ExpressionWrapper(Q(pk__in=liked_post_ids), output_field=BooleanField())
            queryset = queryset.annotate(liked=user_liked_post)
            return queryset.filter(Q(is_private=False) | Q(owner=self.request.user))
        else:
            return queryset.filter(is_private=False)  

    def get_serializer_context(self):
        if self.request.user.is_authenticated:
            return {
                'owner_id': self.request.user.id,
                'request': self.request
            }
        return {'request': self.request}

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated(), IsOwnerOrReadOnly()]  
        elif self.request.method not in SAFE_METHODS:
            permission_classes = [IsAuthenticated()]  
        else:
            permission_classes = []  
        return permission_classes
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        post = self.get_object()
        user = request.user

        if post.liked:
            post.liked_by.remove(user)
            post.likes_count -= 1
            post.save()
            liked = False
        else:
            post.liked_by.add(user)
            post.likes_count += 1
            post.save()
            liked = True

        return Response({'liked': liked}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def save_post(self, request, pk=None):
        user = request.user
        post = self.get_object()

        if SavedPost.objects.filter(user=user, post=post).exists():
            return Response({'message': 'Post already saved'}, status=status.HTTP_400_BAD_REQUEST)

        if hasattr(self, 'save_post_to_user'):  
            self.save_post_to_user(user, post)
        else:
            SavedPost.objects.create(user=user, post=post)

        return Response({'message': 'Post saved successfully'}, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsOwnerOrReadOnly])
    def request_to_public(self, request, pk=None):
        post = self.get_object()

        if post.status == Post.REQUESTED:
            return Response({'message': 'Request already registerd, wait for approval.'}, status=status.HTTP_201_CREATED)

        post.status = Post.REQUESTED
        post.save()
        return Response({'message': 'Request registerd, we let you know soon.'}, status=status.HTTP_201_CREATED)


class PopularPostViewSet(ListModelMixin, GenericViewSet):
    serializer_class = SimplePostSerializer
    pagination_class = PopularPostPagination

    def get_queryset(self):
        queryset = Post.objects.select_related('owner', 'collection') \
            .filter(Q(is_private=False) | Q(owner=self.request.user)) \
            .annotate(views=Subquery(HitCount.objects.filter(content_type=ContentType.objects.get_for_model(Post), object_pk=OuterRef('pk')).values('hits'))) \
            .annotate(
                ratio=Case(
                    When(Q(views__gt=0), then=Cast('likes_count', FloatField()) / Cast('views', FloatField())),
                    output_field=FloatField(),
                    default=0,
                )
            ).order_by('-ratio')

        return queryset

    def get_serializer_context(self):
        if self.request.user.is_authenticated:
            return {
                'owner_id': self.request.user.id,
                'request': self.request
            }
        return {'request': self.request}
    

class OwnPostViewSet(ListModelMixin, GenericViewSet):
    serializer_class = SimplePostSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = OwnPostFilter
    pagination_class = PostPagination
    search_fields = ['title', 'description']

    def get_queryset(self):
        return Post.objects.select_related('owner', 'collection') \
            .filter(owner=self.request.user) \
            .annotate(views=Subquery(HitCount.objects.filter(content_type=ContentType.objects.get_for_model(Post), object_pk=OuterRef('pk')).values('hits'))) \
            .order_by('-created_at', '-updated_at')
    

class CollectionViewSet(ListModelMixin, GenericViewSet):
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer


class FollowViewSet(ListModelMixin, 
                      CreateModelMixin,
                      DestroyModelMixin,
                    #   RetrieveModelMixin,
                      GenericViewSet):
    queryset = Follow.objects.all()
    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = FollowListPagination

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return SimpleUserSerializer
        return FollowSerializer

    def get_serializer_context(self):
        return {'request': self.request}

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        follow_data = serializer.validated_data
        follower = request.user
        following_user_id = follow_data['following'].id  

        if follower.id == following_user_id:
            return Response({'message': "You can't follow yourself."}, status=status.HTTP_409_CONFLICT)
        
        if Follow.objects.filter(follower=follower, following=following_user_id).exists():
            return Response({'message': 'You are already following this user.'}, status=status.HTTP_409_CONFLICT)

        follow = Follow.objects.create(follower=follower, following_id=following_user_id)
        serializer = self.get_serializer(follow)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None, *args, **kwargs):
        try:
            follow = Follow.objects.get(follower=request.user, following_id=pk)
        except Follow.DoesNotExist:
            return Response({'message': 'Follow not found.'}, status=status.HTTP_404_NOT_FOUND)

        if follow.follower != request.user:
            return Response({'message': 'You can not remove follows for other users.'}, status=status.HTTP_403_FORBIDDEN)

        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def list(self, request, *args, **kwargs):
        following_id = self.get_queryset().filter(follower=self.request.user).values('following_id')
        queryset = User.objects.filter(pk__in=following_id)
        page = self.paginate_queryset(queryset)
        serializer = SimpleUserSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)
    
    # def retrieve(self, request, *args, **kwargs):
    #     queryset = self.get_queryset()
    #     if not queryset.filter(follower=request.user, following=kwargs['pk']).exists():
    #         return Response({'message': 'Not matching any following user.'}, status=status.HTTP_400_BAD_REQUEST)
    #     else:
    #         instance = User.objects.get(pk=kwargs['pk'])
    #         serializer = self.get_serializer(instance)
    #         return Response(serializer.data)
        

class FollowerViewSet(ListModelMixin, 
                      DestroyModelMixin,
                      GenericViewSet):
    queryset = Follow.objects.all()
    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = FollowListPagination

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return SimpleUserSerializer
        return FollowSerializer

    def get_serializer_context(self):
        return {'request': self.request}

    def destroy(self, request, pk=None, *args, **kwargs):
        try:
            follow = Follow.objects.get(follower_id=pk, following=request.user)
        except Follow.DoesNotExist:
            return Response({'message': 'Follower not found.'}, status=status.HTTP_404_NOT_FOUND)

        if follow.following != request.user:
            return Response({'message': 'Follower not found.'}, status=status.HTTP_403_FORBIDDEN)

        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def list(self, request, *args, **kwargs):
        following_id = self.get_queryset().filter(following=self.request.user).values('follower')
        queryset = User.objects.filter(pk__in=following_id)
        page = self.paginate_queryset(queryset)
        serializer = SimpleUserSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)
    

class FollowingsPostViewSet(ListModelMixin, GenericViewSet):
    serializer_class = SimplePostSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = PostFilter
    pagination_class = PostPagination
    permission_classes = [IsAuthenticated]
    search_fields = ['title', 'description']

    def get_queryset(self):
        following_users_id = Follow.objects.filter(follower=self.request.user).values('following_id')
        return Post.objects.select_related('owner', 'collection') \
            .filter(owner_id__in=following_users_id, is_private=False) \
            .annotate(views=Subquery(HitCount.objects.filter(content_type=ContentType.objects.get_for_model(Post), object_pk=OuterRef('pk')).values('hits'))) \
            .order_by('-created_at', '-updated_at')
    