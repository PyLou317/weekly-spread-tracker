
import pandas as pd
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from candidates.models import Candidate
from .forms import ReportUploadForm
from datetime import datetime
import os


@login_required
def upload_report(request):
    if request.method == 'POST':
        form = ReportUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['report_file']
            
            # Save the file temporarily
            file_name = default_storage.save(f'temp/{uploaded_file.name}', ContentFile(uploaded_file.read()))
            file_path = default_storage.path(file_name)
            
            try:
                # Process the uploaded report
                result = process_report(file_path, request.user)
                
                # Clean up the temporary file
                default_storage.delete(file_name)
                
                messages.success(request, f"Report processed successfully! {result['message']}")
                return redirect('dashboard:dashboard')
                
            except Exception as e:
                # Clean up the temporary file on error
                default_storage.delete(file_name)
                messages.error(request, f"Error processing report: {str(e)}")
                
    else:
        form = ReportUploadForm()
    
    return render(request, 'reports/upload.html', {'form': form})


def process_report(file_path, user):
    """Process the uploaded CSV/Excel report"""
    try:
        # Try to read as CSV first, then Excel
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
    except Exception as e:
        raise Exception(f"Could not read file: {str(e)}")
    
    # Expected columns (adjust based on actual report format)
    expected_columns = [
        'candidate_name', 'client_name', 'contract_start_date',
        'contract_end_date', 'weekly_spread_amount', 'recruiter_or_account_manager'
    ]
    
    # Check if required columns exist (case-insensitive)
    df.columns = df.columns.str.lower().str.replace(' ', '_')
    
    new_candidates = 0
    updated_candidates = 0
    moved_to_review = 0
    
    # Get existing active candidates for this user
    existing_candidates = set(
        Candidate.objects.filter(user=user, status='active').values_list(
            'candidate_name', 'client_name'
        )
    )
    
    # Track candidates found in the report
    report_candidates = set()
    
    # Process each row in the report
    for _, row in df.iterrows():
        try:
            candidate_name = str(row.get('candidate_name', '')).strip()
            client_name = str(row.get('client_name', '')).strip()
            
            if not candidate_name or not client_name:
                continue
                
            report_candidates.add((candidate_name, client_name))
            
            # Check if candidate already exists
            existing_candidate = Candidate.objects.filter(
                user=user,
                candidate_name__iexact=candidate_name,
                client_name__iexact=client_name,
                status='active'
            ).first()
            
            candidate_data = {
                'candidate_name': candidate_name,
                'client_name': client_name,
                'contract_start_date': pd.to_datetime(row.get('contract_start_date')).date(),
                'contract_end_date': pd.to_datetime(row.get('contract_end_date')).date(),
                'weekly_spread_amount': float(row.get('weekly_spread_amount', 0)),
                'recruiter_or_account_manager': str(row.get('recruiter_or_account_manager', '')).strip(),
            }
            
            if existing_candidate:
                # Update existing candidate
                for field, value in candidate_data.items():
                    setattr(existing_candidate, field, value)
                existing_candidate.save()
                updated_candidates += 1
            else:
                # Create new candidate
                Candidate.objects.create(
                    user=user,
                    status='active',
                    **candidate_data
                )
                new_candidates += 1
                
        except Exception as e:
            continue  # Skip problematic rows
    
    # Move candidates not in the report to review queue
    candidates_not_in_report = existing_candidates - report_candidates
    for candidate_name, client_name in candidates_not_in_report:
        Candidate.objects.filter(
            user=user,
            candidate_name=candidate_name,
            client_name=client_name,
            status='active'
        ).update(status='review')
        moved_to_review += 1
    
    return {
        'message': f"Added {new_candidates} new candidates, updated {updated_candidates} existing candidates, moved {moved_to_review} to review queue."
    }
