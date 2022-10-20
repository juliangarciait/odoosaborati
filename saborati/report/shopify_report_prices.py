# -*- encoding: utf-8 -*-

import time
from odoo import models, api, _, fields
from odoo.exceptions import ValidationError
from xlsxwriter.utility import xl_rowcol_to_cell
from datetime import datetime

import logging 
_logger = logging.getLogger(__name__)

class ShopifyReportPrices(models.AbstractModel): 
    _name = 'report.saborati.shopify_report_prices_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objects): 
        records = []
        if product.shopify_product_template_ids.shopify_instance_id.shopify_b2b_pricelist_id: 
            for product in objects:
                b2b_record = {
                    'name'                    : '',
                    'priority'                : 0,
                    'status'                  : 'enable', 
                    'apply_to'                : 'Customer tags',
                    'customer_emails'         : '',
                    'customer_tags'           : '',
                    'product_condition_type'  : 'Specific products',
                    'product_titles'          : '', 
                    'sku'                     : '',
                    'barcode'                 : '',
                    'product_collections'     : '',
                    'product_tags'            : '',
                    'discount_type'           : 'apply a price to selected products',
                    'discount_value'          : 0.00,
                    'start_date'              : '',
                    'end_date'                : '',
                    'exc_customer_tags'       : '',
                    'exclude_from'            : 'None',
                }
                if product.shopify_product_template_ids: 
                    b2b_price =  product.shopify_product_template_ids.shopify_instance_id.shopify_b2b_pricelist_id.get_product_price(product, 1.0, False)

                    b2b_record['name'] = 'b' + str(product.id) + '-' + product.default_code
                    b2b_record['product_titles'] = product.name
                    b2b_record['sku'] = product.default_code
                    b2b_record['customer_tags'] = 'b2b'
                    b2b_record['discount_value'] = b2b_price
                    records.append(b2b_record)

        if product.shopify_product_template_ids.shopify_instance_id.shopify_wholesale_pricelist_id: 
            for product in objects: 
                wholesale_record = {
                    'name'                    : '',
                    'priority'                : 0,
                    'status'                  : 'enable', 
                    'apply_to'                : 'Customer tags',
                    'customer_emails'         : '',
                    'customer_tags'           : '',
                    'product_condition_type'  : 'Specific products',
                    'product_titles'          : '', 
                    'sku'                     : '',
                    'barcode'                 : '',
                    'product_collections'     : '',
                    'product_tags'            : '',
                    'discount_type'           : 'apply a price to selected products',
                    'discount_value'          : 0.00,
                    'start_date'              : '',
                    'end_date'                : '',
                    'exc_customer_tags'       : '',
                    'exclude_from'            : 'None',
                }
                if product.shopify_product_template_ids: 
                    wholesale_price = product.shopify_product_template_ids.shopify_instance_id.shopify_wholesale_pricelist_id.get_product_price(product, 1.0, False)

                    wholesale_record['name'] = 'w' + str(product.id) + '-' + product.default_code
                    wholesale_record['product_titles'] = product.name
                    wholesale_record['sku'] = product.default_code
                    wholesale_record['customer_tags'] = 'wholesale'
                    wholesale_record['discount_value'] = wholesale_price
                    records.append(wholesale_record)
                    
        if not product.shopify_product_template_ids.shopify_instance_id.shopify_wholesale_pricelist_id and not product.shopify_product_template_ids.shopify_instance_id.shopify_b2b_pricelist_id: 
            raise ValidationError ("No se puede generar reporte porque no se tiene asignada listas de precio para B2B ni Wholesale")
            
        workbook.set_properties({
            'comments' : 'Created with Python and XlsxWrite from Odoo 15.0'
        })
        sheet = workbook.add_worksheet(_('Reporte de precios para shopify'))
        sheet.set_landscape()
        sheet.fit_to_pages(1, 0)
        sheet.set_zoom(100)
        sheet.set_column(0, 0, 15)
        sheet.set_column(1, 2, 20)
        sheet.set_column(3, 3, 10)
        sheet.set_column(4, 46, 15)

        year = fields.Date.today().year
        month = fields.Date.today().month
        sheet_title = ['name', 'priority', 'status', 'apply_to', 'customer_emails', 'customer_tags', 'product_condition_type', 'product_titles', 'sku', 'barcode', 'product_collections', 'product_tags', 'discount_type', 'discount_value', 'start_date', 'end_date', 'exc_customer_tags', 'exclude_from']

        sheet.set_row(0, None, None, {'collapsed': 1})
        bold = workbook.add_format({})
        money = workbook.add_format({'num_format' : '#,##0'})

        sheet.write_row(0, 0, sheet_title)

        i = 1 

        for record in records: 
            sheet.write(i, 0, record.get('name'), bold)
            sheet.write(i, 1, record.get('priority'), bold)
            sheet.write(i, 2, record.get('status'), bold)
            sheet.write(i, 3, record.get('apply_to'), bold)
            sheet.write(i, 4, record.get('customer_emails'), bold)
            sheet.write(i, 5, record.get('customer_tags'), bold)
            sheet.write(i, 6, record.get('product_condition_type'), bold)
            sheet.write(i, 7, record.get('product_titles'), bold)
            sheet.write(i, 8, record.get('sku'), bold)
            sheet.write(i, 9, record.get('barcode'), bold)
            sheet.write(i, 10, record.get('product_collections'), bold)
            sheet.write(i, 11, record.get('product_tags'), bold)
            sheet.write(i, 12, record.get('discount_type'), bold)
            sheet.write(i, 13, float(record.get('discount_value')), bold)
            sheet.write(i, 14, record.get('start_date'), bold)
            sheet.write(i, 15, record.get('end_date'), bold)
            sheet.write(i, 16, record.get('exc_customer_tags'), bold)
            sheet.write(i, 17, record.get('exclude_from'), bold)
            i += 1




