import json

from django.contrib.auth.models import User
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.contrib.auth.decorators import user_passes_test, login_required
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.forms import Form as EmptyForm
from django.http import HttpResponse, HttpResponseBadRequest

from ssheepdog import models
from ssheepdog.models import Login
from ssheepdog.forms import UserProfileForm, AccessFilterForm


def permission_required(perm, login_url=None, raise_exception=True):
    def check_perms(user):
        if user.has_perm(perm):
            return True
        if raise_exception:
            raise PermissionDenied
        return False
    return user_passes_test(check_perms, login_url=login_url)


@login_required
@permission_required('ssheepdog.can_view_access_summary')
def view_access_summary(request):
    users = (User.objects
             .select_related('_profile_cache')
             .order_by('_profile_cache__nickname'))
    if not request.user.has_perm("ssheepdog.can_view_all_users"):
        users = users.filter(pk=request.user.pk)
    logins = (Login.objects
              .select_related('client', 'machine')
              .order_by('client__nickname', 'machine__nickname', 'username'))
    if not request.user.has_perm("ssheepdog.can_view_all_logins"):
        logins = logins.filter(users=request.user)
    filter_form = AccessFilterForm(request.GET)
    u, l = filter_form.data.get('user'), filter_form.data.get('login')
    if u:
        users = users.filter(Q(username__icontains=u)
                             | Q(email__icontains=u)
                             | Q(first_name__icontains=u)
                             | Q(last_name__icontains=u)
                             | Q(_profile_cache__nickname__icontains=u)
                             )
    if l:
        logins = logins.filter(Q(username__icontains=l)
                               | Q(client__nickname__icontains=l)
                               | Q(client__description__icontains=l)
                               | Q(machine__nickname__icontains=l)
                               | Q(machine__hostname__icontains=l)
                               | Q(machine__ip__icontains=l)
                               | Q(machine__description__icontains=l))

    # To conserve DB queries, pre load all relations as a dict
    # {(3,4): True} means user w/ 3 can access login w/ id 4
    rel_list = Login.users.through.objects.values("user_id", "login_id")
    user_login_rel = dict([((x['user_id'], x['login_id']), True)
                           for x in rel_list])

    for login in logins:
        login.entries = get_user_login_info(login, users, user_login_rel)

    return render_to_response(
        'view_grid.html',
        {'users': users, 'logins': logins, 'filter_form': filter_form},
        context_instance=RequestContext(request))


def get_user_login_info(login, users, user_login_rel):
    """
    Return a dict of data for each user; it's important
    that the users remain in the same order.
    """
    login_is_active = login.is_active and login.machine.is_active

    info = []
    for user in users:
        is_allowed = (user.pk, login.pk) in user_login_rel
        is_active = user.is_active and login_is_active

        verb = "is" if is_active else "would be"
        adjective = "permitted to access" if is_allowed else "forbidden from"
        explanations = []
        if not user.is_active:
            explanations.append("user were active")
        if not login.is_active:
            explanations.append("login were active")
        if not login.machine.is_active:
            explanations.append("machine were active")
        if_ = " if " if is_allowed else " even if "
        explanation = if_ + " and ".join(explanations) if explanations else ""

        tooltip = ("%s %s %s %s@%s%s"
                   % (user,
                      verb, adjective,
                      login.username,
                      login.machine.hostname or login.machine.ip,
                      explanation))
        info.append({'is_active': is_active,
                     'is_allowed': is_allowed,
                     'action': 'deny' if is_allowed else 'permit',
                     'tooltip': tooltip,
                     'user': user})
    return info


@permission_required('ssheepdog.can_view_access_summary')
def user_admin_view(request, id=None):
    user = User.objects.select_related('_profile_cache').get(pk=id)
    profile = user.get_profile()

    if request.method == 'POST' and request.user.pk == user.pk:
        # Can only edit your own ssh key through this interface
        if not request.user.has_perm('ssheepdog.can_edit_own_public_key'):
            raise PermissionDenied
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('ssheepdog.views.view_access_summary')
    else:
        form = UserProfileForm(instance=profile)
    return render_to_response('user_view.html', {'user': user, 'form': form},
                              context_instance=RequestContext(request))


@permission_required('ssheepdog.can_view_access_summary')
def login_admin_view(request, id=None):
    return render_to_response('login_view.html',
                              {'login': Login.objects.get(pk=id)},
                              context_instance=RequestContext(request))


@permission_required('ssheepdog.can_sync')
def manual_sync(request, id):
    login = Login.objects.get(pk=id)
    login.flag_as_manually_synced_by(request.user)
    return login_admin_view(request, id)


@permission_required('ssheepdog.can_sync')
def sync_keys(request):
    pk = request.POST.get('pk', None)
    if pk:
        try:
            login = Login.objects.get(pk=pk)
            login.sync(request.user)
        except Login.DoesNotExist:
            pass
    else:
        Login.sync_all(request.user)
    return redirect('ssheepdog.views.view_access_summary')


@permission_required('ssheepdog.can_sync')
def generate_new_application_key(request):
    from ssheepdog.utils import generate_new_application_key
    generate_new_application_key()
    return redirect('ssheepdog.views.view_access_summary')


@permission_required('ssheepdog.change_login')
def change_access(request, action, user_pk, login_pk):
    user = User.objects.select_related('_profile_cache').get(pk=user_pk)
    login = Login.objects.get(pk=login_pk)

    if request.method == 'POST':
        form = EmptyForm(request.POST)  # Using empty form just for CSFR
        if form.is_valid():
            if action == 'permit':
                login.users.add(user)
            elif action == 'deny':
                login.users.remove(user)
            return redirect('ssheepdog.views.view_access_summary')
    else:
        form = EmptyForm()
    return render_to_response('confirm_toggle.html',
                              {'user': user, 'form': form,
                               'login': login, 'action': action},
                              context_instance=RequestContext(request))


def _sanity_checks(data):
    keys = ['username', 'hostname', 'ip', 'application_key_name']
    assert set(data.keys()) >= set(keys), (
        'Post must include %s and may include client_name' % ', '.join(keys))
    if 'client_name' in data.keys():
        keys.append('client_name')
    for key in keys:
        assert isinstance(data[key], basestring), '%s must be a string' % key
        assert len(data[key]) > 0, '%s cannot be empty' % key
    query = models.NamedApplicationKey.objects.filter(
        nickname=data['application_key_name'])
    assert query.count() == 1, 'Named application key does not exist'
    data['application_key'] = query.get().application_key
    assert (models.Machine.objects.filter(ip=data['ip'])
            .count() == 0), 'Machine with ip already exists'
    assert (models.Machine.objects.filter(hostname=data['hostname'])
            .count() == 0), 'Machine with hostname already exists'


def create_machine_via_api(request):
    """
    Validate with simple shared secret.
    API cannot do much harm in any event, since it can only
    give us more power over machines.
    """
    try:
        assert request.method == 'POST', 'Request must be a POST'
        data = json.loads(request.raw_post_data)
        _sanity_checks(data)  # Adds application_key
    except AssertionError as e:
        return HttpResponseBadRequest(str(e))
    client, _ = (models.Client.objects
                 .get_or_create(nickname=data['client_name'])
                 if data.get('client_name') else None)
    models.Login.objects.create(
        machine=models.Machine.objects.create(
            ip=data['ip'],
            hostname=data['hostname'],
            client=client,
            nickname=data['hostname']),
        username=data['username'],
        application_key=data['application_key'])
    return HttpResponse('Machine entry created', status=201)
