# -*- coding: utf-8 -*-

from odoo import models, api, fields, _


class AccountMoveLine(models.Model): 
    _inherit = 'account.move.line'
    
    replacement_cost = fields.Float('Replacement Cost', compute="_compute_replacement_cost",
        store=True,
        readonly=False)
    margin_rc = fields.Float(compute="_compute_margin_rc", digits="Product Price", store=True)
    margin_signed_rc = fields.Float(
        compute="_compute_margin_rc",
        digits="Product Price",
        store=True,
    )
    margin_percent_rc = fields.Float(
        string="Margin (%)", compute="_compute_margin_rc", store=True, readonly=True
    )
    
    
    @api.depends("replacement_cost", "price_subtotal")
    def _compute_margin_rc(self):
        for line in self:
            if line.move_id and line.move_id.move_type[:2] == "in":
                line.update(
                    {"margin_rc": 0.0, "margin_signed_rc": 0.0, "margin_percent_rc": 0.0}
                )
                continue
            tmp_margin = line.price_subtotal - (line.replacement_cost * line.quantity)
            sign = line.move_id.move_type in ["in_refund", "out_refund"] and -1 or 1
            line.update(
                {
                    "margin_rc": tmp_margin,
                    "margin_signed_rc": tmp_margin * sign,
                    "margin_percent_rc": (
                        tmp_margin / line.price_subtotal * 100.0
                        if line.price_subtotal
                        else 0.0
                    ),
                }
            )
        
    def _get_purchase_replacement_cost(self):
        # Overwrite this function if you don't want to base your
        # purchase price on the product standard_price
        self.ensure_one()
        return self.product_id.replacement_cost
    
    
    @api.depends("product_id", "product_uom_id")
    def _compute_replacement_cost(self):
        for line in self:
            if line.move_id.move_type in ["out_invoice", "out_refund"]:
                purchase_price = line._get_purchase_replacement_cost()
                if line.product_uom_id != line.product_id.uom_id:
                    purchase_price = line.product_id.uom_id._compute_price(
                        purchase_price, line.product_uom_id
                    )
                move = line.move_id
                company = move.company_id or self.env.company
                line.replacement_cost = company.currency_id._convert(
                    purchase_price,
                    move.currency_id,
                    company,
                    move.invoice_date or fields.Date.today(),
                    round=False,
                )
            else:
                line.replacement_cost = 0.0
