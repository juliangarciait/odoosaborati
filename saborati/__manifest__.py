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
        'security/ir.model.access.csv',
        'security/groups.xml',
        
        'views/product_supplierinfo_views.xml',
        'views/product_template_views.xml',
        'views/sale_order_views.xml',
        'views/mrp_bom_views.xml',
        'views/product_template_views.xml',
        'views/product_tags_views.xml',
        'views/stock_production_lot_views.xml',
        'views/product_category_views.xml',
        'views/product_product_views.xml',
        'views/brand_views.xml', 
    ], 
    'installable' : True, 
    'auto_install' : False
}