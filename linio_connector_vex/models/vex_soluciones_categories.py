from odoo import api, fields, models
#from odoo.addons.payment.models.payment_acquirer import ValidationError

class Categories(models.Model):
    _inherit                = 'product.public.category'
    conector                = fields.Selection(selection_add=[('linio', 'Linio')])
    #global_identifier = fields.Char()
