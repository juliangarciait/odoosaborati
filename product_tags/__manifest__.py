# -*- coding: utf-8 -*-

{
    'name': "Tags for Products", 
    'summary': """
    This module adds tags model for products and its field in product model
    """, 
    'author': "Quemari developers", 
    'website': "http://www.quemari.com",
    'category': "Inventory",
    'depends': [
        'stock'
    ], 
    'data': [
        'security/ir.model.access.csv',

        'views/product_template_view.xml',
        'views/product_tags_view.xml',
    ]
}