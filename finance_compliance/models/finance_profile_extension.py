# -*- coding: utf-8 -*-
from odoo import api, fields, models


class FinanceProfile(models.Model):
    _inherit = "finance.profile"

    def _compute_pending_documents(self):
        super()._compute_pending_documents()

    document_ids = fields.One2many(
        "finance.document",
        "profile_id",
        string="Documentos",
    )
    recommendation_ids = fields.One2many(
        "finance.recommendation",
        "profile_id",
        string="Recomendações",
    )
    compliance_log_ids = fields.One2many(
        "finance.compliance.log",
        "profile_id",
        string="Logs de compliance",
    )
