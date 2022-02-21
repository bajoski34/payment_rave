import logging
import requests
import pprint
import json
from odoo import _, api, models, fields
from odoo.addons.payment.payment_rave.controllers.main import RaveController

_logger = logging.getLogger(__name__)

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'


    def _get_specific_processing_values(self, processing_values):
        """ Overide of payment to return Flutterwave-specific values. """

        res = super()._get_specific_processing_values(processing_values)
        if self.provider != 'rave':
            return res
        
        return {
            'tx_ref': processing_values['reference'],
            'public_key': self.acquirer_id.rave_public_key,
            'redirect_url': self.return_url,
            'currency': self.currency_id.name,
            'amount': processing_values['amount'],
            'email': self.partner_email,
            'phonenumber': self.partner_phone,
            'firstname': self.partner_first_name,
            'lastname': self.partner_last_name,
            'country': self.partner_country_id.code,
            'customer_id': self.partner_id.id,
        }

    def _send_payment_request(self):
        """ Overide of paymeent to send payment request to stripe with a confirmed Payment"""

        super()._send_payment_request()
        if self.provider != 'rave':
            return

        # make the payment request to Flutterwave

    

        

    def _rave_verify_charge(self, data):
        # https://api.flutterwave.com/v3/transactions/verify_by_reference?tx_ref=DevRef002156
        api_url_charge = 'https://%s/transactions/verify_by_reference?tx_ref=%s' % (self.acquirer_id._get_rave_api_url(), self.reference)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % self.acquirer_id.rave_secret_key,
        }
        
        _logger.info('_flutterwave_verify_charge: Sending values to URL %s, values:\n%s', api_url_charge, self.reference)
        r = requests.get(api_url_charge,headers=headers, data=json.dumps(payload))
        # res = r.json()
        _logger.info('_flutterwave_verify_charge: Values received:\n%s', pprint.pformat(r))
        return self._rave_validate_tree(r.json(),data)

    def _rave_validate_tree(self, tree, data):
        self.ensure_one()
        if self.state != 'draft':
            _logger.info('Flutterwave: trying to validate an already validated tx (ref %s)', self.reference)
            return True

        status = tree.get('status')
        amount = tree["data"]["amount"]
        currency = tree["data"]["currency"]
        
        if status == 'successful' and amount == data["amount"] and currency == data["currency"] :
            self.write({
                'date': fields.datetime.now(),
                'acquirer_reference': tree["data"]["txid"],
            })
            self._set_transaction_done()
            self.execute_callback()
            if self.payment_token_id:
                self.payment_token_id.verified = True
            return True
        else:
            error = tree['message']
            _logger.warn(error)
            self.sudo().write({
                'state_message': error,
                'acquirer_reference':tree["data"]["txid"],
                'date': fields.datetime.now(),
            })
            self._set_transaction_cancel()
            return False