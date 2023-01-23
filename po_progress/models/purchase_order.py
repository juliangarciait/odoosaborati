from odoo import fields, models, api

import logging

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    qty_d_progress = fields.Float(compute='_compute_po_order_progress')
    max_qty_d = fields.Float(compute='_compute_po_order_progress')
    percent_d_progress = fields.Float(compute='_compute_po_order_progress', string="Progreso de recepción")


    def _compute_po_order_progress(self):
       for record in self:
            order_lines_done = 0
            order_l_qty = 0 
            for line in record.order_line:
                if line.product_id.type in ['product', 'consu']:
                    order_l_qty += line.product_qty
                order_lines_done += line.qty_received
            record.qty_d_progress = order_lines_done
            record.max_qty_d = order_l_qty
            if order_l_qty > 0:
                record.percent_d_progress = order_lines_done/order_l_qty
            else:
                record.percent_d_progress = 0