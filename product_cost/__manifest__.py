# -*- coding: utf-8 -*-

{
    'name' : "Costos de reposición", 
    'summary' : """
    Este módulo agrega el campo de costos de reposición y el cálculo del mismo
    """, 
    'author' : "Quemari developers", 
    'website' : "http://www.quemari.com",
    'category' : "Inventory", 
    'depends' : [
        'stock',
        'purchase', 
        'mrp',
    ], 
    'data' : [
        'views/product_template_view.xml',
        'views/mrp_bom_view.xml',
        'views/account_move_views.xml',
    ],
}