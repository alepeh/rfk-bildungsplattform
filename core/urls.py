from django.urls import include, path
from .views import views, checkout_view, orders_view

urlpatterns = [
    path('', views.index, name='index'),
    path('register/<int:id>/', views.register, name='register'),
    path('checkout/<int:schulungstermin_id>/',
         checkout_view.checkout,
         name='checkout'),
    path('confirm-order/', checkout_view.confirm_order, name='confirm_order'),
    path('order-confirmation/<int:bestellung_id>/',
         checkout_view.order_confirmation,
         name='order_confirmation'),
    path('terms-and-conditions/', views.terms_and_conditions, name='terms_and_conditions'),
    path('mitarbeiter', views.mitarbeiter, name='mitarbeiter'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('send-reminder/<int:pk>/', views.send_reminder, name='send_reminder'),
    path('meine_bestellungen/',
         orders_view.UserBestellungenListView.as_view(),
         name='order_list'),
]
