from odoo import api, fields, models
from odoo.exceptions import ValidationError
import threading
from ..models.vex_soluciones_meli_config import API_URL, INFO_URL, get_token
# from ..wizard.vex_soluciones_meli_action_synchro import MeliActionSynchro
from .vex_soluciones_meli_config import AUTH_URL, get_token, COUNTRIES, CURRENCIES , COUNTRIES_DOMINIO
from odoo.exceptions import ValidationError
import requests


class ApiSynchroInstance(models.Model):
    _inherit  = 'vex.instance'
    name      = fields.Char(required=True)

    app_id = fields.Char(string="App ID")
    user_id = fields.Char(string="User ID")
    secret_key = fields.Char()
    server_code = fields.Char()
    redirect_uri = fields.Char(default="https://www.vexsoluciones.com/")
    access_token = fields.Char()
    refresh_token = fields.Char()
    print_data_error_meli = fields.Boolean(default=False)


    url_get_server_code =  fields.Char(compute="get_server_code")
    @api.depends('redirect_uri','app_id')
    def get_server_code(self):
        for record in self:
            url = ''
            if record.app_id and record.redirect_uri and record.meli_country:
                code_country = COUNTRIES_DOMINIO[record.meli_country]

                url = 'https://auth.mercadolibre.com.{}/authorization?response_type=code&client_id={}&redirect_uri={}'.format(code_country,record.app_id,record.redirect_uri)
            record.url_get_server_code = url

    meli_country = fields.Selection(COUNTRIES, string='Country')
    default_currency = fields.Selection(CURRENCIES, string='Default Currency')
    
    nick = fields.Char()    
    import_products_paused = fields.Boolean(default=False)
    conector  = fields.Selection(selection_add=[('meli', 'Mercado Libre')])
    state_meli = fields.Selection([('init','Introduction'),
                                   ('init_settings','Initial Settings'),('keys','keys'),('setting','Settings')],default='init')
    field_brand = fields.Many2one('ir.model.fields', string="Campo Marca",
                                  domain=[('model_id.model','=','product.product'),
                                          ('ttype','in',['char','text','many2one'])])

    meli_logistics = fields.One2many('vex.status.meli.shipment','instance')
    not_products_full = fields.Boolean(string="No sincronizar Productos Full Envio")
    


    def get_user(self):
        if not self.nick:
            raise ValidationError('NOT NICK')
        if not self.meli_country:
            raise ValidationError('NOT COUNTRY')
        url_user = "https://api.mercadolibre.com/sites/{}/search?nickname={}".format(self.meli_country, self.nick)
        #raise ValidationError(url_user)
        item = requests.get(url_user).json()
        if 'seller' in item:
            self.user_id = str(item['seller']['id'])
        else:
            raise ValidationError(f'INCORRECT NICK OR COUNTRY: {str(item)}')

    def get_token(self):
        if not self.server_code:
            raise ValidationError('NOT SERVER CODE')
        if not self.app_id:
            raise ValidationError('Not App ID')
        if not self.secret_key:
            raise ValidationError('Not secret key')
        if not self.redirect_uri:
            raise ValidationError('Not Redirect Uri')
        headers = {"accept": "application/json",
                   "content-type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "authorization_code",
            "client_id": self.app_id,
            "client_secret": self.secret_key,
            "code": self.server_code,
            "redirect_uri": self.redirect_uri,

        }
        url = 'https://api.mercadolibre.com/oauth/token'
        r = requests.post(url, json=data, headers=headers)
        data = r.json()


        if 'access_token' in data:
            self.write({
                'access_token': data['access_token'],
                'refresh_token': data['refresh_token'],
            })
        else:
            import json
            raise ValidationError(json.dumps(data))


    def fun_test(self):
        res = super(ApiSynchroInstance, self).fun_test()
        if self.conector == 'meli':
            self.test_run()
        return res

    def test_run(self):

        access_token = self.access_token
        user_info_url = 'https://api.mercadolibre.com/users/me'
        res = requests.get(user_info_url, params={'access_token': access_token})

        if res.status_code == 200:
            raise ValidationError('Successfully connected')
        else:
            self.env['vex.synchro'].check_synchronize(self)


    @api.onchange('state_meli')
    def change_state(self):
        for record in self:
            if record.conector == 'meli':
                continue
            if record.state_meli == 'keys' and record.conector == 'meli' :
                if not record.user_id:
                    raise ValidationError('required user_id')
                if not record.app_id:
                    raise ValidationError('required app_id')
                if not record.secret_key:
                    raise ValidationError('required secret_key')
                if not record.redirect_uri:
                    raise ValidationError('required redirect_uri')
                if not record.meli_country:
                    raise ValidationError('required meli_country')
                if not record.default_currency:
                    raise ValidationError('required default_currency')
            if record.state_meli == 'setting' and record.conector == 'meli':
                if not record.server_code:
                    raise ValidationError('required server_code')
                if not record.access_token:
                    raise ValidationError('required access_token')
                if not record.refresh_token:
                    raise ValidationError('required refresh_token')

    def get_crons(self):
        if self.conector == 'meli':
            # cr0 = self.env.ref('base_conector_vex.vex_soluciones_ir_cron_automatico')
            cr1 = self.env.ref('odoo-mercadolibre.vex_soluciones_ir_cron_automatico_meli_sale')
            cr2 = self.env.ref('odoo-mercadolibre.vex_soluciones_ir_cron_automatico_meli_stock')

            dm = [('id', 'in', [cr1.id, cr2.id]), '|', ('active', '=', True), ('active', '=', False)]

            return {
                'name': ('CRONS'),
                'type': 'ir.actions.act_window',
                'view_mode': 'tree,form',
                'res_model': 'ir.cron',
                # 'views': [(view.id, 'form')],
                # 'view_id': view.id,
                'target': 'current',
                'domain': dm,

            }
        res = super().get_crons()
        return res



    def set_id_meli_erp_to_vex(self):
        for product in self.env['product.product'].search([('meli_id','!=',False)]):
            #raise ValueError([product.company_id,self.env.company,])
            if  product.company_id == self.env.company:
                product.id_vex_varition = product.meli_id
                product.id_vex = product.meli_id
                product.server_vex = self.id
                product.conector = 'meli'



