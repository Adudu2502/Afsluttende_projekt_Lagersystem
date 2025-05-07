from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView, View, CreateView, UpdateView, DeleteView
from django.views import View
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from .forms import UserRegisterForm, InventoryItemForm
from .models import InventoryItem, Category
from inventory_management.settings import LOW_QUANTITY
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings

def is_admin(user):
    return user.groups.filter(name='Admin').exists()

def is_netværksafdeling(user):
    return user.groups.filter(name='Netværksafdeling').exists()

def is_kundeservice(user):
    return user.groups.filter(name='Kundeservice').exists()

class Index(TemplateView):
	template_name = 'inventory/index.html'
 
class Dashboard(LoginRequiredMixin, View):
    def get(self, request):
        items = InventoryItem.objects.all().order_by('id')
        low_inventory_items = InventoryItem.objects.filter(quantity__lte=LOW_QUANTITY)

        if low_inventory_items.exists():
            count = low_inventory_items.count()
            word = "items have" if count > 1 else "item has"
            messages.error(request, f'{count} {word} low inventory')

            for item in low_inventory_items:
                if not item.email_sent:
                    send_mail(
                        subject='Low Inventory Alert',
                        message=f'Produktet "{item.name}" har en lav lagerbeholdning (quantity: {item.quantity}).',
                        from_email=settings.EMAIL_HOST_USER,
                        recipient_list=[settings.INVENTORY_ALERT_EMAIL],
                        fail_silently=False,
                    )
                    item.email_sent = True
                    item.save()
        else:
            # Reset email_sent for all items if none are low anymore
            InventoryItem.objects.filter(email_sent=True).update(email_sent=False)

        low_inventory_ids = list(low_inventory_items.values_list('id', flat=True))

        return render(request, 'inventory/dashboard.html', {'items': items, 'low_inventory_ids': low_inventory_ids})


class SignUpView(View):
	def get(self, request):
		form = UserRegisterForm()
		return render(request, 'inventory/signup.html', {'form': form})

def post(self, request):
	form = UserRegisterForm(request.POST)

	if form.is_valid():
		form.save()
		user = authenticate(
			username=form.cleaned_data['username'],
			password=form.cleaned_data['password1']
		)

		login(request, user)
		return redirect('index')

	return render(request, 'inventory/signup.html', {'form': form})

class CustomLoginView(LoginView):
    def get(self, request, *args, **kwargs):
        # Ryd gamle beskeder (fx logout-beskeder)
        storage = messages.get_messages(request)
        for _ in storage:
            pass
        return super().get(request, *args, **kwargs)

class CustomLogoutView(View):
    def get(self, request):
        logout(request)
        messages.success(request, "You have been logged out.")
        return render(request, 'inventory/logout.html')
    
    def post(self, request):
        logout(request)
        messages.success(request, "You have been logged out.")
        return render(request, 'inventory/logout.html')
 
@method_decorator(user_passes_test(lambda u: is_admin(u) or is_netværksafdeling(u)), name='dispatch')
class AddItem(LoginRequiredMixin, CreateView):
    model = InventoryItem
    form_class = InventoryItemForm
    template_name = 'inventory/item_form.html'
    success_url = reverse_lazy('dashboard')
     
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context
     
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

@method_decorator(user_passes_test(lambda u: is_admin(u) or is_netværksafdeling(u) or is_kundeservice(u)), name='dispatch') 
class EditItem(LoginRequiredMixin, UpdateView):
    model = InventoryItem
    form_class = InventoryItemForm
    template_name = 'inventory/item_form.html'
    success_url = reverse_lazy('dashboard')

@method_decorator(user_passes_test(lambda u: is_admin(u) or is_netværksafdeling(u)), name='dispatch')
class DeleteItem(LoginRequiredMixin, DeleteView):
    model = InventoryItem
    template_name = 'inventory/delete_item.html'
    success_url = reverse_lazy('dashboard')
    context_object_name = 'item'