# -*- coding: utf-8 -*-

from odoo import http
import logging
import pprint
_logger = logging.getLogger(__name__)

class ControllerAngularNew(http.Controller):


    @http.route(['/meli/callbacks'], type='json', auth="public",
                methods=['POST', 'GET'], website=True, csrf=False)
    def create_multi_activity_material(self, **post):
        data = http.request.jsonrequest
        _logger.info(f''' MELI DATA CALLBACK ''',pprint.pformat(data))

# class Odoo-mercadolibre(http.Controller):
#     @http.route('/odoo-mercadolibre/odoo-mercadolibre/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/odoo-mercadolibre/odoo-mercadolibre/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('odoo-mercadolibre.listing', {
#             'root': '/odoo-mercadolibre/odoo-mercadolibre',
#             'objects': http.request.env['odoo-mercadolibre.odoo-mercadolibre'].search([]),
#         })

#     @http.route('/odoo-mercadolibre/odoo-mercadolibre/objects/<model("odoo-mercadolibre.odoo-mercadolibre"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('odoo-mercadolibre.object', {
#             'object': obj
#         })
