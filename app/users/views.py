from django.shortcuts import render
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView, PasswordChangeDoneView
from django.views.generic.detail import DetailView
from django.views.generic import UpdateView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from .forms import ProfileUpdateForm

User = get_user_model()

class CustomLoginView(LoginView):
    """
    Custom login view to handle user authentication.
    """
    template_name = 'users/registration/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        role = self.request.user.role
        if role == 'admin':
            return reverse_lazy('dashboard:dashboard')
        elif role == 'cashier':
            return reverse_lazy('dashboard:cashier')
        elif role == 'inventory_manager':
            return reverse_lazy('dashboard:inventory_manager')
        elif role == 'veterinarian':
            return reverse_lazy('dashboard:veterinarian')
        return reverse_lazy('dashboard:home')

   
class CustomLogoutView(LogoutView):
    """
    Custom logout view to handle user logout.
    """
    next_page = reverse_lazy('users:login')



class ProfileView(LoginRequiredMixin, DetailView):
    """
    View to display user profile information.
    """
    model = User
    template_name = 'users/profile.html'
    context_object_name = 'user'

    def get_object(self, queryset=None):
        """
        Override to get the current user object.
        """
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.headers.get('HX-Request'):
            context['template_to_extend'] = 'partials/base_empty.html'
        else:
            context['template_to_extend'] = 'new_dash_base.html'
        return context
    

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """
    View to update user profile information.
    """
    model = User
    form_class = ProfileUpdateForm
    success_url = reverse_lazy('users:profile')
    template_name = 'users/profile_update.html'
    context_object_name = 'user'

    def get_object(self, queryset=None):
        """
        Override to get the current user object.
        """
        return self.request.user
    

class PasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    """
    View to change user password.
    """
    template_name = 'users/password_change.html'
    success_url = reverse_lazy('users:password_change_done')

    def form_valid(self, form):
        """
        Override to set the success URL after password change.
        """
        response = super().form_valid(form)
        messages.success(self.request, 'Your password was changed successfully.')
        return response
    

class PasswordChangeDoneView(LoginRequiredMixin, PasswordChangeDoneView):
    """
    View to display a message after password change.
    """
    template_name = 'users/password_change_done.html'

    