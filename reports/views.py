

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
    
    # Required columns (only these are essential)
    required_columns = ['contractor_name', 'client_name', 'weekly_spread_amount']
    
    # Try to map actual columns to expected columns
    column_mapping = {}
    for actual_col in df.columns:
        # Explicitly look for contractor/candidate NAME fields (not ID fields)
        if (any(word in actual_col for word in ['contractor_name', 'candidate_name', 'employee_name', 'worker_name']) or
            (any(word in actual_col for word in ['contractor', 'candidate', 'employee', 'worker']) and 'name' in actual_col)):
            column_mapping['contractor_name'] = actual_col
        # Explicitly look for client/customer NAME fields (not ID fields)  
        elif (any(word in actual_col for word in ['customer_name', 'client_name']) or
              (any(word in actual_col for word in ['customer', 'client']) and 'name' in actual_col)):
            column_mapping['client_name'] = actual_col
        # Flexible matching for spread amount
        elif any(word in actual_col for word in ['spread', 'expected_net_spread', 'net_spread', 'amount']):
            column_mapping['weekly_spread_amount'] = actual_col
        # Optional fields (if they exist in the report)
        elif any(word in actual_col for word in ['start', 'begin', 'commence']) and 'date' in actual_col:
            column_mapping['contract_start_date'] = actual_col
        elif any(word in actual_col for word in ['end', 'finish', 'complete', 'weekending']) and 'date' in actual_col:
            column_mapping['contract_end_date'] = actual_col
        elif any(word in actual_col for word in ['recruiter', 'account', 'manager', 'am']):
            column_mapping['recruiter_or_account_manager'] = actual_col
    
    print(f"Column mapping: {column_mapping}")
    
    # Check if we have essential columns
    missing_columns = [col for col in required_columns if col not in column_mapping]
    if missing_columns:
        raise Exception(f"Could not find required columns: {missing_columns}. Available columns: {list(df.columns)}. Please ensure your file has contractor/candidate name, client/customer name, and spread amount columns.")
    
    new_candidates = 0
    updated_candidates = 0
    moved_to_review = 0
    
    # Get existing active candidates for this user
    existing_candidates = set(
        Candidate.objects.filter(user=user, status='active').values_list(
            'contractor_name', 'client_name'
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
            contractor_name = str(row.get(column_mapping.get('contractor_name', 'contractor_name'), '')).strip()
            client_name = str(row.get(column_mapping.get('client_name', 'client_name'), '')).strip()
            
            print(f"Processing row {index + 1}: '{contractor_name}' - '{client_name}'")
            
            if not contractor_name or not client_name or contractor_name == 'nan' or client_name == 'nan':
                print(f"Skipping row {index + 1} due to missing name data")
                continue
                
            report_candidates.add((contractor_name, client_name))
            
            # Check if candidate already exists
            existing_candidate = Candidate.objects.filter(
                user=user,
                contractor_name__iexact=contractor_name,
                client_name__iexact=client_name,
                status='active'
            ).first()
            
            # Parse data with defaults for missing fields
            try:
                # Parse weekly spread amount (required field)
                spread_col = column_mapping.get('weekly_spread_amount')
                weekly_spread = row.get(spread_col, 0)
                if pd.isna(weekly_spread):
                    weekly_spread = 0
                else:
                    # Clean currency formatting (remove $, commas, spaces)
                    weekly_spread = str(weekly_spread).replace('$', '').replace(',', '').strip()
                    try:
                        weekly_spread = float(weekly_spread)
                    except (ValueError, TypeError):
                        weekly_spread = 0
                
                # Set default dates for user to edit manually
                # Using today's date as a reasonable default
                start_date = datetime.now().date()
                end_date = datetime.now().date()
                
                # Get recruiter info if available
                recruiter = ''
                if 'recruiter_or_account_manager' in column_mapping:
                    recruiter_col = column_mapping['recruiter_or_account_manager']
                    recruiter = str(row.get(recruiter_col, '')).strip()
                
                candidate_data = {
                    'contractor_name': contractor_name,
                    'client_name': client_name,
                    'contract_start_date': start_date,
                    'contract_end_date': end_date,
                    'weekly_spread_amount': float(weekly_spread),
                    'recruiter_or_account_manager': recruiter,
                }
            except Exception as e:
                print(f"Error parsing row data for {contractor_name} - {client_name}: {str(e)}")
                continue
            
            if existing_candidate:
                # Update existing candidate
                for field, value in candidate_data.items():
                    setattr(existing_candidate, field, value)
                existing_candidate.save()
                updated_candidates += 1
                print(f"Updated existing candidate: {contractor_name}")
            else:
                # Create new candidate
                new_candidate = Candidate.objects.create(
                    user=user,
                    status='active',
                    **candidate_data
                )
                new_candidates += 1
                print(f"Created new candidate: {contractor_name} (ID: {new_candidate.pk})")
                
        except Exception as e:
            continue  # Skip problematic rows
    
    # Move candidates not in the report to review queue
    candidates_not_in_report = existing_candidates - report_candidates
    for contractor_name, client_name in candidates_not_in_report:
        Candidate.objects.filter(
            user=user,
            contractor_name=contractor_name,
            client_name=client_name,
            status='active'
        ).update(status='review')
        moved_to_review += 1
    
    return {
        'message': f"Added {new_candidates} new candidates, updated {updated_candidates} existing candidates, moved {moved_to_review} to review queue."
    }

