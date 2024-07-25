""" Usage : Inherit the model res company and added and manage the functionality of Onboarding Panel"""
from odoo import fields, models, api

SHOPIFY_ONBOARDING_STATES = [('not_done', "Not done"), ('just_done', "Just done"), ('done', "Done"),
                             ('closed', "Closed")]


class ResCompany(models.Model):
    _inherit = 'res.company'

    default_shopify_instance_id = fields.Many2one('shopify.instance.ept', string="Default Instance")

