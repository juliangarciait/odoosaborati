from odoo import api, fields, models
from odoo.exceptions import ValidationError

class Categories(models.Model):
    _inherit                = 'product.public.category'
    conector                = fields.Selection(selection_add=[('meli', 'Mercado Libre')])
    required_manufacture_meli = fields.Boolean(default=False)
    required_brand_meli = fields.Boolean(default=False)
    '''

    _sql_constraints = [
        ('unique_id_meli', 'unique(id_vex, conector , code_site_meli)',
         'There can be no duplication of synchronized categories')
    ]
    '''