# -*- coding: utf-8 -*-
{
    "name": "Finance Planning",
    "summary": "Metas, fluxo de caixa e assistentes guiados vinculados a perfis financeiros",
    "version": "16.0.1.0.0",
    "license": "LGPL-3",
    "author": "Finance Suite",
    "depends": ["finance_core", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "data/finance_goal_data.xml",
        "views/finance_goal_views.xml",
        "views/finance_cashflow_views.xml",
        "views/finance_profile_views.xml",
        "wizard/finance_goal_wizard_views.xml",
    ],
}
