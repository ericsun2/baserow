from baserow_premium.api.views.errors import ERROR_INVALID_SELECT_OPTION_PARAMETER
from baserow_premium.api.views.exceptions import InvalidSelectOptionParameter
from baserow_premium.license.features import PREMIUM
from baserow_premium.license.handler import LicenseHandler
from baserow_premium.views.exceptions import KanbanViewHasNoSingleSelectField
from baserow_premium.views.handler import get_rows_grouped_by_single_select_field
from baserow_premium.views.models import KanbanView
from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.decorators import allowed_includes, map_exceptions
from baserow.api.errors import ERROR_USER_NOT_IN_GROUP
from baserow.api.schemas import get_error_schema
from baserow.contrib.database.api.fields.errors import (
    ERROR_FIELD_DOES_NOT_EXIST,
    ERROR_FILTER_FIELD_NOT_FOUND,
)
from baserow.contrib.database.api.rows.serializers import (
    RowSerializer,
    get_row_serializer_class,
)
from baserow.contrib.database.api.views.errors import (
    ERROR_NO_AUTHORIZATION_TO_PUBLICLY_SHARED_VIEW,
    ERROR_VIEW_FILTER_TYPE_DOES_NOT_EXIST,
    ERROR_VIEW_FILTER_TYPE_UNSUPPORTED_FIELD,
)
from baserow.contrib.database.api.views.serializers import validate_api_grouped_filters
from baserow.contrib.database.api.views.utils import get_public_view_authorization_token
from baserow.contrib.database.fields.exceptions import (
    FieldDoesNotExist,
    FilterFieldNotFound,
)
from baserow.contrib.database.fields.field_filters import (
    FILTER_TYPE_AND,
    FILTER_TYPE_OR,
)
from baserow.contrib.database.rows.registries import row_metadata_registry
from baserow.contrib.database.table.operations import ListRowsDatabaseTableOperationType
from baserow.contrib.database.views.exceptions import (
    NoAuthorizationToPubliclySharedView,
    ViewDoesNotExist,
    ViewFilterTypeDoesNotExist,
    ViewFilterTypeNotAllowedForField,
)
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.registries import (
    view_filter_type_registry,
    view_type_registry,
)
from baserow.contrib.database.views.signals import view_loaded
from baserow.core.exceptions import UserNotInWorkspace
from baserow.core.handler import CoreHandler

from .errors import (
    ERROR_KANBAN_DOES_NOT_EXIST,
    ERROR_KANBAN_VIEW_HAS_NO_SINGLE_SELECT_FIELD,
)
from .serializers import get_kanban_view_example_response_serializer
from .utils import prepare_kanban_view_parameters


class KanbanViewView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="view_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns only rows that belong to the related view's "
                "table.",
            ),
            OpenApiParameter(
                name="include",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    "A comma separated list allowing the values of `field_options` and "
                    "`row_metadata` which will add the object/objects with the same "
                    "name to the response if included. The `field_options` object "
                    "contains user defined view settings for each field. For example "
                    "the field's width is included in here. The `row_metadata` object"
                    " includes extra row specific data on a per row basis."
                ),
            ),
            OpenApiParameter(
                name="limit",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="Defines how many rows should be returned by default. "
                "This value can be overwritten per select option.",
            ),
            OpenApiParameter(
                name="offset",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="Defines from which offset the rows should be returned."
                "This value can be overwritten per select option.",
            ),
            OpenApiParameter(
                name="select_option",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    "Accepts multiple `select_option` parameters. If not provided, the "
                    "rows of all select options will be returned. If one or more "
                    "`select_option` parameters are provided, then only the rows of "
                    "those will be included in the response. "
                    "`?select_option=1&select_option=null` will only include the rows "
                    "for both select option with id `1` and `null`. "
                    "`?select_option=1,10,20` will only include the rows of select "
                    "option id `1` with a limit of `10` and and offset of `20`."
                ),
            ),
        ],
        tags=["Database table kanban view"],
        operation_id="list_database_table_kanban_view_rows",
        description=(
            "Responds with serialized rows grouped by the view's single select field "
            "options if the user is authenticated and has access to the related "
            "workspace. Additional query parameters can be provided to control the "
            "`limit` and `offset` per select option."
            "\n\nThis is a **premium** feature."
        ),
        responses={
            200: get_kanban_view_example_response_serializer(),
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_KANBAN_VIEW_HAS_NO_SINGLE_SELECT_FIELD",
                    "ERROR_INVALID_SELECT_OPTION_PARAMETER",
                    "ERROR_FEATURE_NOT_AVAILABLE",
                ]
            ),
            404: get_error_schema(["ERROR_KANBAN_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            ViewDoesNotExist: ERROR_KANBAN_DOES_NOT_EXIST,
            KanbanViewHasNoSingleSelectField: (
                ERROR_KANBAN_VIEW_HAS_NO_SINGLE_SELECT_FIELD
            ),
            InvalidSelectOptionParameter: ERROR_INVALID_SELECT_OPTION_PARAMETER,
        }
    )
    @allowed_includes("field_options", "row_metadata")
    def get(self, request, view_id, field_options, row_metadata):
        """Responds with the rows grouped by the view's select option field value."""

        view_handler = ViewHandler()
        view = view_handler.get_view_as_user(request.user, view_id, KanbanView)
        workspace = view.table.database.workspace

        # We don't want to check if there is an active premium license if the workspace
        # is a template because that feature must then be available for demo purposes.
        if not workspace.has_template():
            LicenseHandler.raise_if_user_doesnt_have_feature(
                PREMIUM, request.user, workspace
            )

        CoreHandler().check_permissions(
            request.user,
            ListRowsDatabaseTableOperationType.type,
            workspace=workspace,
            context=view.table,
            allow_if_template=True,
        )
        single_select_option_field = view.single_select_field

        if not single_select_option_field:
            raise KanbanViewHasNoSingleSelectField(
                "The requested kanban view does not have a required single select "
                "option field."
            )

        (
            included_select_options,
            default_limit,
            default_offset,
        ) = prepare_kanban_view_parameters(request)

        model = view.table.get_model()
        serializer_class = get_row_serializer_class(
            model, RowSerializer, is_response=True
        )
        rows = get_rows_grouped_by_single_select_field(
            view=view,
            single_select_field=single_select_option_field,
            option_settings=included_select_options,
            default_limit=default_limit,
            default_offset=default_offset,
            model=model,
        )

        rows_serialized = {}
        for key, value in rows.items():
            rows_serialized[key] = {
                "count": value["count"],
                "results": serializer_class(value["results"], many=True).data,
            }

        response = {"rows": rows_serialized}

        if field_options:
            view_type = view_type_registry.get_by_model(view)
            context = {"fields": [o["field"] for o in model._field_objects.values()]}
            serializer_class = view_type.get_field_options_serializer_class(
                create_if_missing=True
            )
            response.update(**serializer_class(view, context=context).data)

        if row_metadata:
            row_metadata = row_metadata_registry.generate_and_merge_metadata_for_rows(
                request.user,
                view.table,
                (row.id for row_group in rows.values() for row in row_group["results"]),
            )
            response.update(row_metadata=row_metadata)

        view_loaded.send(
            sender=self,
            table=view.table,
            view=view,
            table_model=model,
            user=request.user,
        )

        return Response(response)


class PublicKanbanViewView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="slug",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.STR,
                description="Returns only rows that belong to the related view.",
            ),
            OpenApiParameter(
                name="limit",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="Defines how many rows should be returned by default. "
                "This value can be overwritten per select option.",
            ),
            OpenApiParameter(
                name="offset",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="Defines from which offset the rows should be returned."
                "This value can be overwritten per select option.",
            ),
            OpenApiParameter(
                name="select_option",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    "Accepts multiple `select_option` parameters. If not provided, the "
                    "rows of all select options will be returned. If one or more "
                    "`select_option` parameters are provided, then only the rows of "
                    "those will be included in the response. "
                    "`?select_option=1&select_option=null` will only include the rows "
                    "for both select option with id `1` and `null`. "
                    "`?select_option=1,10,20` will only include the rows of select "
                    "option id `1` with a limit of `10` and and offset of `20`."
                ),
            ),
            OpenApiParameter(
                name="filters",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    "A JSON serialized string containing the filter tree to apply "
                    "to this view. The filter tree is a nested structure containing "
                    "the filters that need to be applied. \n\n"
                    "Please note that if this parameter is provided, all other "
                    "`filter__{field}__{filter}` will be ignored, "
                    "as well as the `filter_type` parameter. \n\n"
                    "An example of a valid filter tree is the following:"
                    '`{"filter_type": "AND", "filters": [{"field": 1, "type": "equal", '
                    '"value": "test"}]}`.\n\n'
                    f"The following filters are available: "
                    f'{", ".join(view_filter_type_registry.get_types())}.'
                ),
            ),
            OpenApiParameter(
                name="filter__{field}__{filter}",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    f"The rows can optionally be filtered by the same view filters "
                    f"available for the views. Multiple filters can be provided if "
                    f"they follow the same format. The field and filter variable "
                    f"indicate how to filter and the value indicates where to filter "
                    f"on.\n\n"
                    "Please note that if the `filters` parameter is provided, "
                    "this parameter will be ignored. \n\n"
                    f"For example if you provide the following GET parameter "
                    f"`filter__field_1__equal=test` then only rows where the value of "
                    f"field_1 is equal to test are going to be returned.\n\n"
                    f"The following filters are available: "
                    f'{", ".join(view_filter_type_registry.get_types())}.'
                ),
            ),
            OpenApiParameter(
                name="filter_type",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    "`AND`: Indicates that the rows must match all the provided "
                    "filters.\n"
                    "`OR`: Indicates that the rows only have to match one of the "
                    "filters.\n\n"
                    "This works only if two or more filters are provided."
                    "Please note that if the `filters` parameter is provided, "
                    "this parameter will be ignored. \n\n"
                ),
            ),
        ],
        tags=["Database table kanban view"],
        operation_id="public_list_database_table_kanban_view_rows",
        description=(
            "Responds with serialized rows grouped by the view's single select field "
            "options related to the `slug` if the kanban view is publicly shared. "
            "Additional query parameters can be provided to control the `limit` and "
            "`offset` per select option. \n\nThis is a **premium** feature."
        ),
        responses={
            200: get_kanban_view_example_response_serializer(),
            401: get_error_schema(["ERROR_NO_AUTHORIZATION_TO_PUBLICLY_SHARED_VIEW"]),
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_KANBAN_VIEW_HAS_NO_SINGLE_SELECT_FIELD",
                    "ERROR_VIEW_FILTER_TYPE_DOES_NOT_EXIST",
                    "ERROR_VIEW_FILTER_TYPE_UNSUPPORTED_FIELD",
                    "ERROR_FILTER_FIELD_NOT_FOUND",
                    "ERROR_FILTERS_PARAM_VALIDATION_ERROR",
                ]
            ),
            404: get_error_schema(["ERROR_KANBAN_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            ViewDoesNotExist: ERROR_KANBAN_DOES_NOT_EXIST,
            KanbanViewHasNoSingleSelectField: (
                ERROR_KANBAN_VIEW_HAS_NO_SINGLE_SELECT_FIELD
            ),
            InvalidSelectOptionParameter: ERROR_INVALID_SELECT_OPTION_PARAMETER,
            NoAuthorizationToPubliclySharedView: (
                ERROR_NO_AUTHORIZATION_TO_PUBLICLY_SHARED_VIEW
            ),
            FilterFieldNotFound: ERROR_FILTER_FIELD_NOT_FOUND,
            ViewFilterTypeDoesNotExist: ERROR_VIEW_FILTER_TYPE_DOES_NOT_EXIST,
            ViewFilterTypeNotAllowedForField: ERROR_VIEW_FILTER_TYPE_UNSUPPORTED_FIELD,
            FieldDoesNotExist: ERROR_FIELD_DOES_NOT_EXIST,
        }
    )
    @allowed_includes("field_options")
    def get(self, request, slug: str, field_options: bool):
        """
        Lists all the rows of a kanban view that is publicly shared. The rows are
        grouped by the view's single select field options.
        """

        filter_type = (
            FILTER_TYPE_OR
            if request.GET.get("filter_type", "AND").upper() == "OR"
            else FILTER_TYPE_AND
        )
        filter_object = {key: request.GET.getlist(key) for key in request.GET.keys()}

        # Advanced filters are provided as a JSON string in the `filters` parameter.
        # If provided, all other filter parameters are ignored.
        api_filters = None
        if (filters := filter_object.get("filters", None)) and len(filters) > 0:
            api_filters = validate_api_grouped_filters(filters[0])

        view_handler = ViewHandler()
        view = view_handler.get_public_view_by_slug(
            request.user,
            slug,
            KanbanView,
            authorization_token=get_public_view_authorization_token(request),
        )

        single_select_option_field = view.single_select_field
        if not single_select_option_field:
            raise KanbanViewHasNoSingleSelectField(
                "The requested kanban view does not have a required single select "
                "option field."
            )

        (
            included_select_options,
            default_limit,
            default_offset,
        ) = prepare_kanban_view_parameters(request)

        model = view.table.get_model()
        view_type = view_type_registry.get_by_model(view)
        (
            queryset,
            field_ids,
            publicly_visible_field_options,
        ) = ViewHandler().get_public_rows_queryset_and_field_ids(
            view,
            filter_type=filter_type,
            filter_object=filter_object,
            table_model=model,
            view_type=view_type,
            api_filters=api_filters,
        )

        serializer_class = get_row_serializer_class(
            model,
            RowSerializer,
            is_response=True,
            field_ids=field_ids,
        )
        rows = get_rows_grouped_by_single_select_field(
            view=view,
            single_select_field=single_select_option_field,
            option_settings=included_select_options,
            default_limit=default_limit,
            default_offset=default_offset,
            model=model,
            base_queryset=queryset,
        )

        for key, value in rows.items():
            rows[key]["results"] = serializer_class(value["results"], many=True).data

        response = {"rows": rows}

        if field_options:
            context = {"field_options": publicly_visible_field_options}
            serializer_class = view_type.get_field_options_serializer_class(
                create_if_missing=True
            )
            response.update(**serializer_class(view, context=context).data)

        return Response(response)
