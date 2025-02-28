from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from .forms import ConsumerCreationForm


class SignUpView(CreateView):
    form_class = ConsumerCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/registration_form.html'
