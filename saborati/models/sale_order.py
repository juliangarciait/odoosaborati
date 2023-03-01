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
                if line.product_id.detailed_type == 'product':  
                    qty_percentage += line.product_uom_qty * line.price_unit
                    dlv_percentage += line.qty_delivered * line.price_unit

            record.delivery_percentage = dlv_percentage / qty_percentage if qty_percentage > 0 else 0.0
    
    @api.model
    def create(self, vals_list): 
        res = super(SaleOrder, self).create(vals_list)
        
        res.medium_id = self.env.company.medium_id.id
        
        return res
    
    def action_confirm(self): 
        res = super(SaleOrder, self).action_confirm()
        
        products = []
        process_import_export_obj = False
        for line in self.order_line:
            for product in line.product_id.product_tmpl_id.shopify_product_template_ids: 
                process_import_export_obj = self.env['shopify.process.import.export'].create({
                    'shopify_instance_id' : product.shopify_instance_id.id,
                })
                products.append(product.id)
                
        if process_import_export_obj: 
            process_import_export_obj.with_context({'active_ids' : products}).shopify_selective_product_stock_export()
        
        return res
    
    def action_cancel(self): 
        res = super(SaleOrder, self).action_cancel()
        
        products = []
        process_import_export_obj = False
        for line in self.order_line: 
            for product in line.product_id.product_tmpl_id.shopify_product_template_ids: 
                process_import_export_obj = self.env['shopify.process.import.export'].create({
                    'shopify_instance_id' : product.shopify_instance_id.id,
                })
                products.append(product.id)
                
        if process_import_export_obj: 
            process_import_export_obj.with_context({'active_ids' : products}).shopify_selective_product_stock_export()
            
        return res
    
class SaleOrderLine(models.Model): 
    _inherit = 'sale.order.line'

    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        
        self._update_description()
        
        return res
            
    def _update_description(self):
        if not self.product_id:
            return
        valid_values = self.product_id.product_tmpl_id.valid_product_template_attribute_line_ids.product_template_value_ids
        # remove the is_custom values that don't belong to this template
        for pacv in self.product_custom_attribute_value_ids:
            if pacv.custom_product_template_attribute_value_id not in valid_values:
                self.product_custom_attribute_value_ids -= pacv

        # remove the no_variant attributes that don't belong to this template
        for ptav in self.product_no_variant_attribute_value_ids:
            if ptav._origin not in valid_values:
                self.product_no_variant_attribute_value_ids -= ptav

        vals = {}
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            vals['product_uom_qty'] = self.product_uom_qty or 1.0

        lang = get_lang(self.env, self.order_id.partner_id.lang).code
        product = self.product_id.with_context(
            lang=lang,
        )

        self.update({'name': product.name})
        