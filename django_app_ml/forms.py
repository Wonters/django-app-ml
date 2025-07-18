from django import forms
from .models import DataSet, IAModel

class DatasetForm(forms.ModelForm):
    class Meta:
        model = DataSet
        fields = ['name', 'description', 'link']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].initial = "dataset_1"
        self.fields['description'].initial = "Description du dataset"
        self.fields['link'].initial = "https://www.kaggle.com/datasets/kaggle/sample-csv-file"
        self.fields['name'].widget = forms.TextInput(attrs={"class": "form-control", "placeholder": "Nom du dataset"})
        self.fields['description'].widget = forms.Textarea(attrs={"class": "form-control", "placeholder": "Description du dataset"})
        self.fields['link'].widget = forms.TextInput(attrs={"class": "form-control", "placeholder": "URL du dataset"})

class ModelIAForm(forms.ModelForm):
    class Meta:
        model = IAModel
        fields = ['name', 'description', 'dataset']

    def __init__(self, *args, **kwargs):
        dataset_id = kwargs.pop('dataset_id', None)
        super().__init__(*args, **kwargs)
        self.fields['name'].initial = "model_1"
        self.fields['description'].initial = "Description du modèle"
        
        # Pré-remplir le dataset si un ID est fourni
        if dataset_id:
            try:
                dataset = DataSet.objects.get(id=dataset_id)
                self.fields['dataset'].initial = dataset
                # Rendre le champ caché et non modifiable
                self.fields['dataset'].widget = forms.HiddenInput()
            except DataSet.DoesNotExist:
                pass
        
        self.fields['name'].widget = forms.TextInput(attrs={"class": "form-control", "placeholder": "Nom du modèle"})
        self.fields['description'].widget = forms.Textarea(attrs={"class": "form-control", "placeholder": "Description du modèle"})
        
        # Widget par défaut pour dataset (si pas de dataset_id fourni)
        if not dataset_id:
            self.fields['dataset'].widget = forms.Select(attrs={"class": "form-control"})
