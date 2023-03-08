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
        'crm',
        'report_xlsx',
        'sale',
        'sale_management',
        'queue_job',
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
        'views/res_company.xml',
        'views/crm_lead_views.xml',
        'views/res_partner.xml',
        'views/product_collection_views.xml',
        'views/product_pricelist_views.xml',
        'views/purchase_order_views.xml',
        'views/utm_medium_views.xml',
        #'views/stock_picking_views.xml',
        'views/stock_quant_views.xml',

        'wizard/assign_margin_to_product_views.xml',
        'wizard/assign_collection_to_product_views.xml',

        'report/shopify_report_prices.xml',
        'report/sale_report_templates.xml',
    ], 
    'installable' : True, 
    'auto_install' : False
}