from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Contractor
from .forms import CandidateForm
from accounts.models import UserProfile


@login_required
def list_view(request):
    contractors = Contractor.objects.filter(user=request.user, status='active')
    user = UserProfile.objects.get(user=request.user)

    # Handle batch deletion
    if request.method == 'POST':
        action = request.POST.get('action')
        selected_candidates = request.POST.getlist('selected_candidates')

        if action == 'delete' and selected_candidates:
            deleted_count = Contractor.objects.filter(
                pk__in=selected_candidates,
                user=request.user
            ).delete()[0]
            messages.success(request, f'Successfully deleted {deleted_count} contractors.')
            return redirect('contractors:list')
        elif action == 'delete_all':
            deleted_count = Contractor.objects.filter(
                user=request.user,
                status='active'
            ).delete()[0]
            messages.success(request, f'Successfully deleted all {deleted_count} contractors.')
            return redirect('contractors:list')

    # Search functionality
    search = request.GET.get('search')
    if search:
        contractors = contractors.filter(
            contractor_name__icontains=search
        ) | contractors.filter(
            client_name__icontains=search
        )

    # Sorting functionality
    sort = request.GET.get('sort', 'created_at')
    order = request.GET.get('order', 'desc')
    allowed_sorts = [
        'contractor_id', 'contractor_name', 'client_name', 'contract_start_date', 
        'contract_end_date', 'recruiter_or_account_manager', 'status', 'weekly_spread_amount', 'created_at'
    ]
    if sort not in allowed_sorts:
        sort = 'created_at'
    order_prefix = '-' if order == 'desc' else ''
    contractors = contractors.order_by(f"{order_prefix}{sort}")

    # Pagination 
    per_page_options = [10, 20, 50, 100]
    try:
        # Sanitize the input to prevent a ValueError
        per_page = int(request.GET.get('per_page', 10))
        if per_page not in per_page_options:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
        
    paginator = Paginator(contractors, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'contractors/list.html', {
        'user': user,
        'page_obj': page_obj,
        'selected_per_page': per_page,
        'per_page_options': per_page_options,
        'search': search,
        'sort': sort,
        'order': order,
    })


@login_required
def detail_view(request, pk):
    candidate = get_object_or_404(Contractor, pk=pk, user=request.user)
    return render(request, 'contractors/detail.html', {'candidate': candidate})


@login_required
def create_view(request):
    if request.method == 'POST':
        form = CandidateForm(request.POST, user=request.user)
        if form.is_valid():
            contractor = form.save(commit=False)
            contractor.user = request.user
            contractor.save()
            messages.success(request, 'Contractor added successfully!')
            return redirect('contractors:list')
    else:
        form = CandidateForm(user=request.user)

    return render(request, 'contractors/form.html', {
        'form': form,
        'title': 'Add New Contractor',
        'submit_text': 'Add Contractor'
    })


@login_required
def edit_view(request, pk):
    candidate = get_object_or_404(Contractor, pk=pk, user=request.user)

    if request.method == 'POST':
        form = CandidateForm(request.POST, instance=candidate, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Contractor updated successfully!')
            return redirect('contractors:detail', pk=candidate.pk)
    else:
        form = CandidateForm(instance=candidate, user=request.user)

    return render(request, 'contractors/form.html', {
        'form': form,
        'title': 'Edit Contractor',
        'submit_text': 'Update Contractor',
        'candidate': candidate
    })


@login_required
def delete_view(request, pk):
    contractor = get_object_or_404(Contractor, pk=pk, user=request.user)

    if request.method == 'POST':
        contractor.delete()
        messages.success(request, 'Contractor deleted successfully!')
        return redirect('contractors:list')

    return render(request, 'contractors/delete.html', {'candidate': contractor})


@login_required
def review_queue_view(request):
    contractors = Contractor.objects.filter(user=request.user, status='review')

    if request.method == 'POST':
        action = request.POST.get('action')
        contractor_id = request.POST.get('candidate_id')
        contractor = get_object_or_404(Contractor, pk=contractor_id, user=request.user)

        if action == 'reactivate':
            contractor.status = 'active'
            contractor.save()
            messages.success(request, f'Reactivated {contractor.contractor_first_name} {contractor.contractor_last_name}')
        elif action == 'remove':
            contractor.status = 'inactive'
            contractor.save()
            messages.success(request, f'Removed {contractor.contractor_first_name} {contractor.contractor_last_name}')

        return redirect('contractors:review_queue')

    return render(request, 'contractors/review_queue.html', {'candidates': contractors})