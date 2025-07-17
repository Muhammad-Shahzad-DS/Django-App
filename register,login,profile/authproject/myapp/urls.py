from django.urls import path
from myapp.views import VerifyEmailView
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),  # ✅ fixed here
    path('profile/', views.profile_view, name='profile'),
    path('logout/', views.logout_page, name='logout'),
    path('update/', views.update_profile, name='update'),
    path('delete-account/', views.delete_account, name='delete_account'),
    path('token-send/', views.token_send, name='token_send'),
    path('success/', views.success, name='success'),
    path('verify-email/<uidb64>/<token>/', VerifyEmailView.as_view(), name='verify-email')
    # path('media/fallback.png/', views.image, name='image'),
]
