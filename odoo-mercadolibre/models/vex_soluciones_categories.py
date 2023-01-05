from odoo import api, fields, models
from odoo.addons.payment.models.payment_acquirer import ValidationError

class Categories(models.Model):
    _inherit                = 'product.public.category'
    conector                = fields.Selection(selection_add=[('meli', 'Mercado Libre')])
    required_attributes_meli = fields.Boolean(default=False)
    '''

    _sql_constraints = [
        ('unique_id_meli', 'unique(id_vex, conector , code_site_meli)',
         'There can be no duplication of synchronized categories')
    ]
    '''