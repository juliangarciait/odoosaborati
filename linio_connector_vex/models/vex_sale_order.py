from odoo import api, fields, models

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    docs_linio = fields.One2many('linio.documents.sol','order_id')
    conector = fields.Selection(selection_add=[('linio', 'Linio')])

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    linio_order_item_id = fields.Char()
    linio_shop_id = fields.Char()
    linio_shippingtype = fields.Char()

class DocumentsOrderLine(models.Model):
    _name = 'linio.documents.sol'
    sale_order_line = fields.Many2one('sale.order.line')
    data = fields.Binary()
    name = fields.Char()
    order_id = fields.Many2one('sale.order',related='sale_order_line.order_id')
    type = fields.Char()

