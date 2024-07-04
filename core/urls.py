from django.urls import include, path
from .views import views, checkout_view

urlpatterns = [
    path('', views.index, name='index'),
    path('register/<int:id>/', views.register, name='register'),
    path('checkout/<int:schulungstermin_id>/', checkout_view.checkout, name='checkout'),
    path('mitarbeiter', views.mitarbeiter, name='mitarbeiter'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('send-reminder/<int:pk>/', views.send_reminder, name='send_reminder'),
]
