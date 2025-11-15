# -*- coding: utf-8 -*-
{
    "name": "Finance Investments",
    "summary": "Carteiras versionadas, ativos referenciados e wizards de rebalanceamento",
    "version": "19.0.1.0.0",
    "license": "LGPL-3",
    "author": "Finance Suite",
    "depends": ["finance_core", "queue_job"],
    "data": [
        "security/ir.model.access.csv",
        "data/finance_investment_data.xml",
        "views/finance_asset_views.xml",
        "views/finance_portfolio_views.xml",
        "views/finance_profile_views.xml",
        "wizard/finance_snapshot_wizard_views.xml",
        "wizard/finance_rebalance_wizard_views.xml",
        "wizard/finance_review_wizard_views.xml",
    ],
    "installable": True,
}
