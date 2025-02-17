from django.urls import re_path

from baserow.contrib.builder.api.domains.views import (
    AsyncPublishDomainView,
    DomainsView,
    DomainView,
    OrderDomainsView,
    PublicBuilderByDomainNameView,
    PublicBuilderByIdView,
    PublicBuilderWorkflowActionsView,
    PublicDataSourcesView,
    PublicElementsView,
)

app_name = "baserow.contrib.builder.api.domains"

urlpatterns_with_builder_id = [
    re_path(
        r"$",
        DomainsView.as_view(),
        name="list",
    ),
    re_path(r"order/$", OrderDomainsView.as_view(), name="order"),
]

urlpatterns_without_builder_id = [
    re_path(r"(?P<domain_id>[0-9]+)/$", DomainView.as_view(), name="item"),
    re_path(
        r"(?P<domain_id>[0-9]+)/publish/async/$",
        AsyncPublishDomainView.as_view(),
        name="publish",
    ),
    re_path(
        r"published/by_name/(?P<domain_name>[^/]+)/$",
        PublicBuilderByDomainNameView.as_view(),
        name="get_builder_by_domain_name",
    ),
    re_path(
        r"published/by_id/(?P<builder_id>[0-9]+)/$",
        PublicBuilderByIdView.as_view(),
        name="get_builder_by_id",
    ),
    re_path(
        r"published/page/(?P<page_id>[0-9]+)/elements/$",
        PublicElementsView.as_view(),
        name="list_elements",
    ),
    re_path(
        r"published/page/(?P<page_id>[0-9]+)/data_sources/$",
        PublicDataSourcesView.as_view(),
        name="list_data_sources",
    ),
    re_path(
        r"published/page/(?P<page_id>[0-9]+)/workflow_actions/$",
        PublicBuilderWorkflowActionsView.as_view(),
        name="list_workflow_actions",
    ),
]
