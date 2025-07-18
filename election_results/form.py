from django import forms
from .models import States, Lga, Ward, PollingUnit, AnnouncedPuResults


class PollingUnitSelectionForm(forms.Form):
    state = forms.ModelChoiceField(
        queryset=States.objects.none(),
        empty_label="Select a State",
        required=True
    )

    lga = forms.ModelChoiceField(
        queryset=Lga.objects.none(),
        empty_label="Select an LGA",
        required=True
    )

    ward = forms.ModelChoiceField(
        queryset=Ward.objects.none(),
        empty_label="Select a Ward",
        required=True
    )

    polling_unit = forms.ModelChoiceField(
        queryset=PollingUnit.objects.none(),
        empty_label="Select a Polling Unit",
        required=True
    )

    def __init__(self, *args, **kwargs):
        state_id = kwargs.pop('state_id', None)
        lga_id = kwargs.pop('lga_id', None)
        ward_id = kwargs.pop('ward_id', None)

        super().__init__(*args, *kwargs)

        self.fields['state'].queryset = States.objects.filter(state_id=25)

        if state_id:
            self.fields['lga'].queryset = Lga.objects.filter(state_id=state_id)
        else:
            self.fields['lga'].queryset = Lga.objects.none()


        if lga_id:
            self.fields['ward'].queryset = Ward.objects.filter(lga_id=lga_id)
        else:
            self.fields['ward'].queryset = Ward.objects.none()


        if ward_id:
            self.fields['polling_unit'].queryset = PollingUnit.objects.filter(ward_id=ward_id)
        else:
            self.fields['polling_unit'].queryset = PollingUnit.objects.none()
