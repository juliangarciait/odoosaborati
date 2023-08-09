from odoo import api, fields, models
from ..models.vex_soluciones_meli_config  import MELI_STATUS , MELI_SHIPPINGS

class InstanceOrderStatus(models.Model):
    _name = "vex.status.meli.shipment"
    instance = fields.Many2one('vex.instance', required=True)
    conector = fields.Selection(related="instance.conector")
    state   = fields.Selection(MELI_SHIPPINGS,string="TIPO LOGISTICA", required=True)
    warehouse_id = fields.Many2one('stock.warehouse',string="Almacen", required=True)
    confirm_albaran = fields.Boolean(default=False, string="Confirmar Albaran")
    created_invoice = fields.Boolean(default=False)
    confirm_invoice = fields.Boolean(default=False, string="Confirmar Factura")
    journal_id = fields.Many2one('account.journal', string="Diario")
    odoo_state = fields.Selection([('draft', 'Quotation'), ('send', 'Quotation Send'),
                                   ('sale', 'Sales Order'), ('done', 'Locked'),
                                   ('cancel', 'Cancelled')])
    update_price = fields.Boolean(default=False, string="Exportar Precio a Mercado Libre")
    update_stock = fields.Boolean(default=False, string="Exportar Stock a Mercado Libre")



    _sql_constraints = [
        ('unique_value', 'unique(state,instance)', 'There can be no duplication of synchronized status')
    ]