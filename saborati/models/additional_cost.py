# -*- coding: utf-8 -*-

from odoo import models, fields, api, _ 

class AdditionalCost(models.Model): 
    _name = 'additional.cost'
    _order = 'create_date desc'
    
    company_id = fields.Many2one('res.company', string='Company',  default=lambda self: self.env.company.id, company_dependent=True)
    
    cost = fields.Float(string='Costo adicional', company_dependent=True)
    note = fields.Text(string='Notas', company_dependent=True)

    product_tmpl_id = fields.Many2one('product.template', company_dependent=True)