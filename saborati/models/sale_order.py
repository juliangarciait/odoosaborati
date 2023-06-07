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
                mrp_bom_id = False
                if line.product_id.detailed_type == 'product':  
                    mrp_bom_id = self.env['mrp.bom'].search([('product_id', '=', line.product_id.id), ('type', '=', 'phantom')], order='write_date desc', limit=1)
                    if mrp_bom_id: 
                        products = []
                        product_qty = 0
                        for mrp_bom_line in mrp_bom_id.bom_line_ids: 
                            if mrp_bom_line.product_id.detailed_type == 'product':
                                products.append(mrp_bom_line.product_id.id)
                                product_qty += mrp_bom_line.product_qty           
                        qty_to_deliver = product_qty * line.product_uom_qty
                        
                        if qty_to_deliver > 0: 
                            qty_done = 0
                            pickings = self.env['stock.picking'].search([('sale_id', '=', line.order_id.id), ('state', '=', 'done')])
                            for picking in pickings.move_ids_without_package:
                                if picking.product_id.id in products: 
                                    qty_done += picking.quantity_done
                            
                            line.qty_delivered = (qty_done * line.product_uom_qty / qty_to_deliver) 
                        
                    dlv_percentage += line.qty_delivered * line.price_unit
                    qty_percentage += line.product_uom_qty * line.price_unit

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

        self.update({'name': product.display_name})
    
    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        if not self.product_uom or not self.product_id:
            self.price_unit = 0.0
            return
        if self.order_id.pricelist_id and self.order_id.partner_id:
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id,
                quantity=self.product_uom_qty,
                date=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position')
            )
            #self.price_unit = product._get_tax_included_unit_price(
            #    self.company_id or self.order_id.company_id,
            #    self.order_id.currency_id,
            #    self.order_id.date_order,
            #    'sale',
            #    fiscal_position=self.order_id.fiscal_position_id,
            #    product_price_unit=self._get_display_price(product),
            #    product_currency=self.order_id.currency_id
            #)
        