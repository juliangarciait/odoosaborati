# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging 
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model): 
    _inherit = 'sale.order'

    delivery_percentage = fields.Float('Delivery %', compute='_compute_deliver_percentage')

    @api.depends('order_line.product_uom_qty', 'order_line.qty_delivered', 'order_line.price_unit')
    def _compute_deliver_percentage(self): 
        for record in self:
            qty_percentage = 0
            dlv_percentage = 0

            for line in record.order_line: 
                qty_percentage += line.product_uom_qty * line.price_unit
                dlv_percentage += line.qty_delivered * line.price_unit

            record.delivery_percentage = dlv_percentage / qty_percentage if qty_percentage > 0 else 0.0