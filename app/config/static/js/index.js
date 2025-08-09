document.addEventListener('DOMContentLoaded', function () {
  const toasts = document.querySelectorAll('.toast-message');
  toasts.forEach((toast) => {
    setTimeout(() => {
      toast.classList.add('opacity-0');
      setTimeout(() => toast.remove(), 500);
    }, 3000);
  });
});