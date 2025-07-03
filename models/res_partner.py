from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)
class ResPartner(models.Model):
    _inherit = 'res.partner'
    support_client_id = fields.Many2one('helpdesk.custom.client',string='Cliente de soporte')
    