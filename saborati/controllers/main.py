# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

import base64
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class ImageUrl(http.Controller):   
   
    @http.route('/cl/i/<string:encodedimage>', type='http', auth='public')
    def create_image_collection_url(self, encodedimage=''):
        if encodedimage:
            try:
                decode_data = base64.urlsafe_b64decode(encodedimage)
                res_id = str(decode_data, "utf-8")
                status, headers, content = request.env['ir.http'].sudo().binary_content(
                    model='product.collection', id=res_id,
                    field='image_1920')
                content_base64 = base64.b64decode(content) if content else ''
                _logger.info("Image found with status %s", str(status))
                headers.append(('Content-Length', len(content_base64)))
                return request.make_response(content_base64, headers)
            except Exception:
                return request.not_found()
        return request.not_found()
    
    