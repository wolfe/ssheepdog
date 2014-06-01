from django.conf.urls import patterns, url
from aws_policy_manager.views import ListAWSPoliciesView

urlpatterns = patterns(
    'aws_policy_manager.views',
    url(r'^$', ListAWSPoliciesView.as_view(), name='policy_list'),
)
