# spid_config.py
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SP_CONFIG = {
    'strict': True,
    'debug': True,
    'sp': {
        'entityId': 'https://tuo-dominio.com/metadata/',  # URL pubblico dei metadati SP
        'assertionConsumerService': {
            'url': 'https://tuo-dominio.com/acs/',  # URL dove ricevere la risposta SAML
            'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST',
        },
        'singleLogoutService': {
            'url': 'https://tuo-dominio.com/sls/',
            'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect',
        },
        'x509cert': '',
        'privateKey': '',
    },
    'idp': {
        'entityId': 'https://idp.spid.gov.it/',
        'singleSignOnService': {
            'url': 'https://idp.spid.gov.it/sso',
            'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect',
        },
        'singleLogoutService': {
            'url': 'https://idp.spid.gov.it/slo',
            'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect',
        },
        'x509cert': 'MIIC...IL_CERTIFICATO_IDP...',
    },
    'security': {
        'authnRequestsSigned': True,
        'logoutRequestSigned': True,
        'logoutResponseSigned': True,
        'signMetadata': False,
        'wantMessagesSigned': False,
        'wantAssertionsSigned': True,
        'wantNameId': True,
        'wantNameIdEncrypted': False,
        'wantAssertionsEncrypted': False,
        'wantAttributeStatement': True,
    },
}
