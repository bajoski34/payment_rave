import logging
import requests
import pprint
import json
from odoo import _, api, models, fields


_logger = logging.getLogger(__name__)

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _rave_verify_charge(self, data):
        api_url_charge = 'https://%s/flwv3-pug/getpaidx/api/v2/verify' % (self.acquirer_id._get_rave_api_url())
        payload = {
            'SECKEY': self.acquirer_id.rave_secret_key,
            'txref': self.reference,
        }
        headers = {
            'Content-Type': 'application/json',
        }
        
        _logger.info('_rave_verify_charge: Sending values to URL %s, values:\n%s', api_url_charge, pprint.pformat(payload))
        r = requests.post(api_url_charge,headers=headers, data=json.dumps(payload))
        # res = r.json()
        _logger.info('_rave_verify_charge: Values received:\n%s', pprint.pformat(r))
        return self._rave_validate_tree(r.json(),data)

    def _rave_validate_tree(self, tree, data):
        self.ensure_one()
        if self.state != 'draft':
            _logger.info('Rave: trying to validate an already validated tx (ref %s)', self.reference)
            return True

        status = tree.get('status')
        amount = tree["data"]["amount"]
        currency = tree["data"]["currency"]
        
        if status == 'success' and amount == data["amount"] and currency == data["currency"] :
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