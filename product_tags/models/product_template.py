# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ProductTemplate(models.Model): 
    _inherit = 'product.template'

    tag_ids = fields.Many2many('product.tags', column1='product_id', column2='tag_id', string="Tags")