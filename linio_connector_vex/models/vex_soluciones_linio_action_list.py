from odoo import api, fields, models
from odoo.addons.payment.models.payment_acquirer import ValidationError
import requests

#from .vex_soluciones_meli_config import API_URL


class LinioActionList(models.Model):
    _inherit = "vex.restapi.list"
    conector = fields.Selection(selection_add=[('linio', 'Linio')])
