from django.contrib.auth.tokens import default_token_generator
from django.db.models import Avg
from django.db.utils import IntegrityError
from django.shortcuts import get_object_or_404

from rest_framework import filters, status, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from reviews.models import Category, Genre, Review, Title, User

from django_filters.rest_framework import DjangoFilterBackend

from .filters import TitleFilterSet
from .permissions import (
    IsAdmin,
    ReadOnlyOrAdmin,
    AuthorOrModeratorOrAdminOrReadOnly
)
from .serializers import (
    ForAdminSerializer, UserSerializerOrReadOnly,
    SignupSerializer, TokenSerializer,
    OutputTitleSerializer, InputTitleSerializer,
    CategorySerializer, GenreSerializer,
    ReviewSerializer, CommentSerializer,
)
from .utils import send_confirmation_code

OCCUPIED_EMAIL_OR_USERNAME = 'Электронная почта или имя пользователя занято'

REVIEW_ERROR = 'Нельзя создать два ревью на одно произведение'
INVALID_TOKEN = 'Неверный токен'


class SignUp(APIView):
    permission_classes = AllowAny,

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user, created = User.objects.get_or_create(
                email=serializer.validated_data.get('email'),
                username=serializer.validated_data.get('username'),
            )
            if created:
                user.is_active = False
                user.save()
        except IntegrityError:
            raise ValidationError(OCCUPIED_EMAIL_OR_USERNAME)
        send_confirmation_code(user, request.data['email'])
        return Response(serializer.data, status=status.HTTP_200_OK)


class APIToken(APIView):
    permission_classes = AllowAny,

    def post(self, request):
        serializer = TokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(
            User,
            username=serializer.validated_data['username']
        )
        if not default_token_generator.check_token(
                user, serializer.validated_data['confirmation_code']):
            response = {'confirmation_code': INVALID_TOKEN}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = True
        user.save()
        token = RefreshToken.for_user(user)
        response = {
            'token': str(token.access_token),
        }
        return Response(response)


class UserViewSet(viewsets.ModelViewSet):
    """API для работы пользователями"""

    lookup_field = 'username'
    queryset = User.objects.all()
    serializer_class = ForAdminSerializer
    permission_classes = (IsAdmin,)
    pagination_class = PageNumberPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ('username',)

    @action(
        detail=False,
        methods=['get', 'patch'],
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        """
        Запрос и возможность редактирования
        информации профиля пользователя.
        """
        user = get_object_or_404(User, username=request.user.username)
        if request.method == 'GET':
            serializer = UserSerializerOrReadOnly(user, many=False)
            return Response(serializer.data)
        if request.method == 'PATCH':
            serializer = UserSerializerOrReadOnly(
                user,
                data=request.data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)


class TitleInfoViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                       viewsets.GenericViewSet):
    permission_classes = ReadOnlyOrAdmin,
    pagination_class = PageNumberPagination
    filter_backends = filters.SearchFilter,
    search_fields = 'name',

    @action(methods=['delete'], url_path=r'(?P<slug>\w+)', detail=False)
    def destroy_object(self, *args, **kwargs):
        get_object_or_404(
            self.get_queryset(),
            slug=kwargs.get('slug')
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CategoryViewSet(TitleInfoViewSet):
    serializer_class = CategorySerializer
    queryset = Category.objects.all()


class GenreViewSet(TitleInfoViewSet):
    serializer_class = GenreSerializer
    queryset = Genre.objects.all()


class TitleViewSet(viewsets.ModelViewSet):
    permission_classes = ReadOnlyOrAdmin,
    pagination_class = PageNumberPagination
    filter_backends = DjangoFilterBackend,
    filterset_class = TitleFilterSet

    def get_queryset(self):
        return Title.objects.annotate(rating=Avg('reviews__score'))

    def get_serializer_class(self):
        if self.request._request.method in SAFE_METHODS:
            return OutputTitleSerializer
        return InputTitleSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = AuthorOrModeratorOrAdminOrReadOnly,

    def get_queryset(self):
        return get_object_or_404(
            Title,
            id=self.kwargs.get('title_id')
        ).reviews.all()

    def perform_create(self, serializer):
        title = get_object_or_404(Title, id=self.kwargs.get('title_id'))
        if title.reviews.filter(author=self.request.user).exists():
            raise ValidationError(REVIEW_ERROR)
        serializer.save(author=self.request.user, title=title)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = AuthorOrModeratorOrAdminOrReadOnly,

    def get_queryset(self):
        return get_object_or_404(
            Review,
            id=self.kwargs.get('review_id')
        ).comments.all()

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
            review=get_object_or_404(
                Review,
                id=self.kwargs.get('review_id')
            )
        )
