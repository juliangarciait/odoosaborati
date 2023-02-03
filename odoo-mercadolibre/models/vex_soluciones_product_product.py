from odoo import api, fields, models
from odoo.addons.payment.models.payment_acquirer import ValidationError
import requests
from .vex_soluciones_meli_config import CONDITIONS

class ProductProduct(models.Model):
    _inherit = 'product.product'
    product_condition = fields.Selection(CONDITIONS, string='Product Condition', help='Default product condition')
    #brand = fields.Char(string="Product Brand")
    #questions_count = fields.Integer(required=False, compute='_count_questions')
    #questions = fields.One2many('meli.questions', 'product_id')
    active_meli = fields.Boolean(default=True)
    buying_mode = fields.Selection([('buy_it_now', 'buy it now'), ('classified', 'classified')])
    listing_type_id = fields.Selection([('free', 'free'), ('bronze', 'bronze'),
                                        ('gold_special', 'gold special')])
    name_product_meli = fields.Text(string="Titulo")
    description_meli = fields.Text(string="Descripcion")


    def update_conector_vex(self):


        if len(self) == 1 :
            name = self.name_product_meli or self.name
            if self.id_vex_varition or self.id_vex:
                # id_vex =  self.id_vex_varition or self.id_vex

                dx = {
                    'default_product': self.id,
                    # 'default_brand': self.brand ,
                    'default_quantity': self.qty_available,
                    'default_condition': self.product_condition,
                    'default_buying_mode': self.buying_mode,
                    'default_listing_type_id': self.listing_type_id,
                    'default_name_product_meli': name,
                    'default_description_meli': self.description_meli

                }

                return {
                    'name': ('Update to ML'),
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'meli.export.unite',
                    'target': 'new',
                    # 'res_id': wiz.id,
                    'context': dx
                }
            else:
                if not self.image_1920:
                    raise ValidationError('THIS PRODUCT DONT HAVE IMAGE')

                dx = {
                    'default_product': self.id,
                    # 'default_brand': self.brand ,
                    'default_quantity': self.qty_available,
                    # 'default_condition': self.product_condition,
                    # 'default_buying_mode': self.buying_mode,
                    # 'default_listing_type_id': self.listing_type_id,
                    'default_name_product_meli': name,
                    'default_description_meli': self.description_meli
                    # 'default_category': categ
                }

                if self.product_condition:
                    dx['default_condition'] = self.product_condition
                if self.buying_mode:
                    dx['default_buying_mode'] = self.buying_mode
                if self.listing_type_id:
                    dx['default_listing_type_id'] = self.listing_type_id

                return {
                    'name': ('Export to ML'),
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'meli.export.unite',
                    'target': 'new',
                    # 'res_id': wiz.id,
                    'context': dx
                }

        else:

            accion = self.env['vex.restapi.list'].search([('conector', '=', 'meli'), ('argument', '=', 'products')])
            for server in self.env['vex.instance'].search([]):
                name_products = ''
                n = ''
                start_date = fields.Datetime.now()
                for record in self:
                    if record.id_vex_varition or record.id_vex:
                        self.env['meli.export'].export_product(record, server,None,False)
                        name_products += record.display_name + ' , '
                        n += str(record.id) + ' ,'
                end_date = fields.Datetime.now()
                if n != '':
                    dx = {
                        'start_date': "'{}'".format(start_date),
                        'end_date': "'{}'".format(end_date),
                        'description': f"'actualizacion de productos terminada:  {str(n)}'",
                        'state': "'done'",
                        'server_vex': server.id,
                        'vex_list': accion.id,
                        'detail': f"'productos:  {name_products}'",
                    }
                    self.env['vex.synchro'].json_execute_create('vex.logs', dx)










