# -*- coding: utf-8 -*-
{
    "name": "Finance Portal",
    "summary": "Portal do cliente com visão 360°, documentos e mensagens seguras",
    "version": "16.0.1.0.0",
    "license": "LGPL-3",
    "author": "Finance Suite",
    "depends": [
        "portal",
        "finance_core",
        "finance_planning",
        "finance_investments",
        "finance_compliance",
        "finance_calendar_integration",
    ],
    "data": [
        "security/finance_portal_rules.xml",
        "views/finance_portal_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "finance_portal/static/src/scss/finance_portal.scss",
        ],
    },
    "application": False,
}
