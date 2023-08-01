# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError


class PosConfig(models.Model):
    _inherit = 'pos.config'
    limited_products_loading = fields.Boolean('Limited Product Loading', default=True)

    def get_limited_products_loading(self, fields):
        query = """
            WITH pm AS (
                  SELECT product_id,
                         Max(write_date) date
                    FROM stock_quant
                GROUP BY product_id
            )
               SELECT p.id
                 FROM product_product p
            LEFT JOIN product_template t ON product_tmpl_id=t.id
            LEFT JOIN pm ON p.id=pm.product_id
                WHERE (
                        t.available_in_pos
                    AND t.sale_ok
                    AND (t.company_id=%(company_id)s OR t.company_id IS NULL)
                    AND %(available_categ_ids)s IS NULL OR t.pos_categ_id=ANY(%(available_categ_ids)s)
                )    OR p.id=%(tip_product_id)s
             ORDER BY t.priority DESC,
                      t.detailed_type DESC,
                      COALESCE(pm.date,p.write_date) DESC 
                LIMIT %(limit)s
        """
        params = {
            'company_id': self.company_id.id,
            'available_categ_ids': self.iface_available_categ_ids.mapped('id') if self.iface_available_categ_ids else None,
            'tip_product_id': self.tip_product_id.id if self.tip_product_id else None,
            'limit': self.limited_products_amount
        }
        self.env.cr.execute(query, params)
        product_ids = self.env.cr.fetchall()
        products = self.env['product.product'].with_company(self.company_id).search_read([('id', 'in', product_ids)], fields=fields)
        return products