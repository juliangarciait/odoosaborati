# -*- coding: utf-8 -*-

{
    'name' : "Status de delivery y filtros por lotes",
    'summary' : """
    Módulo que añade el status del delivery relacionado a la venta en la vista tree, agrega porcentaje en deliveries y filtros por lotes 
    """, 
    'author' : "Quemari developers", 
    'website' : "http://www.quemari.com",
    'category' : "Inventory",
    'depends' : [
        'sale_management',
    ],
    'data' : [
        'views/sale_order_views.xml',
        'views/stock_picking_views.xml',
    ],
}