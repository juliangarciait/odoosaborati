# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ProductTemplate(models.Model): 
    _inherit = 'product.template'

    tag_ids = fields.Many2many('product.tags', 'product_tag_rel', 'product_id', 'tag_id', string="Tags")