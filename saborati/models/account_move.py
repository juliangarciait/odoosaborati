# -*- coding: utf-8 -*-

from odoo import fields, models, api, _ 
import logging 
_logger = logging.getLogger(__name__)


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
    

    
class AccountPayment(models.Model):
    _inherit = 'account.payment'

    invoice_details = fields.Text(string='Detalles de Facturas', compute='_compute_invoice_details')

    importe_pendiente = fields.Monetary(string='Importe pendiente', compute='_compute_invoice_details')

    @api.depends('invoice_line_ids')
    def _compute_invoice_details(self):
        for record in self:
            details = ""
            cantidad_pagada = 0
            # for line in record.invoice_line_ids:
            #     if line.account_internal_type == 'receivable' and line.move_id.move_type in ['out_invoice', 'in_invoice']:
            #         invoice = line.move_id
            #         # Aquí puedes formatear la información como prefieras
            self._cr.execute('''
                             SELECT
                invoice.name, part.amount
            FROM account_payment payment
            JOIN account_move move ON move.id = payment.move_id
            JOIN account_move_line line ON line.move_id = move.id
            JOIN account_partial_reconcile part ON
                part.debit_move_id = line.id
                OR
                part.credit_move_id = line.id
            JOIN account_move_line counterpart_line ON
                part.debit_move_id = counterpart_line.id
                OR
                part.credit_move_id = counterpart_line.id
            JOIN account_move invoice ON invoice.id = counterpart_line.move_id
            JOIN account_account account ON account.id = line.account_id
            WHERE account.internal_type IN ('receivable', 'payable')
                AND payment.id = %(payment_ids)s
                AND line.id != counterpart_line.id
                AND invoice.move_type in ('out_invoice', 'out_refund', 'in_invoice', 'in_refund', 'out_receipt', 'in_receipt')
                             ''', {
            'payment_ids': record.id
            })
            query_res = self._cr.dictfetchall()
            for res in query_res:
                    #details.append(res)
                    details += res['name']+"  $"+str(res["amount_total"]) + "\n"
                    cantidad_pagada += float(res["amount_total"])
            record.importe_pendiente = record.amount - cantidad_pagada
            record.invoice_details = details