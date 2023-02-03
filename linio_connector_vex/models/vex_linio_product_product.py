from odoo import api, fields, models
from odoo.addons.payment.models.payment_acquirer import ValidationError

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def export_stock_linio(self, instance, record):

        warehouse_x_export = record.warehouse_stock_vex
        if instance.export_stock_all_products:
            warehouse_x_export = instance.warehouse_stock_vex
        if warehouse_x_export:
            data = self.env['report.stock.report_product_product_replenishment'].with_context(
                warehouse=warehouse_x_export.id)._get_report_data(False,[record.id])
        else:
            data = self.env['report.stock.report_product_product_replenishment']._get_report_data(False,[record.id])

        #raise ValidationError(str(data))

        # future_virtual_available = data['virtual_available'] + data['qty']['in'] - data['qty']['out']
        future_virtual_available = data['virtual_available']

        if future_virtual_available < instance.export_stock_min:
            future_virtual_available = 0
        # raise ValidationError(str(future_virtual_available))

        id_vex = record.id_vex_varition or record.id_vex

        data_xml = f'''
            <Product>
            <SellerSku>{id_vex}</SellerSku>
            <Quantity>{future_virtual_available}</Quantity>
            </Product>
            '''
        #raise ValidationError(str([data_xml,data['virtual_available']]))
        return data_xml

    def update_conector_vex(self):
        accion = self.env['vex.restapi.list'].search([('conector', '=', 'linio'), ('argument', '=', 'products')])
        import time
        msg = 'Actualizacion Finalizada'

        servers_share = self.env['vex.instance'].search([('share_multi_instances', '=', True)])

        #raise ValidationError('que esta pasando aqui')

        numero_vueltas = round(len(self) / 51)  # 0 1 2 3 .. 50
        numero_vueltas = int(numero_vueltas)

        if self and numero_vueltas == 0:
            numero_vueltas = 1

        #raise ValidationError(str([servers_share,numero_vueltas]))

        for instance in servers_share:
            contador = 0
            for n in range(numero_vueltas):
                dt_xml = ''
                name_products = ''

                # agrupar los productos
                for record in self:
                    if contador < 50:
                        dt_xml += self.export_stock_linio(instance, record)
                        name_products += str(record.id) + ','
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

                    #raise   ValidationError(str([res,data_xml]))
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

                    #raise ValidationError(str(dx))



                    self.env['vex.synchro'].json_execute_create('vex.logs', dx)
                    time.sleep(30)
                    msg += instance.name + '\n'
                    # msg += '\n'+data_xml
                    # msg +=  '\n'+str(n)

                    if not 'SuccessResponse' in res:
                        msg += str(res)



        return self.env['popup.vex'].get_message(msg)

