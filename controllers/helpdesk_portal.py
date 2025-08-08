# -*- coding: utf-8 -*-
from operator import itemgetter

from markupsafe import Markup
from odoo import http, _
from odoo.addons.helpdesk.controllers.portal import CustomerPortal
from odoo.http import request
from odoo.osv.expression import AND, FALSE_DOMAIN
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.tools import groupby as groupbyelem

import logging

_logger = logging.getLogger(__name__)
class CustomerPortalExtended(CustomerPortal):

    def _prepare_helpdesk_tickets_domain(self):
        _logger.info("Nuevo ticketssss")
        domain = super()._prepare_helpdesk_tickets_domain()
        _logger.info(domain)
        # Obtener el partner del usuario actual
        partner = request.env.user.partner_id

        # Si el partner es manager, filtrar por related_client = support_client_id
        if partner.is_manager:
            support_client_id = partner.support_client_id
            if support_client_id:
                domain = [('related_client', '=', support_client_id.id)]
            else:
                # Si no tiene support_client_id, no mostrar tickets
                pass
        else:
            # Si no es manager, mantener el dominio original (por ejemplo, tickets del partner)
            # El dominio original podría estar filtrando por partner_id, etc.
            # No modificamos `domain` porque ya viene del `super()`
            pass

        return domain


    def _prepare_my_tickets_values(self, page=1, date_begin=None, date_end=None, sortby=None, filterby='all', search=None, groupby='none', search_in='name'):
        values = self._prepare_portal_layout_values()
        domain = self._prepare_helpdesk_tickets_domain()
        partner = request.env.user.partner_id
        if partner.is_manager and partner.support_client_id:
            # Manager: puede ver tickets de su cliente asignado
            TicketModel = request.env['helpdesk.ticket'].sudo()
        else:
            # Usuario normal: solo ve sus propios tickets (según reglas de acceso)
            TicketModel = request.env['helpdesk.ticket']
        searchbar_sortings = {
            'create_date desc': {'label': _('Recientes')},
            'id desc': {'label': _('Referencia')},
            'name': {'label': _('Area')},
            'user_id': {'label': _('Asignado')},
            'stage_id': {'label': _('Etapa')},
            'date_last_stage_update desc': {'label': _('Última etapa actualizada')},
        }
        searchbar_filters = {
            'all': {'label': _('Todo'), 'domain': []},
            'assigned': {'label': _('Asignado'), 'domain': [('user_id', '!=', False)]},
            'unassigned': {'label': _('No asignado'), 'domain': [('user_id', '=', False)]},
            'open': {'label': _('Abierto'), 'domain': [('close_date', '=', False)]},
            'closed': {'label': _('Cerrado'), 'domain': [('close_date', '!=', False)]},
        }
        searchbar_inputs = dict(sorted(self._ticket_get_searchbar_inputs().items(), key=lambda item: item[1]['sequence']))
        searchbar_groupby = dict(sorted(self._ticket_get_searchbar_groupby().items(), key=lambda item: item[1]['sequence']))

        # default sort by value
        if not sortby:
            sortby = 'create_date desc'

        domain = AND([domain, searchbar_filters[filterby]['domain']])
        _logger.info(domain)
        if date_begin and date_end:
            domain = AND([domain, [('create_date', '>', date_begin), ('create_date', '<=', date_end)]])

        # search
        if search and search_in:
            domain = AND([domain, self._ticket_get_search_domain(search_in, search)])

        # pager
        tickets_count = TicketModel.search_count(domain)
        pager = portal_pager(
            url="/my/tickets",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'search_in': search_in, 'search': search, 'groupby': groupby, 'filterby': filterby},
            total=tickets_count,
            page=page,
            step=self._items_per_page
        )

        order = f'{groupby}, {sortby}' if groupby != 'none' else sortby
        _logger.info(domain)
        tickets = TicketModel.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        _logger.info(f"Tickets: {tickets}")
        request.session['my_tickets_history'] = tickets.ids[:100]

        if not tickets:
            grouped_tickets = []
        elif groupby != 'none':
            grouped_tickets = [TicketModel.concat(*g) for k, g in groupbyelem(tickets, itemgetter(groupby))]
        else:
            grouped_tickets = [tickets]

        values.update({
            'date': date_begin,
            'grouped_tickets': grouped_tickets,
            'page_name': 'ticket',
            'default_url': '/my/tickets',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': searchbar_filters,
            'searchbar_inputs': searchbar_inputs,
            'searchbar_groupby': searchbar_groupby,
            'sortby': sortby,
            'groupby': groupby,
            'search_in': search_in,
            'search': search,
            'filterby': filterby,
        })
        return values