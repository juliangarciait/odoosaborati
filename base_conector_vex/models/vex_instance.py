from odoo import api, fields, models
import requests
from odoo.exceptions import UserError
import datetime
from datetime import timedelta
class VexInstance(models.Model):
    _name        = "vex.instance"
    _description = "Instance Vex"
    name = fields.Char(string='Name', required=True)
    company = fields.Many2one('res.company')
    picking_policy = fields.Selection([('direct', 'Deliver each product when available'),
                                       ('one', 'Deliver all products at once')], default='direct')
    warehouse = fields.Many2one('stock.warehouse')
    location_id = fields.Many2one('stock.location', string="Stock Location",related="warehouse.lot_stock_id")

    journal_id = fields.Many2one('account.journal', domain="[('type','in',('bank','cash'))]")
    payment_term = fields.Many2one('account.payment.term')
    use_date_specific = fields.Boolean(string="Usar Fecha Especifica")
    latest_days_order = fields.Integer(string="Ultimos N dias")
    order_after = fields.Datetime()
    order_after_days = fields.Datetime(compute="get_order_after_days")
    def get_order_after_days(self):
        for record in self:
            record.order_after_days = fields.Datetime.now() -timedelta(days=record.latest_days_order)

    all_orders = fields.Boolean(defaul=True)
    all_status_orders = fields.Boolean(defaul=True, string='All the states')
    total_products = fields.Integer(compute='_generate_total')
    total_categories = fields.Integer(compute='_generate_total')
    total_customers = fields.Integer(compute='_generate_total')
    total_orders = fields.Integer(compute='_generate_total')
    conector = fields.Selection([])
    categ_id = fields.Many2one('product.category', string="product category")
    active_automatic = fields.Boolean(default=False, string="Activate automatic sync")

    pricelist = fields.Many2one('product.pricelist')
    sales_team = fields.Many2one('crm.team', string="Sales Team")
    import_lines = fields.One2many('vexlines.import','instance')
    sequence_id = fields.Many2one('ir.sequence')
    state_orders = fields.One2many('vex.instance.status.orders','instance')

    import_stock = fields.Boolean(default=True)
    url_license = fields.Char(default='https://www.pasarelasdepagos.com/', required=True)
    license_secret_key = fields.Char(default='587423b988e403.69821411')
    license_key = fields.Char()
    active_list = fields.Many2one('vex.restapi.list')
    search_sku = fields.Boolean()
    tax_id = fields.Many2one('account.tax',string='Impuesto')

    discount_fee = fields.Selection([
        ('save','Guardar como Dato'),
        ('save_line','Guardar como Linea')
    ],string="Comision"
    )

    shipment = fields.Selection([
        ('save','Guardar como Dato'),
        ('save_line','Guardar como Linea')
    ],string="Envio"
    )

    user_sale_id = fields.Many2one('res.users',string="Vendedor Ventas")
    export_stock_min = fields.Integer(string="Stock Minimo a exportar")
    share_multi_instances = fields.Boolean(default=False,string="Compartir Productos entre cuentas")
    export_stock_all_products = fields.Boolean(default=True,string="Exportar Stock todos los productos")
    warehouse_stock_vex = fields.Many2one('stock.warehouse', string="Almacen x Exportar")
    type_document = fields.Many2one('l10n_latam.identification.type',string="Tipo de Identificacion")




    def validate_licence(self):
        URL = f"https://www.pasarelasdepagos.com?license_key={self.license_key}&slm_action=slm_check&secret_key={self.license_secret_key}"
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        r = requests.get(url=URL, headers=headers).json()
        if not 'result' in r:
            return
            raise UserError(str(r))
        if r['result'] != 'success':
            raise UserError('NO TINES LECENCIA VALIDA')

    @api.model
    def default_get(self,fields):
        res = super(VexInstance,self).default_get(fields)
        sq = self.env['ir.sequence'].search([('code','=','sale.order')],limit=1)
        if sq:
            res.update({'sequence_id': sq.id})
        return res

    def _generate_total(self):
        for record in self:
            # buscar todos los productos para este servidor
            products = self.env['product.template'].search_count(
                [('id_vex', '!=', False), ('server_vex', '=', int(record.id))])
            record.total_products = products
            # categories = self.env['product.public.category'].search_count([(id_api, '!=', False), (server_api, '=', int(record.id))])
            record.total_categories = 0
            # customers = self.env['res.partner'].search_count([(id_api, '!=', False), (server_api, '=', int(record.id))])
            record.total_customers = 0
            # orders = self.env['sale.order'].search_count([(id_api, '!=', False), (server_api, '=', int(record.id))])
            record.total_orders = 0

    def fun_test(self):
        self.validate_licence()
        return 0

    def stop_sync(self):
        cron = self.env['ir.cron'].search([('argument', '=', 'vex_cron'),
                                           "|",
                                           ("active", "=", True), ("active", "=", False)])
        if cron:
            cron.active = False

    def view_setting_sinc_lines(self):
        cron = self.env['ir.cron'].search([('argument', '=', 'vex_cron'),
                                           "|",
                                           ("active", "=", True), ("active", "=", False)])

        view = self.env.ref('base.ir_cron_view_form', False)

        # picking_type_id = self.picking_type_id or self.picking_id.picking_type_id
        return {
            'name': ('Configurar Cron'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'ir.cron',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'current',
            'res_id': cron.id,
            'context': dict(
                cron.env.context,
            ),
        }

        return

    class VexImportLines(models.Model):
        _name = "vexlines.import"
        url = fields.Char(required=True)
        orden = fields.Integer(required=True)
        instance = fields.Many2one('vex.instance',required=True)
        accion = fields.Many2one('vex.restapi.list',required=True)
        state = fields.Selection([('done','Realizado'),('wait','Pendiente')],default="wait")


