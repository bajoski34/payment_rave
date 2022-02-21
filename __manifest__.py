# -*- coding: utf-8 -*-
{
    'name': 'Flutterwave for Business',
    'category': 'eCommerce',
    'summary': 'The Official Flutterwave Payment Acquirer for Odoo Clients',
    'version': '3.0',
    'license': 'LGPL-3',
    'author': 'Flutterwave Technology Solutions',
    'website': 'https://app.flutterwave.com/',
    'description': """Flutterwave Payment Acquirer""",
    'depends': ['payment'],
    'data': [
        'views/payment_views.xml',
        'views/payment_rave_templates.xml',
        'data/payment_acquirer_data.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'payment_rave/static/src/js/payment_form.js',
        ],
    },
    'images': ['static/src/img/flutterwave.png'],
    'application': True,
    'unistall_hook': 'uninstall_hook',    
}
