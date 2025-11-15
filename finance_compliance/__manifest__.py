# -*- coding: utf-8 -*-
{
    "name": "Finance Compliance",
    "summary": "Recomendações auditáveis, documentos e trilha imutável",
    "version": "16.0.1.0.0",
    "license": "LGPL-3",
    "author": "Finance Suite",
    "depends": ["finance_core", "finance_planning", "finance_investments", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "data/finance_compliance_data.xml",
        "views/finance_recommendation_views.xml",
        "views/finance_compliance_views.xml",
        "views/finance_profile_views.xml",
        "wizard/finance_recommendation_wizard_views.xml",
    ],
}
