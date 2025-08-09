from django.urls import path
from .views import (
  CustomLoginView, 
  CustomLogoutView, 
  ProfileView, 
  ProfileUpdateView, 
  PasswordChangeView, 
  PasswordChangeDoneView
)


app_name = 'users'

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/update/', ProfileUpdateView.as_view(), name='profile_update'),
    path('password/change/', PasswordChangeView.as_view(), name='password_change'),
    path('password/change/done/', PasswordChangeDoneView.as_view(), name='password_change_done'),
]