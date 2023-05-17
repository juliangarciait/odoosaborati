# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)


class ProductMargin(models.Model): 
    _name = 'product.margin'
    _order = 'create_date desc'
    
    company_id = fields.Many2one('res.company', string='Company',  default=lambda self: self.env.company.id)

    margin = fields.Float('Margin', default=lambda self: self.env.company.default_company_margin)
    product_tmpl_id = fields.Many2one('product.template')