# -*- coding: utf-8 -*-

from odoo import fields, models, api, _ 
import logging
_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model): 
    _inherit = 'product.template'

    margin_ids = fields.One2many('product.margin', 'product_tmpl_id')

    list_price = fields.Float(compute="_compute_price")


    @api.depends('margin_ids', 'replacement_cost')
    def _compute_price(self): 
        for record in self:
            record.list_price = 1.0
            margin = self.env['product.margin'].search([('product_tmpl_id', '=', record.id)], order='create_date desc', limit=1).margin
            if margin and record.replacement_cost:   
                record.list_price = record.replacement_cost / (1 - margin)
