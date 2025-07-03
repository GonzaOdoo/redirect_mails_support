from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)
class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    # Puedes agregar nuevos campos si los necesitas
    area = fields.Selection([('odoo','Soporte Odoo'),('lis','Soporte Lis'),('red','Problema de red'),('impr','Problema de impresora')],string="Área de soporte")
    country = fields.Many2one('res.country',related='related_client.country')
    related_client = fields.Many2one('helpdesk.custom.client',string='Cliente relacionado')


class HelpdeskTeam(models.Model):
    _inherit = 'helpdesk.team'

    country_id = fields.Many2one('res.country',string='País')
    