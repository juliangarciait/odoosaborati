from odoo import api, fields, models
from odoo.addons.payment.models.payment_acquirer import ValidationError
#import threading

from urllib.parse import urlencode
from datetime import datetime
from hashlib import sha256
from hmac import HMAC
import pytz
import requests

#url = 'https://sellercenter-api.linio.com.pe'


class ApiSynchroInstance(models.Model):
    _inherit  = 'vex.instance'
    conector = fields.Selection(selection_add=[('linio', 'Linio')])
    user_id = fields.Char(string="User ID")
    api_key = fields.Char(string="API Key")
    url_linio = fields.Char(string="URL")

    use_warehousetype = fields.Boolean(string="Usar Alamcenes x Tipo de Envio")
    warehouse_dropshipping = fields.Many2one('stock.warehouse',string="Almacen x Envio Directo (Dropshipping)")
    warehouse_ownwarehouse = fields.Many2one('stock.warehouse', string="Almacen x Almacen Propio (Own Warehouse)")

    def get_crons_linio(self):
        cr0 = self.env.ref('base_conector_vex.vex_soluciones_ir_cron_automatico')
        cr1 = self.env.ref('linio_connector_vex.vex_soluciones_ir_cron_automatico_linio_sale')
        cr2 = self.env.ref('linio_connector_vex.vex_soluciones_ir_cron_automatico_linio_stock')

        dm = [('id', 'in', [cr0.id,cr1.id,cr2.id]),'|',('active','=',True),('active','=',False)]

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

    def fun_test(self):
        res = super(ApiSynchroInstance, self).fun_test()
        if self.conector == 'linio':
            return  self.test_run_linio()
        return res

    def test_run_linio(self):
        if not self.user_id:
            raise ValidationError('NOT USER')
        if not self.api_key:
            raise ValidationError('NOT API KEY')


        res = self.api_get_linio('FeedCount').json()

        if 'SuccessResponse' in res:


            return self.env['popup.vex'].get_message('Successful Connection')

        else:

            raise ValidationError(str(res))


    def api_get_linio(self,action,others=None):
        tz = pytz.timezone('America/Lima')
        parameters = {
            'UserID': self.user_id,
            #'Version': instance.version,
            'Version': '1.0',
            'Action': action,
            'Format': 'JSON',
            'Timestamp': datetime.now(tz=tz).isoformat(),
        }

        if others:
            parameters.update(others)

        concatenated = urlencode(sorted(parameters.items()))
        parameters['Signature'] = HMAC(bytes(self.api_key, 'utf-8'), bytes(concatenated, 'utf-8'),
                                       sha256).hexdigest()
        res = requests.get(self.url_linio, params=parameters)
        #raise ValidationError(str(res.json()))
        #raise ValidationError(len(res.json()['SuccessResponse']['Body']['Products']['Product']))

        return res

    def post_export_linio(self,action, others=None, data=None):
        tz = pytz.timezone('America/Lima')
        parameters = {
            'UserID': self.user_id,
            'Version': '1.0',
            'Action': action,
            'Format': 'JSON',
            'Timestamp': datetime.now(tz=tz).isoformat(),
        }

        if others:
            parameters.update(others)

        concatenated = urlencode(sorted(parameters.items()))
        parameters['Signature'] = HMAC(bytes(self.api_key, 'utf-8'), bytes(concatenated, 'utf-8'),
                                       sha256).hexdigest()

        headers = {

            "Accept": "application/xml",

            "Content-Type": "application/x-www-form-urlencoded"

        }
        res = requests.post(self.url_linio, params=parameters, data=data, headers=headers)

        #url = "https://sellercenter-api.linio.com.pe?Action=ProductUpdate&Format=JSON&Timestamp=2022-08-29T00%3A31%3A02-05%3A00&UserID=decorfanti%40gmail.com&Version=1.0&Signature=d3e7ec0758a80866b5b2f0cc069804a0a9b078f841c7a289c6aafc147d1bd3b0"
        #res = requests.post(url,data=data, headers=headers)
        return res