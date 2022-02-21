# -*- coding: utf-8 -*-
from odoo.addons.payment.tests.common import PaymentCommon


class FlutterwaveCommon(PaymentCommon):

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)

        cls.rave = cls._prepare_acquirer('rave', update_values={
            'name': 'Flutterwave',
            'provider': 'flutterwave',
            'rave_public_key': 'FLWPUBK-e9f8c0b8f8b6f1d0a2a8d3c3a1d9a9b-X',
            'rave_secret_key': 'FLWSECK-e9f8c0b8f8b6f1d0a2a8d3c3a1d9a9b-X',
            'rave_env': 'test',
        })

        cls.acquirer = cls.rave