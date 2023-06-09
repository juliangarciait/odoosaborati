# -*- coding: utf-8 -*-

from odoo import fields, models, api, _ 
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model): 
    _inherit = 'sale.order'

    custom_state_delivery = fields.Char(string='State Delivery',
        compute='_compute_get_delivery_custom_state',
        help='Automatic assignation state from custom state delivery:\n', store=True)

    def write(self, vals):
        if self.custom_state_delivery in ['Ready (No Delivered)', 'Done (Delivered)']:
            if 'order_line' in vals:
                if vals['order_line']:
                    if len(self.order_line) < len(vals['order_line']):
                        raise ValidationError(
                            "You can't add more lines in the current state (" + self.custom_state_delivery + ")")

        return super(SaleOrder, self).write(vals)

    @api.depends('delivery_percentage')
    def _compute_get_delivery_custom_state(self):
        for record in self:
            record.custom_state_delivery = ''
            if record.state == 'draft' or record.state == 'sent' or record.state == 'cancel': 
                record.custom_state_delivery = 'No Status'
            else:
                if record.delivery_percentage >= 1.0: 
                    record.custom_state_delivery = 'Done (Delivered)'
                elif record.delivery_percentage > 0 and record.delivery_percentage < 1.0: 
                    record.custom_state_delivery = 'Waiting'
                elif record.delivery_percentage == 0:
                    record.custom_state_delivery = 'Ready (Not Delivered)'

    



   





