# -*- coding: utf-8 -*-

from odoo import fields, models, api, _ 


class AccountMoveLine(models.Model): 
    _inherit = 'account.move.line'


    def _get_computed_name(self):
            self.ensure_one()

            if not self.product_id:
                return ''

            if self.partner_id.lang:
                product = self.product_id.with_context(lang=self.partner_id.lang)
            else:
                product = self.product_id

            values = []
            if product.partner_ref:
                values.append(product.partner_ref)
            #if self.journal_id.type == 'sale':
            #    if product.description_sale:
            #        values.append(product.description_sale)
            #elif self.journal_id.type == 'purchase':
            #    if product.description_purchase:
            #        values.append(product.description_purchase)
            return '\n'.join(values)