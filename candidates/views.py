
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Candidate
from .forms import CandidateForm


@login_required
def candidate_list(request):
    candidates = Candidate.objects.filter(user=request.user, status='active')
    
    # Search functionality
    search = request.GET.get('search')
    if search:
        candidates = candidates.filter(
            candidate_name__icontains=search
        ) | candidates.filter(
            client_name__icontains=search
        )
    
    paginator = Paginator(candidates, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'candidates/list.html', {
        'page_obj': page_obj,
        'search': search,
    })


@login_required
def candidate_detail(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk, user=request.user)
    return render(request, 'candidates/detail.html', {'candidate': candidate})


@login_required
def candidate_create(request):
    if request.method == 'POST':
        form = CandidateForm(request.POST)
        if form.is_valid():
            candidate = form.save(commit=False)
            candidate.user = request.user
            candidate.save()
            messages.success(request, 'Candidate added successfully!')
            return redirect('candidates:list')
    else:
        form = CandidateForm()
    
    return render(request, 'candidates/form.html', {
        'form': form,
        'title': 'Add New Candidate'
    })


@login_required
def candidate_edit(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = CandidateForm(request.POST, instance=candidate)
        if form.is_valid():
            form.save()
            messages.success(request, 'Candidate updated successfully!')
            return redirect('candidates:detail', pk=candidate.pk)
    else:
        form = CandidateForm(instance=candidate)
    
    return render(request, 'candidates/form.html', {
        'form': form,
        'title': 'Edit Candidate',
        'candidate': candidate
    })


@login_required
def candidate_delete(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk, user=request.user)
    
    if request.method == 'POST':
        candidate.delete()
        messages.success(request, 'Candidate deleted successfully!')
        return redirect('candidates:list')
    
    return render(request, 'candidates/delete.html', {'candidate': candidate})


@login_required
def review_queue(request):
    candidates = Candidate.objects.filter(user=request.user, status='review')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        candidate_id = request.POST.get('candidate_id')
        candidate = get_object_or_404(Candidate, pk=candidate_id, user=request.user)
        
        if action == 'reactivate':
            candidate.status = 'active'
            candidate.save()
            messages.success(request, f'Reactivated {candidate.candidate_name}')
        elif action == 'remove':
            candidate.status = 'inactive'
            candidate.save()
            messages.success(request, f'Removed {candidate.candidate_name}')
        
        return redirect('candidates:review_queue')
    
    return render(request, 'candidates/review_queue.html', {'candidates': candidates})
