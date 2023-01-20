# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)


class ProductMargin(models.Model): 
    _name = 'product.margin'

    company_id = fields.Many2one('res.company', string='Company',  default=lambda self: self.env.company.id, company_dependent=True)

    margin = fields.Float('Margin', default=lambda self: self.env.company.default_company_margin, company_dependent=True)
    product_tmpl_id = fields.Many2one('product.template', company_dependent=True)