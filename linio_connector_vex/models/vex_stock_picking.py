from odoo import api, fields, models

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    def write(self,values):
        res = super(StockPicking, self).write(values)
        raise ValueError(values)
        return res

    '''
    @api.model
    def create(self,values):
        if 'sale_id' in values:
            raise ValueError(['dx',values])
        res = super(StockPicking, self).create(values)
        raise ValueError(['dx2', values])
        return res
    '''