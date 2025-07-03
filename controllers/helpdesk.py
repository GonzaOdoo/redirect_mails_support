from odoo import http
import re
from odoo.http import request
from odoo.osv import expression

from odoo.addons.website_helpdesk.controllers.main import WebsiteForm,WebsiteHelpdesk
from odoo import _
from markupsafe import Markup
from odoo.addons.base.models.ir_qweb_fields import nl2br, nl2br_enclose
from odoo.tools import html2plaintext
import logging

_logger = logging.getLogger(__name__)

class WebsiteHelpdesk(WebsiteHelpdesk):
    
    @http.route(['/helpdesk', '/helpdesk/<model("helpdesk.team"):team>'], type='http', auth="user", website=True, sitemap=True)
    def website_helpdesk_teams(self, team=None, **kwargs):
        search = kwargs.get('search')

        teams_domain = [('use_website_helpdesk_form', '=', True)]
        if not request.env.user.has_group('helpdesk.group_helpdesk_manager'):
            if team and not team.is_published:
                raise NotFound()
            teams_domain = expression.AND([teams_domain, [('website_published', '=', True)]])

        teams = request.env['helpdesk.team'].search(teams_domain, order="id asc")
        if not teams:
            raise NotFound()

        if not team:
            if len(teams) != 1:
                return request.render("website_helpdesk.helpdesk_all_team", {'teams': teams})
            redirect_url = teams.website_url
            if teams.show_knowledge_base and not kwargs.get('contact_form'):
                redirect_url += '/knowledgebase'
            elif kwargs.get('contact_form'):
                redirect_url += '/?contact_form=1'
            return redirect(redirect_url)

        if team.show_knowledge_base and not kwargs.get('contact_form'):
            return redirect(team.website_url + '/knowledgebase')

        result = self.get_helpdesk_team_data(team or teams[0], search=search)
        result['multiple_teams'] = len(teams) > 1
        return request.render("website_helpdesk.team", result)


class WebsiteForm(WebsiteForm):

    def _handle_website_form(self, model_name, **kwargs):
        # Verificación adicional por si acaso
        _logger.info('Procesing helpdesk!')

        email = request.params.get('partner_email')
        if email:
            if request.env.user.email == email:
                partner = request.env.user.partner_id
            else:
                partner = request.env['res.partner'].sudo().search([('email', '=', email)], limit=1)
            if not partner:
                partner = request.env['res.partner'].sudo().create({
                    'email': email,
                    'name': request.params.get('partner_name', False),
                    'phone': request.params.get('partner_phone', False),
                    'company_name': request.params.get('partner_company_name', False),
                    'lang': request.lang.code,
                })
            request.params['partner_id'] = partner.id

        return super(WebsiteForm, self)._handle_website_form(model_name, **kwargs)

    def insert_record(self, request, model, values, custom, meta=None):
        # Llamamos al original para crear el ticket
        _logger.info(f"REQUEST: {request}")
        _logger.info("VALORES DEL FORMULARIO: %s", values)
        _logger.info("CUSTOM CONTENT: %s", custom)
        _logger.info("META DATA: %s", meta)
        res = super().insert_record(request, model, values, custom, meta=meta)

        # Verificamos que sea un ticket de helpdesk
        if model.sudo().model != 'helpdesk.ticket':
            return res

        ticket = request.env['helpdesk.ticket'].sudo().browse(res)
        
        # Procesar campos personalizados del formulario
        default_field = model.website_form_default_field_id
        _logger.info(default_field.name)
        if default_field:
            custom_label = Markup("<h4>%s</h4>" % _("Other Information"))
            default_field_data = values.get(default_field.name, '')
            default_content = Markup("<h4>%s</h4><p>%s</p>") % (
                default_field.name.capitalize(),
                html2plaintext(default_field_data)
            ) if default_field_data else ''

            custom_content = default_content + custom_label + Markup(custom or '')

            if default_field.ttype == 'html':
                custom_content = nl2br(custom_content)

            ticket[default_field.name] = custom_content

        self._aplicar_condiciones(ticket, custom)
        return res

    
    def _aplicar_condiciones(self, ticket, custom):
        """
        Aplica lógica condicional basada en el contenido del formulario.
        """
        # Mapeo de etiquetas visibles al valor técnico esperado
        MAPEO_AREAS = {
            'Soporte Odoo': 'odoo',
            'Soporte Lis': 'lis',
            'Problema de Red': 'red',
            'Problema de Impresora':'impr',
        }

        if custom:
            _logger.info("CUSTOM RAW DATA: %s", custom)
            
            # Procesar Área de soporte
            area_match = re.search(r'Area de soporte\s*:\s*(.*?)(?:<br\s*/?>|\n|$)', custom, re.IGNORECASE | re.DOTALL)
            if area_match:
                area_valor = area_match.group(1).strip()
                _logger.info("VALOR EXTRAÍDO DE 'ÁREA DE SOPORTE': %s", area_valor)
                valor_tecnico = MAPEO_AREAS.get(area_valor)
                if valor_tecnico:
                    ticket.write({'area': valor_tecnico})
                else:
                    _logger.warning("Valor '%s' no encontrado en el mapeo de áreas.", area_valor)

            user = request.env.user
            if user:
                cliente = user.partner_id.support_client_id if user.partner_id else False
                if cliente:
                    # Buscar el equipo según el país del cliente
                    team = request.env['helpdesk.team'].search([
                        ('country_id', '=', cliente.country.id)
                    ], limit=1)
    
                    if team:
                        _logger.info(f"Team encontrado: {team.id}")
                        ticket.write({
                            'team_id': team.id,
                            'related_client': cliente.id
                        })
                    else:
                        _logger.warning("No se encontró un equipo para el país: %s", cliente.country.name)
                        ticket.related_client = cliente.id
                else:
                    _logger.warning("Cliente no encontrado.")