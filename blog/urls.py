from django.urls import include, path
from rest_framework.routers import DefaultRouter 
from . import views

# router = DefaultRouter()
# router.register('blog', views.PostViewSet, basename='posts')
# router.register('blog/detail', views.PostViewSet, basename='post-detail')
# router.register('popular', views.PopularPostViewSet, basename='popular-post')

router = DefaultRouter()
router.register('blog', views.PostListViewSet, basename='posts')
router.register('domain', views.CollectionViewSet, basename='collections')
router.register('blog/detail', views.PostDetailViewSet, basename='post-detail')
router.register('blog/popular', views.PopularPostViewSet, basename='post-popular')
router.register('blog/owns', views.OwnPostViewSet, basename='post-owns')
router.register('blog/followed', views.FollowingsPostViewSet, basename='post-following')
router.register('users/follow', views.FollowViewSet, basename='user-following')
router.register('users/follower', views.FollowerViewSet, basename='user-followers')

urlpatterns = [
    path('', include(router.urls)),
]