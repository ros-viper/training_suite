import os
import string
from django.shortcuts import render, get_object_or_404
from .models import GlobalSetting, UserSetting, User, Global
from django import forms
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core import validators
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.template.defaulttags import register


# Form validation functions go here
def password_validator(value):
    if 20 < len(value) < 6:
        raise ValidationError(_('Password length should be within 6-20 symbols'), code='invalid length')
    if not [_ for _ in value if _ in string.punctuation]:
        raise ValidationError(_('Password should contain special characters'),
                              code='no special chars')
    if not [_ for _ in value if _ in string.ascii_uppercase]:
        raise ValidationError(_('Password should contain capital letters'), code='no uppercase')
    if not [_ for _ in value if _ in string.digits]:
        raise ValidationError(_('Password should contain digits'), code='no lowercase')


def image_validator(value):
    if value.size > 307200:
        raise ValidationError(_('Image size should be under 300Kb'),
                              code='size limit reached')
    if not value.content_type == 'image/jpeg':
        raise ValidationError(_('MIME type is invalid. Only *.JPG files are accepted'),
                              code='image type error')
    if ' ' in value.name or [ _ for _ in value.name.split('.')[0] if _ in string.punctuation]:
        raise ValidationError(_('Name should not contain spaces or special characters'),
                              code='image type error')


# Filter for dict values parsing in a loop within the template
# http://stackoverflow.com/questions/8000022/django-template-how-to-look-up-a-dictionary-value-with-a-variable
@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@login_required
@user_passes_test(lambda user: user.is_staff)
def edit_settings_view(request, settings_type):

    settings_type = settings_type.lower()
    # Querying appropriate Model
    if settings_type == 'user':
        settings_database = UserSetting
        current_settings = UserSetting.objects.all()
    else:
        settings_database = GlobalSetting
        current_settings = GlobalSetting.objects.all()

    # Creating view Form for Settings editing
    class EditForm(forms.ModelForm):
        class Meta:
            model = settings_database
            fields = '__all__'
            widgets = {'form_type': forms.Select, 'widget_type': forms.Select}
            help_texts = {'values': 'Please enter available Form options separated by commas'}

    settings_edit_form = EditForm()

    if request.method == 'POST':
        # Adding new record
        if 'adding_setting' in request.POST:
            settings_edit_form = EditForm(request.POST)
            if settings_edit_form.is_valid():
                # If the form data is already in the database will update the record
                if settings_edit_form.cleaned_data['name'] in current_settings.values_list('name', flat=True):
                    setting_to_update = get_object_or_404(settings_database, name=request.POST['name'])
                    settings_edit_form = EditForm(request.POST, instance=setting_to_update)
                settings_edit_form.save()
        # Removing the selected records
        elif 'deleting_setting' in request.POST:
            selected_question = settings_database.objects.filter(id__in=request.POST.getlist('choice'))
            selected_question.delete()
        # Redirect to the other page with data commitment into DB
        elif 'setting_submission' in request.POST:
            # TODO: add a proper redirect here
            return HttpResponseRedirect(reverse('settings_view', args=(settings_type,)))

    return render(request, ''.join(['settings/edit_', settings_type, '_settings.html']),
                  {'current_settings': current_settings,
                   'settings_type': settings_type,
                   'settings_edit_form': settings_edit_form})


@login_required
@user_passes_test(lambda user: user.is_staff)
def settings_view(request, settings_type):
    # Querying appropriate Model
    if settings_type == 'user':
        settings_database = User
        setting_options = UserSetting.objects.all()
        model_settings = User.objects.all()
    else:
        settings_database = Global
        setting_options = GlobalSetting.objects.all()
        model_settings = Global.objects.all()

    # Form methods mapping dict
    form_widget_mappings = {'CharField': {'type': forms.CharField, 'TextInput': forms.TextInput,
                                          'Textarea': forms.Textarea, 'PasswordInput': forms.PasswordInput},
                            'ChoiceField': {'type': forms.ChoiceField, 'Select': forms.Select,
                                            'SelectMultiple': forms.SelectMultiple, 'CheckboxInput': forms.CheckboxInput,
                                            'RadioSelect': forms.RadioSelect},
                            'IntegerField': {'type': forms.IntegerField, 'NumberInput': forms.NumberInput},
                            'BooleanField': {'type': forms.BooleanField, 'CheckboxInput': forms.CheckboxInput},
                            'DateField': {'type': forms.DateField, 'DateInput': forms.DateInput},
                            'EmailField': {'type': forms.EmailField, 'EmailInput': forms.EmailInput},
                            'FileField': {'type': forms.FileField, 'FileInput': forms.FileInput},
                            'ImageField': {'type': forms.ImageField, 'ClearableFileField': forms.ClearableFileInput,
                                           'FileInput': forms.FileInput},
                            'URLField': {'type': forms.URLField, 'URLInput': forms.URLInput}
                            }

    # The following Form will do all the work except data commitment
    class SettingForm(forms.Form):

        def __init__(self, *args, **kwargs):
            super(SettingForm, self).__init__(*args, **kwargs)

            # Creating a setting Form
            for index, setting in enumerate(setting_options):
                self.fields[setting.name] = form_widget_mappings[setting.form_type]['type']()
                self.fields[setting.name].label = setting.name
                self.fields[setting.name].widget = form_widget_mappings[setting.form_type][setting.widget_type]()
                if setting.form_type == 'ChoiceField':
                    self.fields[setting.name].choices = [('', x) for x in setting.choices.split(',')]
                self.fields[setting.name].help_text = setting.help_message

                # Setting validators
                if setting.name == 'First name' or setting.name == 'Last name':
                    self.fields[setting.name].validators = \
                        [validators.RegexValidator(regex=r'^[\w\-]{1,20}$',
                                                   message='Please enter a valid name of 1-20 symbols length, '
                                                           'containing alphanumeric characters and hyphens only')]
                if 'Password' in setting.name or 'password' in setting.name:
                    self.fields[setting.name].validators =[password_validator]
                if 'Mail' in setting.name or 'mail' in setting.name:
                    self.fields[setting.name].validators = \
                        [validators.RegexValidator(regex=r'^\S+?\@\S+?\.[A-Za-z]+$',
                                                   message='Please enter a valid e-mail address')]
                if 'Phone' in setting.name or 'phone' in setting.name:
                    self.fields[setting.name].initial = '+38'
                    self.fields[setting.name].validators = \
                        [validators.RegexValidator(regex=r'^\+?[\d]{6,18}$',
                                                   message='Please enter a valid phone number, '
                                                           'without hyphens and brackets')]
                if setting.name == 'Nickname':
                    self.fields[setting.name].validators = \
                        [validators.RegexValidator(regex=r'^\S{1,15}$',
                                                   message='Please enter a valid nickname of 1-15 symbols length')]
                if setting.name == 'Photo' or setting.name == 'Avatar' or setting.name == 'Picture':
                    self.fields[setting.name].validators = [image_validator]

        # Another set of validators for the dependant fields
        def clean(self):
            cleaned_data = super(SettingForm, self).clean()
            if 'Password' in self.fields and 'Confirm password' in self.fields and \
                    not cleaned_data.get('Password') == cleaned_data.get('Confirm password'):
                self.add_error('Confirm password', 'Passwords don\'t match')

    settings_form = SettingForm()
    errors = list()

    if request.method == 'POST':
        settings_form = SettingForm(request.POST, request.FILES)
        if settings_form.is_valid():
            # The following Form is created in data commitment purposes only
            class SettingFormSave(forms.ModelForm):
                class Meta:
                    model = settings_database
                    fields = '__all__'

            # 'request.POST' and 'request.FILES' contain human-readable field names, like 'E-mail' or 'Last name'
            # when database field names will obviously have 'email' and 'last_name' equivalents
            # Therefore we need to normalize 'request.POST' and 'request.FILES' dictionaries before committing them
            # confirmation fields should not be committed at all
            database_fields = [f.name for f in settings_database._meta.get_fields()]
            data_to_commit = {}
            for entry in request.POST:
                # Normalizing entry name
                entry_normalized = ''.join([ _ for _ in entry if _ not in string.punctuation])
                entry_normalized = entry_normalized.replace(' ', '_').lower()
                if entry_normalized in database_fields:
                    data_to_commit[entry_normalized] = request.POST[entry]

            # Will store all attached validated files into '__file__/static' folder
            for entry in request.FILES:
                # Saving pictures/photos/avatars on the disk
                if entry == 'Photo' or entry == 'Avatar' or entry == 'Picture':
                    full_file_path = \
                        os.sep.join([os.path.dirname(os.path.abspath(__file__)),
                                     'static', 'avatars', request.FILES[entry].name])
                    file = open(full_file_path, 'wb+')
                    file.write(request.FILES[entry].read())  # No need of multiple_chunks() method here
                                                             # as we have a validator for file size already
                    file.close()

                    # Adding the path to the Form dictionary to save it into the database
                    data_to_commit[entry.lower()] = full_file_path

            # Publishing the entered data into the DB
            setting_to_publish = SettingFormSave(data_to_commit)
            if setting_to_publish.is_valid():
                # If the form data is already in the database will update the record
                if setting_to_publish.cleaned_data['email'] in model_settings.values_list('email', flat=True):
                    setting_to_update = get_object_or_404(settings_database, email=data_to_commit['email'])
                    setting_to_publish = SettingFormSave(data_to_commit, instance=setting_to_update)
                elif setting_to_publish.cleaned_data['nickname'] in model_settings.values_list('nickname', flat=True):
                    setting_to_update = get_object_or_404(settings_database, nickname=data_to_commit['nickname'])
                    setting_to_publish = SettingFormSave(data_to_commit, instance=setting_to_update)
                setting_to_publish.save()

                # TODO: add a redirect here
                return HttpResponse('Your settings had been recorded')
            else:
                errors = setting_to_publish.errors
        else:
            errors = settings_form.errors
    return render(request, ''.join(['settings/', settings_type, '_settings.html']),
                  {'settings_form': settings_form,
                   'settings_type': settings_type,
                   'errors': errors})

