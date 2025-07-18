from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from .models import Lga, Ward, PollingUnit, AnnouncedPuResults, AnnouncedLgaResults, Party
from .form import PollingUnitSelectionForm
from django.db.models import Sum
from django.contrib import messages
from django.utils import timezone


def api_lgas(request):
    state_id = request.GET.get('state_id')
    lgas = Lga.objects.filter(state_id=state_id).values('lga_id', 'lga_name')
    return JsonResponse(list(lgas), safe=False)

def api_wards(request):
    lga_id = request.GET.get('lga_id')
    wards = Ward.objects.filter(lga_id=lga_id).values('ward_id', 'ward_name')
    return JsonResponse(list(wards), safe=False)

def api_polling_units(request):
    ward_id = request.GET.get('ward_id')
    if ward_id:
        pus = PollingUnit.objects.filter(ward_id=ward_id).values('uniqueid', 'polling_unit_name')
        return JsonResponse(list(pus), safe=False)
    return JsonResponse({'error': 'Missing ward id'}, status=400)


# Home route
def home_view(request):
    return render(request, 'home.html')

# 1. Route to view any polling unit result
def polling_unit_result(request):
    state_id = request.GET.get('state')
    lga_id = request.GET.get('lga')
    ward_id = request.GET.get('ward')
    polling_unit_id = request.GET.get('polling_unit')

    form = PollingUnitSelectionForm(
        request.GET or None,
        state_id=state_id,
        lga_id=lga_id,
        ward_id=ward_id
    )

    results = None
    polling_unit_name = None

    if polling_unit_id:
        results = AnnouncedPuResults.objects.filter(polling_unit_uniqueid=polling_unit_id)
        try:
            polling_unit = PollingUnit.objects.get(uniqueid=polling_unit_id)
            polling_unit_name = polling_unit.polling_unit_name
        except PollingUnit.DoesNotExist:
            polling_unit_name = None

    return render(request, 'polling_unit_result.html', {
        'form': form,
        'results': results,
        'selected_pu': polling_unit_id,
        'polling_unit_name': polling_unit_name
    })


# 2. Route to view the sum of votes for all polling units in any polling unit

def lga_result(request):
    lga_id = request.GET.get('lga')
    lgas = Lga.objects.filter(state_id=25)
    parties = Party.objects.all()
    party_results = []
    official_results = []
    total_score = 0
    official_total_score = 0
    lga_name = None

    if lga_id:
        lga_obj = Lga.objects.filter(lga_id=lga_id).first()
        lga_name = lga_obj.lga_name if lga_obj else "Unknown LGA"

        polling_units = PollingUnit.objects.filter(lga_id=lga_id)
        pu_ids = polling_units.values_list('uniqueid', flat=True)

        party_results = (
            AnnouncedPuResults.objects
            .filter(polling_unit_uniqueid__in=pu_ids)
            .values('party_abbreviation')
            .annotate(total_score=Sum('party_score'))
        )
        total_score = sum(r['total_score'] for r in party_results)

        official_results = (
            AnnouncedLgaResults.objects
            .filter(lga_name=lga_id) 
            .values('party_abbreviation')
            .annotate(official_score=Sum('party_score'))
        )
        official_total_score = sum(r['official_score'] for r in official_results)

    return render(request, 'lga_result.html', {
        'lgas': lgas,
        'selected_lga': int(lga_id) if lga_id else None,
        'parties': parties,
        'party_results': party_results,
        'official_results': official_results,
        'total_score': total_score,
        'official_total_score': official_total_score,
        'lga_name': lga_name,
    })


# 3. Add All Party Results for a Polling Unit
def add_all_party_polling_unit_results(request):
    delta_state_id = 25

    lgas = Lga.objects.filter(state_id=delta_state_id).order_by('lga_name')
    parties = Party.objects.all().order_by('partyid')

    selected_lga_id = request.POST.get('lga') if request.method == 'POST' else None
    selected_ward_id = request.POST.get('ward') if request.method == 'POST' else None
    selected_pu_id = request.POST.get('polling_unit') if request.method == 'POST' else None

    wards = []
    polling_units = []

    if selected_lga_id:
        try:
            wards = Ward.objects.filter(lga_id=int(selected_lga_id)).order_by('ward_name')
        except ValueError:
            pass
    if selected_ward_id:
        try:
            polling_units = PollingUnit.objects.filter(ward_id=int(selected_ward_id)).order_by('polling_unit_name')
        except ValueError:
            pass


    if request.method == 'POST':
        pu_id = request.POST.get('polling_unit') 
        entered_by_user = request.POST.get('entered_by_user')

        if not pu_id or not entered_by_user:
            messages.error(request, "Polling Unit, and 'Entered By' user are required for submission.")
           
        else:
            try:
                polling_unit_obj = PollingUnit.objects.get(uniqueid=int(pu_id))
            except (PollingUnit.DoesNotExist, ValueError):
                messages.error(request, f"Error: Selected Polling Unit '{pu_id}' is invalid or does not exist.")
               
            else:
                date_entered = timezone.now()
                user_ip_address = request.META.get('REMOTE_ADDR')

                results_processed_count = 0
                for party in parties:
                    score_field_name = f'score_{party.partyid}'
                    party_score_str = request.POST.get(score_field_name)

                    if party_score_str is not None and party_score_str.strip() != '':
                        try:
                            party_score = int(party_score_str)
                            if party_score < 0:
                                messages.warning(request, f"Skipped {party.partyid}: Score must be non-negative.")
                                continue
                        except ValueError:
                            messages.warning(request, f"Skipped {party.partyid}: Invalid score entered for '{party.partyid}'.")
                            continue

                        original_party_abbreviation = party.partyid
                        desired_max_length = 4

                        processed_party_abbreviation = original_party_abbreviation[:desired_max_length]

                        try:
                            result, created = AnnouncedPuResults.objects.get_or_create(
                                polling_unit_uniqueid=polling_unit_obj,
                                party_abbreviation=processed_party_abbreviation,
                                defaults={
                                    'party_score': party_score,
                                    'entered_by_user': entered_by_user,
                                    'date_entered': date_entered,
                                    'user_ip_address': user_ip_address,
                                }
                            )

                            if not created:
                                old_score = result.party_score
                                if old_score != party_score:
                                    result.party_score = party_score
                                    result.entered_by_user = entered_by_user
                                    result.date_entered = date_entered
                                    result.user_ip_address = user_ip_address
                                    result.save()
                                    messages.info(request, f"Updated score for {party.partyid} at '{polling_unit_obj.polling_unit_name}': {old_score} -> {party_score}.")
                                    results_processed_count += 1
                            else:
                                messages.success(request, f"Added new score for {party.partyid} at '{polling_unit_obj.polling_unit_name}': {party_score}.")
                                results_processed_count += 1
                        
                        except Exception as ie:
                            messages.error(request, f"Error saving result for {original_party_abbreviation}: A similar abbreviation ({processed_party_abbreviation}) already exists for this polling unit. Consider reviewing party names or increasing max_length.")
                            print(f"IntegrityError: {ie} - Party: {original_party_abbreviation}, Sliced: {processed_party_abbreviation}")
                        except Exception as e:
                            messages.error(request, f"An unexpected error occurred while saving results for {original_party_abbreviation}: {e}")
                            print(f"Unexpected error: {e}")

                if results_processed_count > 0:
                    messages.success(request, f"Successfully processed {results_processed_count} result(s) for Polling Unit '{polling_unit_obj.polling_unit_name}'.")
                else:
                    messages.warning(request, "No new results were added or existing results updated based on your input.")
                return redirect('add_all_party_polling_unit_results') 

    context = {
        'lgas': lgas,
        'parties': parties,
        'selected_lga_id': selected_lga_id,
        'selected_ward_id': selected_ward_id,
        'selected_pu_id': selected_pu_id,
        'wards': wards,         
        'polling_units': polling_units, 
    }
    return render(request, 'add_all_party_polling_unit_results.html', context)