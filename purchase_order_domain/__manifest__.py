# -*- coding: utf-8 -*-

{
    'name' : "Mostrar solo producto del proveedor en compras",
    'summary' : """
    Este módulo agrega un filtro para que en las líneas de compras solo se muestren los productos que estén relacionados al proveedor en vendor pricelist
    """, 
    'author' : "Quemari developers",
    'website' : "http://www.quemari.com", 
    'category' : "Purchase", 
    'depends' : [
        'purchase',
    ], 
    'data' : [
        'views/purchase_order_view.xml',
    ],
}