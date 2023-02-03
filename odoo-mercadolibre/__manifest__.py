# -*- coding: utf-8 -*-
{
    'name': "Odoo Mercado Libre Vex Connector",

    'summary': """
        Module to synchronize odoo with Mercado Libre""",


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
    'price': 399.00,
    'currency': 'USD',

    # any module necessary for this one to work correctly
    'depends': ['base_conector_vex'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/vex_instance.xml',
        #'views/vex_soluciones_product_attribute.xml',
        'views/vex_soluciones_meli_synchro_instance.xml',
        'views/vex_soluciones_product_product.xml',
        'views/vex_soluciones_categories.xml',
        'views/vex_soluciones_orders.xml',
        #'views/vex_soluciones_logs.xml',
        #'views/vex_soluciones_questions.xml',
        'views/vex_soluciones_product_template.xml',
        'views/vex_soluciones_customers.xml',
        'wizard/vex_soluciones_meli_action_synchro.xml',
        #'wizard/vex_soluciones_stock.xml',
        'wizard/vex_soluciones_export.xml',
        'data/meli_action_list.xml',
        'data/order_status.xml',
        'data/vex_cron.xml',
        #'views/conectado.xml',
        'views/vex_soluciones_meli_action_list.xml',
    ],

    'images': ['static/description/odoo-mercadolibre.gif'],
}
