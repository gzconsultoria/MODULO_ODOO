# -*- coding: utf-8 -*-
from odoo import api, models


class FinanceProfile(models.Model):
    _inherit = "finance.profile"

    @api.depends("cashflow_plan_ids", "cashflow_plan_ids.monthly_surplus")
    def _compute_financial_snapshots(self):
        super()._compute_financial_snapshots()
        for profile in self:
            plans = profile.cashflow_plan_ids.sorted(lambda p: p.date, reverse=True)
            if plans:
                profile.cashflow_balance = plans[0].monthly_surplus
