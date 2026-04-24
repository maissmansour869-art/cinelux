from django.urls import path

from .views import LoginView, PaymentMethodDetailView, PaymentMethodsView, RegisterView, UpdatePreferencesView, UserProfileView

urlpatterns = [
    path("register", RegisterView.as_view(), name="register"),
    path("login", LoginView.as_view(), name="login"),
    path("<uuid:user_id>", UserProfileView.as_view(), name="user-profile"),
    path("<uuid:user_id>/preferences", UpdatePreferencesView.as_view(), name="user-preferences"),
    path("<uuid:user_id>/payment-methods", PaymentMethodsView.as_view(), name="payment-methods"),
    path("<uuid:user_id>/payment-methods/<uuid:method_id>", PaymentMethodDetailView.as_view(), name="payment-method-detail"),
]
