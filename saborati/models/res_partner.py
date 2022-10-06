# -*- coding: utf-8 -*-

from odoo import models, api, fields, _ 

class ResPartner(models.Model): 
    _inherit = 'res.partner'

    def create(self, vals_list): 
        res = super(ResPartner, self).create(vals_list)

        res.company_id = self.env.company.id
        res.lang = 'es_MX'

        return res