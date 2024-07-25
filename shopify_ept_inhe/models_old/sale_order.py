# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

import json
import logging
from datetime import datetime, timedelta
import time
import pytz
from odoo.tools.misc import format_date
from odoo.tests import Form
from dateutil import parser

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from ...shopify_ept import shopify
from ...shopify_ept.shopify.pyactiveresource.connection import ClientError
from ...shopify_ept.shopify.pyactiveresource.util import xml_to_dict

utc = pytz.utc

_logger = logging.getLogger("Shopify Order")


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def create_shopify_order_lines(self, lines, order_response, instance):
        sale_order_line_obj = self.env["sale.order.line"]
        total_discount = order_response.get("total_discounts", 0.0)
        order_number = order_response.get("order_number")
        for line in lines:
            is_custom_line, is_gift_card_line, product = self.search_custom_tip_gift_card_product(line, instance)
            if float(line.get("total_discount")) != 0.0 and total_discount and float(total_discount) > 0.0:
                discount_amount = 0.0
                for discount_allocation in line.get("discount_allocations"):
                    discount_amount += float(discount_allocation.get("amount"))
                if discount_amount > 0.0: 
                    line['price'] = ((float(line.get("price")) * float(line.get("quantity"))) - float(discount_amount)) / float(line.get("quantity"))
            price = line.get("price")
            if instance.order_visible_currency:
                price = self.get_price_based_on_customer_visible_currency(line.get("price_set"), order_response, price)
            order_line = self.shopify_create_sale_order_line(line, product, line.get("quantity"),
                                                             product.name, price,
                                                             order_response)
            if is_gift_card_line:
                line_vals = {'is_gift_card_line': True}
                if line.get('name'):
                    line_vals.update({'name': line.get('name')})
                order_line.write(line_vals)

            if is_custom_line:
                order_line.write({'name': line.get('name')})

            if line.get('duties'):
                self.create_shopify_duties_lines(line.get('duties'), order_response, instance)

            if float(line.get("total_discount")) == 0.0 and float(total_discount) > 0.0:
                discount_amount = 0.0
                for discount_allocation in line.get("discount_allocations"):
                    if instance.order_visible_currency:
                        discount_total_price = self.get_price_based_on_customer_visible_currency(
                            discount_allocation.get("amount_set"), order_response, discount_amount)
                        if discount_total_price:
                            discount_amount += float(discount_total_price)
                    else:
                        discount_amount += float(discount_allocation.get("amount"))

                if discount_amount > 0.0:
                    _logger.info("Creating discount line for Odoo order(%s) and Shopify order is (%s)", self.name,
                                 order_number)
                    self.shopify_create_sale_order_line({}, instance.discount_product_id, 1,
                                                        product.name, float(discount_amount) * -1,
                                                        order_response, previous_line=order_line,
                                                        is_discount=True)
                    _logger.info("Created discount line for Odoo order(%s) and Shopify order is (%s)", self.name,
                                 order_number)
        # add gift card as product in sale order line
        final_transactions_results = self.prepare_final_list_of_transactions(order_response.get('transaction'))
        total_giftcard_price = 0.0
        total_giftcard_qty = 0
        for transaction in final_transactions_results:
            if transaction.get('gateway') == 'gift_card':
                total_giftcard_qty += 1
                total_giftcard_price += float(transaction.get('amount'))
        if total_giftcard_price:
            product_id = instance.gift_card_product_id
            line_vals = self.prepare_vals_for_gift_card_sale_order_line(product_id, product_id.name,
                                                                        total_giftcard_price,
                                                                        total_giftcard_qty)
            sale_order_line_obj.create(line_vals)
            _logger.info("Gift card line for Odoo order(%s) and Shopify order is (%s)", self.name, order_number)


    def prepare_shopify_order_vals(self, instance, partner, shipping_address,
                                   invoice_address, order_response, payment_gateway,
                                   workflow):
        """
        This method used to Prepare a order vals.
        @param : self, instance, partner, shipping_address,invoice_address, order_response, payment_gateway,workflow
        @return: order_vals
        @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 13/11/2019.
        Task Id : 157350
        """
        ordervals = super(SaleOrder, self).prepare_shopify_order_vals(instance, partner, shipping_address,
                                   invoice_address, order_response, payment_gateway,
                                   workflow)
        var1 = instance.shopify_section_id.id if instance.shopify_section_id else False
        ordervals.update({"team_id": var1})
        return ordervals
