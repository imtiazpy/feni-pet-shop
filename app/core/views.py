from django.http import HttpResponseForbidden
from django.template import loader

def custom_permission_denied_view(request, exception):
    template = loader.get_template('403.html')
    print("==========================")
    return HttpResponseForbidden(template.render({'exception': exception}, request))