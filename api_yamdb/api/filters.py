import django_filters.rest_framework as filter
from reviews.models import Title


class TitleFilterSet(filter.FilterSet):
    genre = filter.CharFilter(field_name='genre__slug')
    category = filter.CharFilter(field_name='category__slug')
    name = filter.CharFilter(lookup_expr='contains')

    class Meta:
        model = Title
        fields = 'genre', 'category', 'year', 'name'
