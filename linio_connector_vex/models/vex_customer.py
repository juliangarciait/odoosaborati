from odoo import api, fields, models
class Customers(models.Model):
    _name           = 'res.partner'
    _inherit        = 'res.partner'
    conector = fields.Selection(selection_add=[('linio', 'Linio')])