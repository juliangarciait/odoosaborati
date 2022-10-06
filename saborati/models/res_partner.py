# -*- coding: utf-8 -*-

from odoo import models, api, fields, _ 

class ResPartner(models.Model): 
    _inherit = 'res.partner'
    
    company_type = fields.Selection(string='Company Type',
        selection=[('person', 'Individual'), ('company', 'Company')],
        compute='_compute_company_type', inverse='_write_company_type', store=True)

    def create(self, vals_list): 
        res = super(ResPartner, self).create(vals_list)

        res.company_id = self.env.company.id
        res.lang = 'es_MX'

        return res