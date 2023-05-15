# -*- coding: utf-8 -*-
# =====================================================================================
# License: OPL-1 (Odoo Proprietary License v1.0)
#
# By using or downloading this module, you agree not to make modifications that
# affect sending messages through Acruxlab or avoiding contract a Plan with Acruxlab.
# Support our work and allow us to keep improving this module and the service!
#
# Al utilizar o descargar este módulo, usted se compromete a no realizar modificaciones que
# afecten el envío de mensajes a través de Acruxlab o a evitar contratar un Plan con Acruxlab.
# Apoya nuestro trabajo y permite que sigamos mejorando este módulo y el servicio!
# =====================================================================================
{
    'name': 'WhatsApp - Admin tab',
    'summary': 'Allows Administrators to release and assign conversations. ChatRoom 2.0.',
    'description': 'Allows Administrators to release and assign conversations. Real ChatRoom. WhatsApp integration. Send Product, WhatsApp Connector. GupShup. Chat-Api. ChatApi. ChatRoom 2.0.',
    'version': '15.0.6',
    'author': 'AcruxLab',
    'live_test_url': 'https://chatroom.acruxlab.com/web/signup',
    'support': 'info@acruxlab.com',
    'price': 150.0,
    'currency': 'USD',
    # 'images': ['static/description/Banner_base.gif'],
    'website': 'https://acruxlab.com/whatsapp',
    'license': 'OPL-1',
    'application': True,
    'installable': True,
    'category': 'Discuss/Sales/CRM',
    'depends': [
        'whatsapp_connector',
    ],
    'data': [
        'security/security.xml',
        'views/conversation_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # widgets
            '/whatsapp_connector_admin/static/src/js/acrux_*.js',
            '/whatsapp_connector_admin/static/src/css/*.css',
        ],
        'web.assets_qweb': [
            'whatsapp_connector_admin/static/src/xml/*',
        ],
    },
    'post_load': '',
    'external_dependencies': {},

}
