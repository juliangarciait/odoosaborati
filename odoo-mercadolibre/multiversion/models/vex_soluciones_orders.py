from odoo import api, fields, models

from  .vex_soluciones_meli_config  import MELI_STATUS , MELI_SHIPPINGS
from odoo.exceptions import UserError

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    meli_shop_id = fields.Char()
    shipping_vex = fields.Float()
    meli_shipment_cost = fields.Float('Envio Meli Cost')
    fee_vex = fields.Float()

class Orders(models.Model):
    _inherit                = 'sale.order'
    conector                = fields.Selection(selection_add=[('meli', 'Mercado Libre')])
    meli_logistic_type      = fields.Selection(MELI_SHIPPINGS,string="Meli Tipo de logística")
    meli_status             = fields.Selection(MELI_STATUS, string='Meli Order Status')
    meli_shipping_id        = fields.Char('Meli Shipping Id')
    meli_pack_id            = fields.Char('Meli Pack Id')
    meli_shipment_cost = fields.Float('Envio Meli Cost')
   
    def _prepare_invoice(self):
        res = super()._prepare_invoice()
        if self.server_vex and self.server_vex.journal_id:
            res['journal_id'] = self.server_vex.journal_id.id
        
        if self.meli_logistic_type and self.server_vex:
            logistic = self.env['vex.status.meli.shipment'].search([('instance', '=', self.server_vex.id), ('state', '=', self.meli_logistic_type)])
            #raise ValueError([logistic,self.meli_logistic_type])
            if logistic.journal_id:
                #raise ValueError(logistic.journal_id.id)
                res['journal_id'] = logistic.journal_id.id
                
        #raise ValueError('kk')
                

        return res

    def manually_validate_logistic(self):
        for record in self:
            logis = record.meli_logistic_verify_warehouse()
            record.meli_logistic_verify_albaran(logis)


    def meli_logistic_verify_warehouse(self):
        logistic = self.env['vex.status.meli.shipment'].search(
            [('instance', '=', self.server_vex.id), ('state', '=', self.meli_logistic_type)])
        if self.state == 'draft':

            if logistic:
                self.warehouse_id = logistic.warehouse_id.id


        return logistic

    def meli_logistic_verify_albaran(self,logistic):

        if self.state in ['sale','done']  and logistic and self.picking_ids and self.server_vex.verify_albaranes:
            if logistic.confirm_albaran:
                for pickind in self.picking_ids:
                    if pickind.state == 'assigned':
                        for l in pickind.move_ids_without_package:
                            l.quantity_done = l.product_uom_qty
                        try:
                            pickind.button_validate()
                        except:
                            return

            #raise ValueError([self.name,self.picking_ids[0].state])
        #raise ValueError([self.name, self.state,logistic , self.picking_ids[0].state])
        
        
    def validate_create_line_shipment(self):
        for record in self:
            if record.state == 'draft' and record.server_vex and record.server_vex.shipment:
                if record.server_vex.shipment == 'save_line':
                    if not record.server_vex.product_shipment:
                        raise UserError('NO DEFINIO UN PRODUCTO X EL ENVIO')
                    exist_line = self.env['sale.order.line'].search(
                        [('order_id', '=', record.id), ('is_vex_line_shipment', '=', True)])
                    if exist_line:
                        if record.shipping_vex != 0:
                            exist_line.price_unit = record.shipping_vex
                            exist_line.product_uom_qty = 1
                        else:
                            exist_line.unlink()


                    else:
                        if record.shipping_vex != 0:
                            exist_line = self.env['sale.order.line'].create({
                                'order_id': record.id,
                                'is_vex_line_shipment': True,
                                'price_unit': record.shipping_vex,
                                'product_uom_qty': 1,
                                'product_id': record.server_vex.product_shipment.id,
                                'name': record.server_vex.product_shipment.display_name
                            })
    def order_validate_state_meli(self):

        for exist in self:
            if not exist.order_line:
                continue

            if exist.server_vex.sudo().id_external_aditional_order:
                if exist[exist.server_vex.sudo().id_external_aditional_order.name]:
                    continue


            exist.validate_create_line_shipment()
            logistic = exist.meli_logistic_verify_warehouse()
            server = exist.server_vex

            #raise ValueError([exist.state,exist.meli_status,exist.meli_logistic_type,logistic])
            if logistic and logistic.odoo_state:
                state_state = logistic
            else:
                state_state = self.env['vex.instance.status.orders'].search(
                    [('instance', '=', server.id), ('value', '=', exist.meli_status)])

            # raise ValueError([logistic, exist.state,state])
            if exist.state not in ['sale', 'done','cancel'] and state_state.odoo_state in ['done', 'sale']:
                available_invoice = True
                for line in exist.order_line:
                    if not  line.product_id:
                        continue
                    if line.product_id.invoice_policy == 'delivery' and line.qty_delivered == line.product_uom_qty:
                        available_invoice = False
                if available_invoice:
                    exist.action_confirm()

                # raise ValueError([logistic, exist.state])

            else:
                if state_state.odoo_state in ['cancel'] and exist.state not in ['cancel']:
                    exist.action_cancel()
                else:
                    if exist.state not in ['sale', 'done','cancel']:
                        exist.state = 'draft' if not state_state else state_state.odoo_state

            # raise ValueError([logistic, exist.state])

            exist.meli_logistic_verify_albaran(logistic)

            if exist and state_state and not exist.invoice_ids and state_state.created_invoice and exist.state in [
                'sale',
                'done']:
                exist._create_invoices()
                #try:
                #    exist._create_invoices()
                #except:
                #    pass

            if state_state and state_state.confirm_invoice and exist.invoice_ids:
                for invoice in exist.invoice_ids:
                    if invoice.state == 'draft':
                        try:
                            invoice.action_post()
                        except:
                            return
        









    
    _sql_constraints = [
        ('unique_id_order_meli', 'unique(id_vex,conector ,server_vex)', 'There can be no duplication of synchronized Orders')
    ]