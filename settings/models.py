from django.db import models


class Setting(models.Model):
    """
    Meta-model for all project settings
    """
    form_types   = [('CharField', 'Text'),
                    ('ChoiceField', 'Selection'),
                    ('IntegerField', 'Digit'),
                    ('BooleanField', 'Boolean'),
                    ('DateField', 'Date'),
                    ('EmailField', 'E-mail'),
                    ('FileField', 'File upload'),
                    ('ImageField', 'Image'),
                    ('URLField', 'URL')]
    # 'name' will be a label for the Setting
    name         = models.CharField(blank=False, max_length=200)
    # 'form_type' is a type of the data which is about to be fetched
    form_type    = models.CharField(default='CharField', blank=False, choices=form_types, max_length=20)
    # Next field determines the type of the Form's widget(HTML Form type)
    widget_type  = models.CharField(blank=False, max_length=20)
    # 'choices' contains all the variants for 'Select', 'RadioSelect', 'CheckboxInput' resulted Forms
    choices      = models.CharField(blank=True, max_length=1000)
    help_message = models.CharField(blank=True, max_length=200)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class GlobalSetting(Setting):
    """
    Global settings options Model.
    """
    pass


class UserSetting(Setting):
    """
    User settings options Model.
    """
    pass
    # user = models.OneToOneField(User, blank=False, null=False, unique=True)


class User(models.Model):
    """
    Model which stores all user information
    """
    first_name = models.CharField(blank=False, max_length=20)
    last_name  = models.CharField(blank=False, max_length=20)
    password   = models.CharField(blank=False, max_length=20)
    email      = models.CharField(blank=False, max_length=40)
    nickname   = models.CharField(blank=False, max_length=15)
    phone      = models.IntegerField(blank=False)
    photo      = models.CharField(blank=False, max_length=256)


class Global(models.Model):
    """
    Model contains all global settings
    """

    # TODO: add necessary fields and do the migration
    pass