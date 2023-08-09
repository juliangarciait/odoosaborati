from odoo import api, fields, models
import threading
import requests

import logging
# import pprint
import math
# import html2text
# import subprocess
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)
# from difflib import SequenceMatcher
# from datetime import timedelta

import datetime
from datetime import datetime


id_api = "id_vex"
server_api = "server_vex"







class WooSynchro(models.TransientModel):
    _inherit = "vex.synchro"




    def import_stock(self, server, products):

        if not server.location_id:
            raise ValidationError('Debe Indicar una Localizaion')
        location = server.location_id
        variantes = self.env['product.product'].search([('product_tmpl_id', 'in', products.ids)])

        for p in variantes:
            quantun = self.env['stock.quant'].search([('product_id', '=', p.id), ('location_id', '=', location.id)])
            if not quantun:
                quantun = self.env['stock.quant'].sudo().create(
                    dict(
                        product_id=p.id,
                        location_id=location.id,
                        inventory_quantity=p.stock_vex,
                    )
                )
            else:
                quantun.sudo().inventory_quantity = p.stock_vex
            quantun.sudo()._apply_inventory()

    def insert_lines_stock(self, l, variante, inventory):

        invline = self.env['stock.inventory.line'].search(
            [('product_id', '=', int(variante.id)), ('inventory_id', '=', int(inventory.id))])
        if not invline:
            self.env['stock.inventory.line'].create({
                'product_id': variante.id,
                'product_qty': variante.stock_vex,
                'location_id': inventory.location_ids[0].id,
                'inventory_id': inventory.id,
                'product_uom_id': variante.uom_id.id,
                'company_id': inventory.company_id.id,
            })
        else:
            invline.write({
                'product_qty': variante.stock_vex
            })

        return 0


    def synchro_threading(self, data, query, server, table, accion, id_vex, api):
        th = []
        for dr in data:
            threaded_synchronization = threading.Thread(
                target=self.except_synchro(dr, query, server, table, accion, id_vex, api))
            # threaded_synchronization = threading.Thread(self.except_synchro(m, accion, wcapi, server, table, fast))
            th.append(threaded_synchronization)
        for t in th:
            t.run()

        return 0

    def except_synchro(self, data, query, server, table, accion, id_vex, api=None):
        self.synchro(data, query, server, table, accion, id_vex, api)
        '''
        try:
            self.synchro(data, query, server, table, accion,id_vex ,api)

        except:
            start_date = fields.Datetime.now()
            dx = {
                'start_date': "'{}'".format(start_date),
                'end_date': "'{}'".format(start_date),
                'description': "'Error importing {}  id {} : '".format(accion.name,data['body']['id'] if 'body' in data else data['id']),
                'state': "'error'",
                'server_vex': server.id,
                'vex_list': accion.id,
                #'conector': "{}".accion.conector
            }
            self.json_execute_create('vex.logs',dx)
        '''

