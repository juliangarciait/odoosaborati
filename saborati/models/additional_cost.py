# -*- coding: utf-8 -*-

from odoo import models, fields, api, _ 

class AdditionalCost(models.Model): 
    _name = 'additional.cost'
    
    cost = fields.Float(string='Costo adicional')
    note = fields.Text(string='Notas')

    product_tmpl_id = fields.Many2one('product.template')