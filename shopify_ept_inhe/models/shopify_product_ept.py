# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

import json
import logging
import time
from datetime import datetime, timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError
#from .. import shopify

_logger = logging.getLogger("Shopify Product")


class ShopifyProductProductEpt(models.Model):
    _inherit = "shopify.product.product.ept"

    def shopify_prepare_variant_vals(self, instance, variant, is_set_price, is_set_basic_detail):
        res = super(ShopifyProductProductEpt, self).shopify_prepare_variant_vals(instance, variant, is_set_price, is_set_basic_detail)
        if is_set_price:
            price = instance.shopify_pricelist_id.get_product_price(variant.product_id, 1.0, partner=False,
                                                                    uom_id=variant.product_id.uom_id.id)
            price = price * (1+(variant.product_id.taxes_id.filtered(lambda r: r.company_id == instance.shopify_company_id).amount)/100)
            res.update({"price": float(price)})

            if instance.shopify_compare_pricelist_id:
                compare_at_price = instance.shopify_compare_pricelist_id.get_product_price(variant.product_id, 1.0,
                                                                                            partner=False,
                                                                                            uom_id=variant.product_id.uom_id.id)
                compare_at_price = compare_at_price * (1+(variant.product_id.taxes_id.filtered(lambda r: r.company_id == instance.shopify_company_id).amount)/100)
                res.update({"compare_at_price": float(compare_at_price)})
        #if is_set_basic_detail:
        #     res.update({"weight": float(variant.product_id.weight)})
        return res

