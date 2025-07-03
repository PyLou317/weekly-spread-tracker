

import pandas as pd
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .forms import ReportUploadForm
from datetime import datetime
import os
from typing import Type
from candidates.models import Candidate


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
            # Try different encodings for CSV files with more aggressive BOM handling
            encodings = [
                'utf-8-sig', 'utf-16', 'utf-16le', 'utf-16be', 
                'utf-8', 'latin-1', 'cp1252', 'iso-8859-1'
            ]
            df = None
            for encoding in encodings:
                try:
                    print(f"Trying encoding: {encoding}")
                    # Try with pandas-compatible error handling
                    try:
                        # For newer pandas versions
                        df = pd.read_csv(
                            file_path, 
                            encoding=encoding,
                            skipinitialspace=True,
                            on_bad_lines='skip',
                            sep=None,  # Let pandas auto-detect separator
                            engine='python'  # More flexible parser
                        )
                    except TypeError:
                        # For older pandas versions
                        df = pd.read_csv(
                            file_path, 
                            encoding=encoding,
                            skipinitialspace=True,
                            on_bad_lines='skip',  # Skips bad lines
                            sep=None,
                            engine='python'
                        )
                    
                    # Check if we got reasonable columns
                    if len(df.columns) > 1 and not any('ÿþ' in str(col) for col in df.columns):
                        print(f"Successfully read with encoding: {encoding}")
                        break
                    else:
                        df = None
                        
                except (UnicodeDecodeError, pd.errors.ParserError) as e:
                    print(f"Failed with encoding {encoding}: {str(e)}")
                    continue
                    
            if df is None:
                raise Exception("Could not decode CSV file with any supported encoding")
        else:
            df = pd.read_excel(file_path)
    except Exception as e:
        raise Exception(f"Could not read file: {str(e)}") from None
    
    # Print original columns for debugging
    print(f"Original columns: {list(df.columns)}")
    
    # Clean column names - remove BOM characters and normalize
    df.columns = [str(col).replace('ÿþ', '').replace('\ufeff', '').strip() for col in df.columns]
    df.columns = [col.lower().replace(' ', '_') for col in df.columns]
    
    print(f"Cleaned columns: {list(df.columns)}")
    
    # Expected columns (adjust based on actual report format)
    expected_columns = [
        'candidate_name', 'client_name', 'contract_start_date',
        'contract_end_date', 'weekly_spread_amount', 'recruiter_or_account_manager'
    ]
    
    # Try to map actual columns to expected columns
    column_mapping = {}
    for expected_col in expected_columns:
        for actual_col in df.columns:
            # Flexible matching for common variations
            if expected_col == 'candidate_name':
                if any(word in actual_col for word in ['contractor', 'candidate',
                                                       'employee', 'worker', 'name'
                                                      ]):
                    column_mapping[expected_col] = actual_col
                    break
            elif expected_col == 'client_name':
                if any(word in actual_col for word in ['customer', 'client']):
                    column_mapping[expected_col] = actual_col
                    break
            elif expected_col == 'contract_start_date':
                if any(word in actual_col for word in ['start', 'begin',
                                                'commence']) and 'date' in actual_col:
                    column_mapping[expected_col] = actual_col
                    break
            elif expected_col == 'contract_end_date':
                if any(word in actual_col for word in ['end', 'finish', 
                            'complete', 'weekending']) and 'date' in actual_col:
                    column_mapping[expected_col] = actual_col
                    break
            elif expected_col == 'weekly_spread_amount':
                if any(word in actual_col for word in ['spread',
                                    'expected_net_spread', 'net_spread', 'amount']):
                    column_mapping[expected_col] = actual_col
                    break
            elif expected_col == 'recruiter_or_account_manager':
                if any(word in actual_col for word in ['recruiter', 'account', 'manager', 'am']):
                    column_mapping[expected_col] = actual_col
                    break
    
    print(f"Column mapping: {column_mapping}")
    
    # Check if we have essential columns
    if 'candidate_name' not in column_mapping or 'client_name' not in column_mapping:
        # If no mapping found, print available columns for user reference
        raise Exception(f"Could not find required columns. Available columns: {list(df.columns)}. Please ensure your file has candidate name and client name columns.")
    
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
    print(f"Processing {len(df)} rows from report")
    print(f"Columns found: {list(df.columns)}")
    
    for index, row in df.iterrows():
        try:
            # Use column mapping to get the right values
            candidate_name = str(row.get(column_mapping.get('candidate_name', 'candidate_name'), '')).strip()
            client_name = str(row.get(column_mapping.get('client_name', 'client_name'), '')).strip()
            
            print(f"Processing row {index + 1}: '{candidate_name}' - '{client_name}'")
            
            if not candidate_name or not client_name or candidate_name == 'nan' or client_name == 'nan':
                print(f"Skipping row {index + 1} due to missing name data")
                continue
                
            report_candidates.add((candidate_name, client_name))
            
            # Check if candidate already exists
            existing_candidate = Candidate.objects.filter(
                user=user,
                candidate_name__iexact=candidate_name,
                client_name__iexact=client_name,
                status='active'
            ).first()
            
            # Parse dates with better error handling using column mapping
            try:
                start_date_col = column_mapping.get('contract_start_date', 'contract_start_date')
                end_date_col = column_mapping.get('contract_end_date', 'contract_end_date')
                spread_col = column_mapping.get('weekly_spread_amount', 'weekly_spread_amount')
                recruiter_col = column_mapping.get('recruiter_or_account_manager', 'recruiter_or_account_manager')
                
                # For weekly spread reports, we might not have contract start/end dates
                if start_date_col in row and pd.notna(row.get(start_date_col)):
                    start_date = pd.to_datetime(row.get(start_date_col), errors='coerce')
                else:
                    # Default to beginning of current year if no start date
                    start_date = pd.to_datetime(f"{datetime.now().year}-01-01")
                
                if end_date_col in row and pd.notna(row.get(end_date_col)):
                    end_date = pd.to_datetime(row.get(end_date_col), errors='coerce')
                else:
                    # Default to end of current year if no end date
                    end_date = pd.to_datetime(f"{datetime.now().year}-12-31")
                
                # Check if dates are valid
                if pd.isna(start_date) or pd.isna(end_date):
                    print(f"Skipping row due to invalid dates: {candidate_name} - {client_name}")
                    print(f"Start date: {row.get(start_date_col)}, End date: {row.get(end_date_col)}")
                    continue
                    
                # Parse weekly spread amount
                weekly_spread = row.get(spread_col, 0)
                if pd.isna(weekly_spread):
                    weekly_spread = 0
                
                candidate_data = {
                    'candidate_name': candidate_name,
                    'client_name': client_name,
                    'contract_start_date': start_date.date(),
                    'contract_end_date': end_date.date(),
                    'weekly_spread_amount': float(weekly_spread),
                    'recruiter_or_account_manager': str(row.get(recruiter_col, '')).strip(),
                }
            except Exception as e:
                print(f"Error parsing row data for {candidate_name} - {client_name}: {str(e)}")
                continue
            
            if existing_candidate:
                # Update existing candidate
                for field, value in candidate_data.items():
                    setattr(existing_candidate, field, value)
                existing_candidate.save()
                updated_candidates += 1
                print(f"Updated existing candidate: {candidate_name}")
            else:
                # Create new candidate
                new_candidate = Candidate.objects.create(
                    user=user,
                    status='active',
                    **candidate_data
                )
                new_candidates += 1
                print(f"Created new candidate: {candidate_name} (ID: {new_candidate.pk})")
                
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

