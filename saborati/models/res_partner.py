# -*- coding: utf-8 -*-

from odoo import models, api, fields, _ 

class ResPartner(models.Model): 
    _inherit = 'res.partner'
    
    company_filter = fields.Selection(
        selection=[('person', 'Individual'), ('company', 'Company')],
        compute='_compute_company_filter', store=True)
    
    address_reference = fields.Text('Referencia')

    partner_company_id = fields.Many2one('res.company', 'Compañía')
    
    @api.depends('company_type')
    def _compute_company_filter(self): 
        for partner in self: 
            partner.company_filter = partner.company_type

    @api.model
    def create(self, vals_list): 
        res = super(ResPartner, self).create(vals_list)

        if not res.partner_company_id: 
            res.partner_company_id = self.env.company.id
        #res.company_id = self.env.company.id
        res.lang = 'es_MX'

        return res