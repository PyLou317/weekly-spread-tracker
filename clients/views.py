
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError
from .models import Client
from .forms import ClientForm


@login_required
def client_list(request):
    clients = Client.objects.filter(user=request.user)
    return render(request, 'clients/list.html', {'clients': clients})


@login_required
def client_create(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            try:
                client = form.save(commit=False)
                client.user = request.user
                client.save()
                messages.success(request, f'Client "{client.name}" added successfully!')
                return redirect('clients:list')
            except IntegrityError:
                messages.error(request, 'A client with this name already exists.')
    else:
        form = ClientForm()
    
    return render(request, 'clients/form.html', {
        'form': form,
        'title': 'Add New Client',
        'submit_text': 'Add Client'
    })


@login_required
def client_edit(request, pk):
    client = get_object_or_404(Client, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f'Client "{client.name}" updated successfully!')
                return redirect('clients:list')
            except IntegrityError:
                messages.error(request, 'A client with this name already exists.')
    else:
        form = ClientForm(instance=client)
    
    return render(request, 'clients/form.html', {
        'form': form,
        'title': 'Edit Client',
        'submit_text': 'Update Client',
        'client': client
    })


@login_required
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk, user=request.user)
    
    if request.method == 'POST':
        client_name = client.name
        client.delete()
        messages.success(request, f'Client "{client_name}" deleted successfully!')
        return redirect('clients:list')
    
    return render(request, 'clients/confirm_delete.html', {'client': client})
