# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero
from itertools import groupby
from datetime import datetime, timedelta
from lxml import etree
import logging

_logger = logging.getLogger(__name__)



class StockPicking(models.Model): 
    _inherit = 'stock.picking'


    custom_state_delivery = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready (No Delivered)'),
        ('done', 'Done (Delivered)'),
        ('cancel', 'Cancel')], string='State Delivery',
        compute='_compute_sync_with_state', store=True,
        help='Automatic assignation state from state delivery:\n'
             '\tNote: It can be modified manually')


    @api.depends('state')
    def _compute_sync_with_state(self):
        for stock in self:
            originally_states = list(dict(stock._fields['state'].selection).keys())
            if not stock.custom_state_delivery:
                _logger.info('Custom state was set')
                stock.custom_state_delivery = stock.state
            elif stock.custom_state_delivery in originally_states:
                stock.custom_state_delivery = stock.state
                _logger.info('Custom state was set')
            else:
                _logger.info('Custom state was not set')


class StockMoveLine(models.Model): 
    _inherit = 'stock.move.line'

    @api.onchange('product_id')
    def _onchange_product_id_set_lot_domain(self):
        lot_ids = []
        if self.product_id: 
            lots = self.env['stock.production.lot'].search([('product_id', '=', self.product_id.id)])
            for lot in lots: 
                if lot.product_qty > 0: 
                    lot_ids.append(lot.id)
            
        return {
            'domain': {'lot_id': [('id', 'in', lot_ids)]}
        } 
    

    
    