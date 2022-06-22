# -*- coding: utf-8 -*-

from odoo import fields, models, api, _ 
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model): 
    _inherit = 'sale.order'

    custom_state_delivery = fields.Char(string='State Delivery',
        compute='_compute_get_delivery_custom_state',
        help='Automatic assignation state from custom state delivery:\n',
        store=True,
        tracking=True)

    def write(self, vals):
        if self.custom_state_delivery in ['Ready (No Delivered)', 'Done (Delivered)']:
            if vals['order_line']:
                if len(self.order_line) < len(vals['order_line']):
                    raise ValidationError("You can't add more lines in the current state ("+self.custom_state_delivery+")")
        return super(SaleOrder, self).write(vals)

    @api.depends('picking_ids.custom_state_delivery')
    def _compute_get_delivery_custom_state(self):
        for record in self:
            previus_status = record.custom_state_delivery
            pickings = self.mapped('picking_ids')
            if len(pickings)>0:
                sorte_list = pickings.sorted(key=lambda r: r.id)
                for picking in sorte_list:
                    if picking.state != 'cancel':
                        record.custom_state_delivery = dict(
                            picking._fields['custom_state_delivery'].selection).get(
                            picking.custom_state_delivery)
                        record.message_post(body='· Estado: {} --> {}'.format(previus_status, record.custom_state_delivery))
                        return
            record.custom_state_delivery = 'No status'

    



   





