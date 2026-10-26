from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, inline_serializer


class AccountsIndexView(APIView):
    """Placeholder endpoint for accounts module."""
    permission_classes = [AllowAny]

    @extend_schema(responses={200: inline_serializer("AccountsIndexResponse", fields={})})
    def get(self, request):
        return Response({"module": "accounts", "status": "initialized"})

