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
    
    def _compute_name(self):
        for line in self:
            if not line.product_id:
                continue

            name = line.with_context(lang=line.order_partner_id.lang)._get_sale_order_line_multiline_description_sale()
            if line.is_downpayment and not line.display_type:
                context = {'lang': line.order_partner_id.lang}
                dp_state = line._get_downpayment_state()
                if dp_state == 'draft':
                    name = _("%(line_description)s (Draft)", line_description=name)
                elif dp_state == 'cancel':
                    name = _("%(line_description)s (Canceled)", line_description=name)
                del context
            line.name = name