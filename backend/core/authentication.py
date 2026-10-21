from rest_framework.authentication import TokenAuthentication, get_authorization_header
from rest_framework import exceptions


class FlexibleTokenAuthentication(TokenAuthentication):
    """
    Supports token authentication with both 'Token' and 'Bearer' prefix.
    """

    def authenticate(self, request):
        auth = get_authorization_header(request).split()

        if not auth:
            return None

        prefix = auth[0].decode('utf-8', errors='ignore').lower()
        if prefix not in ['token', 'bearer']:
            return None

        if len(auth) == 1:
            raise exceptions.AuthenticationFailed(
                'Invalid authorization header. No token provided.'
            )
        elif len(auth) > 2:
            raise exceptions.AuthenticationFailed(
                'Invalid authorization header. Token string should not contain spaces.'
            )

        try:
            token = auth[1].decode('utf-8')
        except UnicodeError:
            raise exceptions.AuthenticationFailed(
                'Invalid authorization header. Token string contains invalid characters.'
            )

        return self.authenticate_credentials(token)
