from rest_framework.authentication import TokenAuthentication, get_authorization_header
from rest_framework import exceptions


class FlexibleTokenAuthentication(TokenAuthentication):
    """
    Unterstützt Token-Authentifizierung sowohl mit 'Token' als auch mit 'Bearer' Präfix.
    """

    def authenticate(self, request):
        auth = get_authorization_header(request).split()

        if not auth:
            return None

        prefix = auth[0].decode('utf-8', errors='ignore').lower()
        if prefix not in ['token', 'bearer']:
            return None

        if len(auth) == 1:
            raise exceptions.AuthenticationFailed('Ungültiger Auth-Header. Kein Token übergeben.')
        elif len(auth) > 2:
            raise exceptions.AuthenticationFailed('Ungültiger Auth-Header. Token darf keine Leerzeichen enthalten.')

        try:
            token = auth[1].decode('utf-8')
        except UnicodeError:
            raise exceptions.AuthenticationFailed('Ungültiger Auth-Header. Token enthält ungültige Zeichen.')

        return self.authenticate_credentials(token)
