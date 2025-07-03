from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)
class HelpdeskTicket(models.Model):
    _name = 'helpdesk.custom.client'

    name = fields.Char('Cliente')
    country = fields.Many2one('res.country',string='Pais')
    partner_ids = fields.One2many(
        'res.partner',
        'support_client_id',
        string='Órdenes de venta asociadas',
        help="Seleccione órdenes de venta existentes para asociar a este viaje"
    )