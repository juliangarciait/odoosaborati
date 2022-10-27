# -*- coding: utf-8 -*-
from odoo import models, api, fields
import logging

class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.depends('company_id')
    def _compute_currency_id(self):
        main_company = self.env.company
        for template in self:
            template.currency_id = template.company_id.sudo().currency_id.id or main_company.currency_id.id