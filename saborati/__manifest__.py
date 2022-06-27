# -*- coding: utf-8 -*-

{
    'name' : "Saborati", 
    'category' : "Uncategorized", 
    'summary' : """
    Saborati
    """,
    'author' : "Quemari developers", 
    'website' : "http://www.quemari.com", 
    'depends' : [
        'purchase',
        'vendor_pricelist_fields',
        'stock',
        'product_tags',
        'product_cost',
    ],
    'data' : [
        'views/product_supplierinfo_views.xml',
        'views/product_template_views.xml',
        'views/sale_order_views.xml',
        'views/mrp_bom_views.xml',
    ], 
    'installable' : True, 
    'auto_install' : False
}