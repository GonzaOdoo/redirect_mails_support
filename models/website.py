# Part of Odoo. See LICENSE file for full copyright and licensing details.

import werkzeug.exceptions
import werkzeug.urls

from werkzeug.urls import url_parse

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.http import request
from odoo.tools.translate import html_translate
import logging

_logger = logging.getLogger(__name__)
class Menu(models.Model):

    _inherit = "website.menu"

    country_id = fields.Many2one('res.country',string = "País")

    def _compute_visible(self):
        for menu in self:
            visible = True
            _logger.info("Computing visible")
            if menu.page_id and not menu.env.user._is_internal():
                _logger.info(menu.env.user)
                page_sudo = menu.page_id.sudo()
                if (not page_sudo.is_visible
                    or (not page_sudo.view_id._handle_visibility(do_raise=False)
                        and page_sudo.view_id._get_cached_visibility() != "password")):
                    visible = False
            _logger.info(menu.env.user.partner_id.support_client_id)
            if menu.controller_page_id and not menu.env.user._is_internal():
                controller_page_sudo = menu.controller_page_id.sudo()
                if (not controller_page_sudo.is_published
                    or (not controller_page_sudo.view_id._handle_visibility(do_raise=False)
                        and controller_page_sudo.view_id._get_cached_visibility() != "password")):
                    visible = False
            if menu.env.user.partner_id.support_client_id and menu.country_id:
                if menu.env.user.partner_id.support_client_id.country.id == menu.country_id.id:
                    visible = True
                else:
                    visible =False
            menu.is_visible = visible