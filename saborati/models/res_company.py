# -*- coding: utf-8 -*-

from odoo import api, fields, models, _ 


class ResCompany(models.Model): 
    _inherit = 'res.company'


    default_company_margin = fields.Float('Default Margin')

    medium_id = fields.Many2one('utm.medium', string='Medio')


    