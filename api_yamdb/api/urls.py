from django.urls import include, path
from rest_framework import routers

from .views import (UserViewSet, ReviewViewSet,
                    CommentViewSet, TitleViewSet,
                    CategoryViewSet, GenreViewSet)

from api.views import APIToken, SignUp

router_v1 = routers.DefaultRouter()
router_v1.register('users', UserViewSet, basename='user')
router_v1.register('titles', TitleViewSet, basename='title')
router_v1.register('categories', CategoryViewSet, basename='category')
router_v1.register('genres', GenreViewSet, basename='genre')
router_v1.register(
    r'titles/(?P<title_id>\d+)/reviews',
    ReviewViewSet,
    basename='reviews')
router_v1.register(
    r'titles/(?P<titles_id>\d+)/reviews/(?P<review_id>\d+)/comments',
    CommentViewSet,
    basename='comments'
)

auth_urls = [
    path(
        'token/',
        APIToken.as_view(),
        name='token'
    ),
    path(
        'signup/',
        SignUp.as_view(),
        name='signup'
    ),
]

urlpatterns = [
    path('v1/', include(router_v1.urls)),
    path('v1/auth/', include(auth_urls)),
]
