# -*- coding: utf-8 -*-

from odoo import models, api, fields, _ 


class AssignCollectionToProduct(models.TransientModel): 
    _inherit = 'assign.collection.to.product'
    
    instance_id = fields.Many2one('shopify.instance.ept')
    