# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.misc import get_lang
import logging 
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model): 
    _inherit = 'sale.order'

    delivery_percentage = fields.Float('Delivery %', compute='_compute_deliver_percentage')
    
    colony = fields.Char('Colonia', related="partner_id.l10n_mx_edi_colony")

    @api.depends('order_line.product_uom_qty', 'order_line.qty_delivered', 'order_line.price_unit')
    def _compute_deliver_percentage(self): 
        for record in self:
            qty_percentage = 0
            dlv_percentage = 0

            for line in record.order_line: 
                qty_percentage += line.product_uom_qty * line.price_unit
                dlv_percentage += line.qty_delivered * line.price_unit

            record.delivery_percentage = dlv_percentage / qty_percentage if qty_percentage > 0 else 0.0
            
            
class SaleOrderLine(models.Model): 
    _inherit = 'sale.order.line'
    
    @api.onchange('product_id')
    def _get_description_(self): 
        self.name = self.product_id.product_tmpl_id.name
        _logger.info('#'*10000)