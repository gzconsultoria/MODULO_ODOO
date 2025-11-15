# -*- coding: utf-8 -*-
{
    "name": "Finance Core",
    "summary": "Base financial advisory profile linked 1:1 to partners with alerts and 360° view",
    "version": "19.0.1.0.0",
    "license": "LGPL-3",
    "author": "Finance Suite",
    "depends": ["base", "contacts", "mail", "board"],
    "data": [
        "security/finance_core_groups.xml",
        "security/ir.model.access.csv",
        "security/finance_core_rules.xml",
        "data/finance_core_data.xml",
        "views/finance_profile_views.xml",
        "views/finance_dashboard_views.xml",
        "views/finance_onboarding_wizard_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "finance_core/static/src/scss/finance_profile.scss",
        ],
    },
    "application": True,
    "installable": True,
}
