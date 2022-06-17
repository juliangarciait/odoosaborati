# -*- coding: utf-8 -*-

from odoo import models, api, fields, _


class ProductTemplate(models.Model): 
    _inherit = 'product.template'

    replacement_cost = fields.Float('Replacement Cost')