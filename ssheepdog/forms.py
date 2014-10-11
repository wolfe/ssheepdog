from django import forms
from ssheepdog import models
from django.utils.safestring import mark_safe
from Crypto.PublicKey import RSA


class AccessFilterForm(forms.Form):
    user = forms.CharField(label="User", required=False)
    login = forms.CharField(label="Login/Machine", required=False)


class LoginForm(forms.ModelForm):
    named_application_key = forms.ModelChoiceField(
        required=False,
        label="Force reset to named key",
        queryset=models.NamedApplicationKey.objects.all(),
        help_text=
        """
        Usually leave this blank.  This can be useful when you just cloned a
        master VM which was already pre-configured with this start key.  This
        named key will be used to authenticate on the next key deployment, but
        SSHeepdog will overwrite the named key the latest SSHeepdog key on the
        next deployment.
        """)

    class Meta:
        model = models.Login

    def save(self, *args, **kwargs):
        commit = kwargs.get('commit', True)
        kwargs['commit'] = False
        obj = super(LoginForm, self).save(*args, **kwargs)
        key = self.cleaned_data['named_application_key']
        if key:
            obj.application_key = key.application_key
        if commit:
            obj.save()
        return obj


class NamedApplicationForm(forms.ModelForm):
    private_key = forms.CharField(
        required=False,
        help_text=('Supply private key to overwrite.'
                   ' It will never be shown again.'),
        widget=forms.Textarea(attrs={'cols': 94}))

    def clean_private_key(self, *args, **kwargs):
        private_key = self.cleaned_data.get('private_key', None)
        if private_key is None or not private_key.strip():
            return None
        private_key = private_key and private_key.strip()
        if not private_key:
            return None
        elif not (private_key.startswith('-----BEGIN RSA PRIVATE KEY-----')
                  and private_key.endswith('-----END RSA PRIVATE KEY-----')):
            raise forms.ValidationError(mark_safe(
                "Private key must be of the form<br/>"
                "-----BEGIN RSA PRIVATE KEY-----<br/>"
                "...<br/>"
                "-----END RSA PRIVATE KEY-----"))
        try:
            pub = RSA.importKey(private_key).publickey().exportKey('OpenSSH')
        except ValueError as e:
            raise forms.ValidationError(str(e))
        self.cleaned_data['new_public_key'] = pub
        return private_key

    def save(self, *args, **kwargs):
        private_key = self.cleaned_data.get('private_key', None)
        if private_key:
            public_key = self.cleaned_data.get('new_public_key')
            key = models.ApplicationKey.objects.create(is_named=True,
                                                       private_key=private_key,
                                                       public_key=public_key)
            self.instance.application_key = key
        return super(NamedApplicationForm, self).save(*args, **kwargs)

    class Meta:
        model = models.NamedApplicationKey


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = models.UserProfile
        fields = ('ssh_key',)
