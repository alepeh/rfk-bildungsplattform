from django.urls import include, path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/<int:id>/', views.register, name='register'),
    path('mitarbeiter', views.manage_authors, name='mitarbeiter'),
    path('accounts/', include('django.contrib.auth.urls')),
]