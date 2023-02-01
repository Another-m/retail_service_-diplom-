from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django import forms

from app.models import Company


class RegisterForm(UserCreationForm):
    username = forms.CharField(label='Логин')
    company = forms.CharField(max_length=50, label="Наименование компании")
    # company = forms.ModelChoiceField(queryset=Company.objects, label="Компания", empty_label="Не выбрано")
    tin = forms.IntegerField(label="ИНН")
    counterparty_type = forms.ChoiceField(choices=Company.C_TYPE, label="Тип контрагента", )
    post = forms.CharField(max_length=30, label="Ваша должность")

    def __init__(self, *args, **kwargs):
        _country_list = kwargs.pop('data_list', None)
        super(RegisterForm, self).__init__(*args, **kwargs)

        # the "name" parameter will allow you to use the same widget more than once in the same
        # form, not setting this parameter differently will cuse all inputs display the
        # same list.
        data = Company.objects.all()
        self.fields['tin'].widget = ListTextWidget(data_list=(i.tin for i in data), name='tin')
        self.fields['company'].widget = ListTextWidget(data_list=(i.name for i in data), name='company')



    class Meta:
        model = get_user_model()
        fields = ('email', 'username', 'company', 'tin', 'counterparty_type', 'post', 'password1', 'password2',)


class ListTextWidget(forms.TextInput):
    def __init__(self, data_list, name, *args, **kwargs):
        super(ListTextWidget, self).__init__(*args, **kwargs)
        self._name = name
        self._list = data_list
        self.attrs.update({'list':'list__%s' % self._name})

    def render(self, name, value, attrs=None, renderer=None):
        text_html = super(ListTextWidget, self).render(name, value, attrs=attrs)
        data_list = '<datalist id="list__%s">' % self._name
        for item in self._list:
            data_list += '<option value="%s">' % item
        data_list += '</datalist>'

        return (text_html + data_list)


class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Логин либо Email')
