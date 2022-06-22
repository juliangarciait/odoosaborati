# -*- coding: utf-8 -*-

from odoo import fields, models, api, _ 


class ProductSupplierinfo(models.Model): 
    _inherit = 'product.supplierinfo'

    notes = fields.Text('Notes')