# -*- coding: utf-8 -*-
import logging
import pprint
import werkzeug

from odoo import http
from odoo.http import request
from odoo.addons.payment.controllers.post_processing import PaymentPostProcessing
from odoo.addons.payment_rave.const import EVENTS

_logger = logging.getLogger(__name__)

class RaveController(http.Controller):
    _checkout_return_url = '/payment/rave/checkout'
    _validation_return_url = '/payment/rave/validation'
    _flutterwave_verify_charge = '/payment/rave/verify_charge'
    _webhook_url = '/payment/rave/webhook'
    
    @http.route([_checkout_return_url], type='http', auth='public', csrf= False)
    def return_payment_values(self, **post):
        """ Upadate the payment values from the database"""
        acquirer_id = int(post.get('acquirer_id'))
        acquirer = request.env['payment.acquirer'].browse(acquirer_id)
        # values = acquirer.rave_form_generate_values(acquirer)
        return post

    @http.route([_webhook_url], type='json', auth='public', csrf= False)
    def flutterwave_webhook(self):
        """ Process the 'Payment Events' sent by Flutterwave to the webook.
            :return:  An empty string to acknowledge the notification with a status of 200 response code.
        """
        event = json.loads(request.httprequest.data)
        _logger.info('flutterwave_webhook: Values received:\n%s', pprint.pformat(event))
        try:
            if event['event'] == EVENTS['CHARGE']:
                tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_feedback_data(
                    'rave', data
                )
                if event['data']['status'] == 'successful' and flutterwave_verify_hash(tx_sudo.acquirer_id.rave_secret_hash):
                    pass

            if event['event'] == EVENTS['TRANSFER']:
                pass
        return ''

    @http.route([_flutterwave_verify_charge], type='json', auth='public')
    def rave_verify_charge(self, **post):
        """ Verify a payment transaction

        Expects the result from the user input from flwpbf-inline.js popup"""
        TX = request.env['payment.transaction']
        tx = None
        data = post.get('data');
        if post.get('tx_ref'):
            tx = TX.sudo().search([('reference', '=', post.get('tx_ref'))])
        if not tx:
            tx_id = (post.get('id') or request.session.get('sale_transaction_id') or
                     request.session.get('website_payment_tx_id'))
            tx = TX.sudo().browse(int(tx_id))
        if not tx:
            raise werkzeug.exceptions.NotFound()

        if tx.type == 'form_save' and tx.partner_id:
            payment_token_id = request.env['payment.token'].sudo().create({
                'acquirer_id': tx.acquirer_id.id,
                'partner_id': tx.partner_id.id,
            })
            tx.payment_token_id = payment_token_id
            response = tx._rave_verify_charge(data)
        else:
            response = tx._rave_verify_charge(data)
        _logger.info('Flutterwave: entering form_feedback with post data %s', pprint.pformat(response))
        if response:
            request.env['payment.transaction'].sudo().with_context(lang=None).form_feedback(response, 'rave')
        # add the payment transaction into the session to let the page /payment/process to handle it
        PaymentPostProcessing.add_payment_transaction(tx)
        return "/payment/process"

    def flutterwave_verify_hash(self, flutterwave_hash):
        """ verify the secret hash of the sent hook."""

        if not flutterwave_hash:
            _logger.warning("Ignored webhook event due to undefined webhook secret")
            return False

        signature_hash = request.httprequest.headers.get('verif-hash')

        if signature_hash != flutterwave_hash:
            _logger.warning("Ignored event with Invalid Signature")
            return False

        return True

