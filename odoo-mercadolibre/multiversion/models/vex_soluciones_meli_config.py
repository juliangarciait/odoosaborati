#import meli
#from ..python_sdk.meli.configuration
from ..sdk.meli.configuration import  Configuration
from ..sdk.meli.api_client import ApiClient
from ..sdk.meli.api.o_auth_2_0_api import OAuth20Api
from ..sdk.meli.exceptions import ApiException
API_URL  = 'https://api.mercadolibre.com'
AUTH_URL = 'https://auth.mercadopago.com.pe'
INFO_URL = 'https://api.mercadolibre.com/users/me'
#('MLM', 'Mexico'),,
#('MMX', 'Mexico'),
COUNTRIES = [
    ('MLM', 'Mexico'),
    ('MLV', 'Venezuela'),
    ('MLB', 'Brasil'),
    ('MPE', 'Perú'),
    #('MCU', 'Cuba'),
    ('MNI', 'Nicaragua'),
    ('MRD', 'Dominicana'),
    ('MCO', 'Colombia'),
    ('MCR', 'Costa Rica'),
    ('MBO', 'Bolivia'),
    ('MHN', 'Honduras'),
    ('MLC', 'Chile'),
    ('MGT', 'Guatemala'),
    ('MEC', 'Ecuador'),
    ('MPY', 'Paraguay'),
    ('MPA', 'Panamá'),
    ('MSV', 'El Salvador'),
    ('MLA', 'Argentina'),
    ('MLU', 'Uruguay')
]

COUNTRIES_DOMINIO = {
    'MLM': 'mx',
    'MLV': 've',
    'MLB': 'br',
    'MPE': 'pe',
    #'MCU': 'cu',
    'MNI': 'ni',
    'MRD': 'do',
    'MCO': 'co',
    'MCR': 'cr',
    'MBO': 'bo',
    'MHN': 'hn',
    'MLC': 'cl',
    'MGT': 'gt',
    'MEC': 'ec',
    'MPY': 'py',
    'MPA': 'pa',
    'MSV': 'sv',
    'MLA': 'ar',
    'MLU': 'uy'
}

CURRENCIES = [
    ('ARS', 'Peso argentino'),
    ('BOB', 'Boliviano'),
    ('BRL', 'Real'),
    ('CLF', 'Unidad de Fomento'),
    ('CLP', 'Peso Chileno'),
    ('COP', 'Peso colombiano'),
    ('CRC', 'Colones'),
    ('CUC', 'Peso Cubano Convertible'),
    ('CUP', 'Peso Cubano'),
    ('DOP', 'Peso Dominicano'),
    ('EUR', 'Euro'),
    ('GTQ', 'Quetzal Guatemalteco'),
    ('HNL', 'Lempira'),
    ('MXN', 'Peso Mexicano'),
    ('NIO', 'Córdoba'),
    ('PAB', 'Balboa'),
    ('PEN', 'Soles'),
    ('PYG', 'Guaraní'),
    ('USD', 'Dólar'),
    ('UYU', 'Peso Uruguayo'),
    ('VEF', 'Bolivar fuerte'),
    ('VES', 'Bolivar Soberano')]

CONDITIONS = [
    ("new", "Nuevo"),
    ("used", "Usado"),
    ("not_specified","No especificado")
]

MELI_STATUS = [
        #Initial state of an order, and it has no payment yet.
        ("confirmed","Confirmado"),
        #The order needs a payment to become confirmed and show users information.
        ("payment_required","Pago requerido"),
        #There is a payment related with the order, but it has not accredited yet
        ("payment_in_process","Pago en proceso"),
        ('partially_paid','Parcialmente Pagado'),
        #The order has a related payment and it has been accredited.
        ("paid","Pagado"),
        ('partially_refunded','Devolución Parcial'),
        ('pending_cancel','Cancelacion Pendiente'),
        #The order has not completed by some reason.
        ("cancelled","Cancelado")
]

MELI_SHIPPINGS = [
    ('drop_off','Mercado Envíos'),
    ('xd_drop_off','Mercado Envíos Place'),
    ('cross_docking','Mercado Envíos Colecta'),
    ('fulfillment','Mercado Envíos Full'),
    ('self_service','Mercado Envíos Flex')
]


CATEGORIES_REQUIRED_ATRR =  [
    'MLM418152',
    'MLM1417'
]

CATEGORIES_REQUIRED_BRAND =  [
    'MLM185717',
    'MLM191147',
    'MLM185709',
    'MLM185710',
    'MLM194320',
    'MLM194365'

]

def get_token(client_id, client_secret, redirect_uri, code, refresh_token):
    configuration2 = Configuration(
        host = API_URL
    )

    with ApiClient() as api_client:
        api_instance = OAuth20Api(api_client)
        grant_type = 'refresh_token'
    
        try:
            api_response = api_instance.get_token(grant_type=grant_type, client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, code=code, refresh_token=refresh_token)
            return api_response
        except ApiException as err:
            return None


