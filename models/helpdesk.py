from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)
class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    # Puedes agregar nuevos campos si los necesitas
    area = fields.Selection([('Soporte Odoo','Soporte Odoo'),('Soporte Lis','Soporte Lis'),('Problema de Red','Soporte IT')],string="Área de soporte")

