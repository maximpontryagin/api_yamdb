from uuid import uuid4

from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.tokens import AccessToken

from api_yamdb.settings import ADMIN_EMAIL
from .serializers import SignUpSerializer, TokenSerializer
from user.models import User

from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
# from django.shortcuts import render
from .serializers import CommentSerializer, ReviewSerializer
from reviews.models import Review, Title

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.pagination import LimitOffsetPagination

from reviews.models import Title, Genre, Category
from .serializers import (TitleGETSerializer, TitleSerializer,
                          GenreSerializer, CategorySerializer,
                          UserSerializer)
from .permissions import (AnonimReadOnly, SuperUserOrAdminOnly,
                          AdminOrReadOnly, AuthUserOrReadOnly,
                          Moderator, ReviewOrCommentPermission, 
                          TitlePermission)
from user.models import User
# from .permissions import AdminOrReadOnly


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (SuperUserOrAdminOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)
    lookup_field = 'username'
    http_method_names = ['get', 'post', 'patch', 'delete']

    @action(methods=['get', 'patch'], detail=False, url_path='me',
            url_name='me', permission_classes=(IsAuthenticated,))
    def get_me_patch(self, request):
        if request.method == 'PATCH':
            serializer = UserSerializer(request.user,
                                        data=request.data,
                                        partial=True,
                                        context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save(role=request.user.role)
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    user = User.objects.filter(email=request.data.get('email'),
                               username=request.data.get('username'))
    if user.exists():
        create_and_send_confirmation_code_by_email(user)
        return Response(request.data, status=status.HTTP_200_OK)

    serializer = SignUpSerializer(data=request.data)
    if serializer.is_valid(raise_exception=True):
        serializer.save()
        user = User.objects.filter(email=serializer.data.get('email'),
                                   username=serializer.data.get('username'))
        create_and_send_confirmation_code_by_email(user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def token(request):
    serializer = TokenSerializer(data=request.data)
    #user = get_object_or_404(User, username=serializer.data.get('username'))
    if serializer.is_valid(raise_exception=True):
        user = get_object_or_404(User, username=serializer.data.get('username'))
        if request.data.get('confirmation_code') == user.confirmation_code:
            return Response(
                {'token': str(AccessToken.for_user(get_object_or_404(User, username=serializer.data.get('username'))))},
                status=status.HTTP_200_OK
            )
    return Response(
        'Неправильно указаны данные в запросе.',
        status=status.HTTP_400_BAD_REQUEST
    )


def create_and_send_confirmation_code_by_email(user):
    unique_token = uuid4()
    user.update(confirmation_code=str(unique_token))
    send_mail(
        subject='Код подтверждения',
        message='Ваш код подтверждения: {user.confirmation_code}',
        from_email=ADMIN_EMAIL,
        recipient_list=[user[0].email],
        fail_silently=True,
    )


class ReviewsViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    # permission_classes = [Moderator, AnonimReadOnly, SuperUserOrAdminOnly, AuthUserOrReadOnly)
    permission_classes = (ReviewOrCommentPermission,)
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        title = get_object_or_404(Title, id=self.kwargs['title_id'])
        return title.reviews.all()

    def perform_create(self, serializer):
        title_id = self.kwargs.get('title_id')
        title = get_object_or_404(Title, pk=title_id)
        serializer.save(author=self.request.user, title=title)


class CommentsViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = (ReviewOrCommentPermission,)

    def get_queryset(self):
        review = get_object_or_404(Review, id=self.kwargs['review_id'])
        return review.comments.all()

    def perform_create(self, serializer):
        review_id = self.kwargs['review_id']
        review = get_object_or_404(Review, pk=review_id)
        serializer.save(author=self.request.user, review=review)


class GenreViewSet(viewsets.ModelViewSet):
    """Получение, добавление, удаление жанра."""
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [AdminOrReadOnly]
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'


class CategoryViewSet(viewsets.ModelViewSet):
    """Получение, добавление, удаление категории."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (AdminOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'


class TitleViewSet(viewsets.ModelViewSet):
    """Получение, добавление, изменение и удаление произведения."""
    queryset = Title.objects.all()
    serializer_class = TitleSerializer
    permission_classes = [TitlePermission]
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('category__slug', 'genre__slug', 'name', 'year')
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        """Определяет какой сериализатор будет использоваться
        для разных типов запроса."""
        if self.action in ('list', 'retrieve'):
            return TitleGETSerializer
        return TitleSerializer

    def method_not_allowed(self, request):
        if request.method == 'PUT':
            serializer = TitleGETSerializer(request.user)
            return Response(
                serializer.data,
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )
