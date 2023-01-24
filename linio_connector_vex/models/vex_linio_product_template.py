from odoo import api, fields, models
from odoo.addons.payment.models.payment_acquirer import ValidationError
import base64
import requests
# from .vex_soluciones_meli_config import CONDITIONS

import subprocess
import sys


def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])


try:
    from dicttoxml import dicttoxml
except:
    install('dicttoxml')

from dicttoxml import dicttoxml


class Product(models.Model):
    _inherit = 'product.template'
    conector = fields.Selection(selection_add=[('linio', 'Linio')])
    check_export_linio = fields.Boolean(default=False)

    # url_image         = fields.Char(string="url_image")

    def export_stock_linio(self,instance,record):

        warehouse_x_export = record.warehouse_stock_vex
        if instance.export_stock_all_products:
            warehouse_x_export = instance.warehouse_stock_vex
        if warehouse_x_export:
            data = self.env['report.stock.report_product_product_replenishment'].with_context(
                warehouse=warehouse_x_export.id)._get_report_data([record.id])
        else:
            data = self.env['report.stock.report_product_product_replenishment']._get_report_data([record.id])

        #future_virtual_available = data['virtual_available'] + data['qty']['in'] - data['qty']['out']
        future_virtual_available = data['virtual_available']

        if future_virtual_available < instance.export_stock_min:
            future_virtual_available = 0
        # raise ValidationError(str(future_virtual_available))
        data_xml = f'''
        <Product>
        <SellerSku>{record.id_vex}</SellerSku>
        <Quantity>{future_virtual_available}</Quantity>
        </Product>
        '''
        return data_xml



    def update_conector_vex(self):
        accion = self.env['vex.restapi.list'].search([('conector','=','linio'),('argument','=','products')])
        import time
        msg = 'Actualizacion Finalizada'

        servers_share = self.env['vex.instance'].search([('share_multi_instances','=',True)])

        products_updated = []


        numero_vueltas =  round(len(self) / 51)  # 0 1 2 3 .. 50
        numero_vueltas = int(numero_vueltas)



        for instance in servers_share:
            contador = 0
            for n in range(numero_vueltas):
                dt_xml = ''
                name_products = ''

                # agrupar los productos
                for record in self:
                    if contador < 50 :
                        dt_xml += self.export_stock_linio(instance, record)
                        name_products += str(record.id) +','
                        contador += 1
                    else:
                        contador = 0

                data_xml = f'''<?xml version="1.0" encoding="UTF-8" ?>
                                                            <Request>
                                                            {dt_xml}
                                                            </Request>
                                                    '''
                if dt_xml != '':
                    start_date = fields.Datetime.now()
                    res = instance.post_export_linio('ProductUpdate', None, data_xml).json()
                    end_date = fields.Datetime.now()
                    dx = {
                        'start_date': "'{}'".format(start_date),
                        'end_date': "'{}'".format(end_date),
                        'description': f"'actualizacion de productos terminada:  {str(n)}'",
                        'state': "'done'",
                        'server_vex': instance.id,
                        'vex_list': accion.id,
                        'detail': f"'productos:  {name_products}'",
                    }

                    self.env['vex.synchro'].json_execute_create('vex.logs', dx)
                    time.sleep(30)
                    msg += instance.name + '\n'
                    # msg += '\n'+data_xml
                    # msg +=  '\n'+str(n)

                    if not 'SuccessResponse' in res:
                        msg += str(res)

        return self.env['popup.vex'].get_message(msg)

    def export_conector_vex(self):
        instance = self.env['vex.instance'].search([])[0]

        for record in self:
            data_xml = '''
            <?xml version="1.0" encoding="UTF-8" ?>
<Request>
<Product>
<Brand>ASM</Brand>
<Description>product description</Description>
<Name>Product</Name>
<Price>123</Price>
<PrimaryCategory>12</PrimaryCategory>
<SellerSku>ASM_A8010</SellerSku>
<TaxClass>default</TaxClass>
</Product>
</Request>
            '''

            #raise ValidationError(data_xml)
            res = instance.post_export_linio('ProductCreate', None, data_xml).json()
            raise ValidationError(str(res))
            print(res)


class Image(models.Model):
    _inherit = 'product.image'
    conector = fields.Selection(selection_add=[('linio', 'Linio')])
