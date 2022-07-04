# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging 
_logger = logging.getLogger(__name__)

class ProductPricelist(models.Model): 
    _inherit = 'product.pricelist'

    is_main_pricelist = fields.Boolean('Use this as main pricelist?')

    @api.model
    def create(self, vals_list): 
        pricelist = super(ProductPricelist, self).create(vals_list)

        if pricelist.is_main_pricelist: 
            pricelist_true = self.search([('is_main_pricelist', '=', True), ('id', '!=', pricelist.id)])
            if pricelist_true: 
                pricelist_true.is_main_pricelist = False
            
            #for item in pricelist.item_ids:

            #    if item.applied_on == '3_global': 
            #        for product in self.env['product.product'].search([]): 
            #            product.product_tmpl_id.list_price = self._get_display_price(product)
            #            _logger.info('#'*1000)
            #            _logger.info(product.list_price)
            #    elif item.applied_on == '2_product_category': 
            #        for product in self.env['product.product'].search([('product_tmpl_id.categ_id', '=', item.categ_id)]):
            #            product.product_tmpl_id.list_price = self._get_display_price(product)
            #    elif item.applied_on == '1_product': 
            #        item.product_tmpl_id.list_price = self._get_display_price(item.product_tmpl_id.internal_reference.product_variant_id)
            #    elif item.applied_on == '0_product_variant': 
            #        item.product_id.product_tmpl_id.list_price = self._get_display_price(item.product_id)
        
        return pricelist

    def write(self, vals): 
        res = super(ProductPricelist, self).write(vals)

        for pricelist in self:
            if pricelist.is_main_pricelist: 
                pricelist_true = self.search([('is_main_pricelist', '=', True), ('id', '!=', pricelist.id)])
                if pricelist_true: 
                    pricelist_true.is_main_pricelist = False
                
                #for item in pricelist.item_ids:

                #    if item.applied_on == '3_global': 
                #        for product in self.env['product.product'].search([]): 
                #            product.product_tmpl_id.list_price = self._get_display_price(product)
                #            _logger.info('#'*1000)
                #            _logger.info(product.list_price)
                #    elif item.applied_on == '2_product_category': 
                #        for product in self.env['product.product'].search([('product_tmpl_id.categ_id', '=', item.categ_id)]):
                #            product.product_tmpl_id.list_price = self._get_display_price(product)
                #    elif item.applied_on == '1_product': 
                #        item.product_tmpl_id.list_price = self._get_display_price(item.product_tmpl_id.internal_reference.product_variant_id)
                #    elif item.applied_on == '0_product_variant': 
                #        item.product_id.product_tmpl_id.list_price = self._get_display_price(item.product_id)

        return res

    def _get_display_price(self, product): 
        if self.discount_policy == 'with_discount':
            return product.with_context(pricelist=self.id, uom=self.product_uom.id).price
        product_context = dict(self.env.context, partner_id=self.order_id.partner_id.id, date=self.order_id.date_order, uom=self.product_uom.id)

        final_price, rule_id = self.order_id.pricelist_id.with_context(product_context).get_product_price_rule(product or self.product_id, self.product_uom_qty or 1.0, self.order_id.partner_id)
        base_price, currency = self.with_context(product_context)._get_real_price_currency(product, rule_id, self.product_uom_qty, self.product_uom, self.order_id.pricelist_id.id)
        if currency != self.order_id.pricelist_id.currency_id:
            base_price = currency._convert(
                base_price, self.order_id.pricelist_id.currency_id,
                self.order_id.company_id or self.env.company, self.order_id.date_order or fields.Date.today())
        # negative discounts (= surcharge) are included in the display price
        return max(base_price, final_price)



class ProductPricelistItem(models.Model): 
    _inherit = 'product.pricelist.item'

    base = fields.Selection([('list_price', 'Sales Price'), ('replacement_cost', 'Replacement Cost'), ('pricelist', 'Other Pricelist')])