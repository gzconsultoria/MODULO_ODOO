# -*- coding: utf-8 -*-
{
    "name": "Finance Reports",
    "summary": "Relatórios dinâmicos com 360° do cliente",
    "version": "19.0.1.0.0",
    "license": "LGPL-3",
    "author": "Finance Suite",
    "depends": ["finance_core", "finance_planning", "finance_investments", "finance_compliance", "report"],
    "data": [
        "report/finance_report_templates.xml",
        "report/finance_report_actions.xml",
        "views/finance_report_views.xml",
    ],
    "installable": True,
}
