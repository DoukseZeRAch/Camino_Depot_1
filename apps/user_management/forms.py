from django import forms
from .models import Users

class UserEditForm(forms.ModelForm):
    class Meta:
        model = Users
        fields = ['username', 'email', 'role', 'is_active']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm'