# coding: utf-8
import requests
from tokenize import group
from werkzeug import urls

from odoo import api, fields, models, _

class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'
    
    provider = fields.Selection(
        selection_add=[('rave', "Rave")], ondelete={'rave': 'cascade'})
    # provider = fields.Selection(selection_add=[('flutterwave', 'Flutterwave')], ondelete={'flutterwave': 'set default'})
    rave_public_key = fields.Char(required_if_provider='rave', groups='base.group_user')
    rave_secret_key = fields.Char(required_if_provider='rave', groups='base.group_user')
    rave_secret_hash = fields.Char(required_if_provider='rave', groups='base.group_user', string="Flutterwave Secret Hash")
    environment = fields.Char(required_if_provider='rave', groups='base.group_user')

    @api.model
    def _get_rave_api_url(self):
        """ Flutterwave URLs"""
        return 'api.flutterwave.com'

    def rave_form_generate_values(self, tx_values):
        self.ensure_one()
        rave_tx_values = dict(tx_values)
        temp_rave_tx_values = {
            'company': self.company_id.name,
            'amount': tx_values['amount'],  # Mandatory
            'currency': tx_values['currency'].name,  # Mandatory anyway
            'currency_id': tx_values['currency'].id,  # same here
            'address_line1': tx_values.get('partner_address'),  # Any info of the partner is not mandatory
            'address_city': tx_values.get('partner_city'),
            'address_country': tx_values.get('partner_country') and tx_values.get('partner_country').name or '',
            'email': tx_values.get('partner_email'),
            'address_zip': tx_values.get('partner_zip'),
            'name': tx_values.get('partner_name'),
            'phone': tx_values.get('partner_phone'),
        }

        rave_tx_values.update(temp_rave_tx_values)
        return rave_tx_values

    def _flw_make_request(self, endpoint, payload=None, method='POST', offline=False):
        """  Make a request to Flutterwave API at the specified endpoint,
        
         Note: self.ensure_one()

        :param str endpoint: The endpoint to be reached by the request
        :param dict payload: The payload of the request
        :param str method: The HTTP method of the request
        :param bool offline: Whether the operation of the transaction being processed is 'offline'
        :return The JSON-formatted content of the response
        :rtype: dict
        :raise: ValidationError if an HTTP error occurs
        """
        self.ensure_one()

        url = urls.url_join('https://api.flutterwave.com/v3/', endpoint)
        headers = {
            'AUTHORIZATION': f'Bearer {self.rave_secret_key}',
            'Content-Type': 'application/js'
        }
        try:
            response = requests.request(method, url, data=payload, headers=headers, timeout=60)

            if not response.ok \
                    and not offline \
                    and 400 <= response.status_code < 500 \
                    and response.json().get('error'):  # The 'code' entry is sometimes missing
                try:
                    response.raise_for_status()
                except requests.exceptions.HTTPError:
                    _logger.exception("invalid API request at %s with data %s", url, payload)
                    error_msg = response.json().get('error', {}).get('message', '')
                    raise ValidationError(
                        "Flutterwave: " + _(
                            "The communication with the API failed.\n"
                            "Flutterwave gave us the following info about the problem:\n'%s'", error_msg
                        )
                    )
        except requests.exceptions.ConnectionError:
            _logger.exception("unable to reach endpoint at %s", url)
            raise ValidationError("Flutterwave: " + _("Could not establish the connection to the API."))
        return response.json()

    def _get_default_payment_method_id(self):
        self.ensure_one()
        if self.provider != 'rave':
            return super()._get_default_payment_method_id()
        return self.env.ref('payment_rave.payment_method_rave').id





