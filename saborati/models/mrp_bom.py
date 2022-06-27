# -*- coding: utf-8 -*-

from odoo import models, api, fields, _ 

import logging 
_logger = logging.getLogger(__name__)


class MrpBom(models.Model): 
    _inherit = 'mrp.bom'

    replacement_cost_total = fields.Float('Replacement Cost Total', compute='_compute_total', store=True)

    @api.depends('bom_line_ids.result')  
    def _compute_total(self): 
        total = 0
        for line in self.bom_line_ids: 
            total += line.result

        self.product_tmpl_id.replacement_cost = self.replacement_cost_total = total

class MrpBomLine(models.Model): 
    _inherit = 'mrp.bom.line'


    result = fields.Float('Result', readonly=True, compute='_compute_result', store=True)

    @api.depends('replacement_cost', 'product_qty')
    def _compute_result(self): 
        for line in self:
            line.result = line.replacement_cost * line.product_qty

