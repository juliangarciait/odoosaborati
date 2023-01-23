# -*- coding: utf-8 -*-
{
    'name': "Odoo Linio Vex Connector",

    'summary': """
        Module to synchronize odoo with Linio
    """,


    'description': """
        Module to synchronize odoo with Mercado Libre
    """,

    'author': "Vex Soluciones",
    'website': "https://www.vexsoluciones.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'price': 150.00,
    'currency': 'USD',

    # any module necessary for this one to work correctly
    'depends': ['base_conector_vex'],

    # always loaded
    'data': [
     'data/linio_action_list.xml',
     'views/vex_linio_instance.xml',
     'views/vex_soluciones_linio_action_list.xml',
     'wizard/vex_linio_action_synchro.xml',
     'data/order_status.xml',
     'security/ir.model.access.csv',
     'views/vex_order.xml',
     'data/vex_cron.xml' ,
     'views/product.xml'


    ],

    #'images': ['static/description/odoo-mercadolibre.gif'],
}