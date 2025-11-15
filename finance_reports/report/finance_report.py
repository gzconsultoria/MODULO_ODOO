# -*- coding: utf-8 -*-
from odoo import api, models


class ReportFinance360(models.AbstractModel):
    _name = "report.finance_reports.finance_report_template"
    _description = "Relatório 360° do cliente"

    @api.model
    def _get_report_values(self, docids, data=None):
        profiles = self.env["finance.profile"].browse(docids)
        return {
            "doc_ids": profiles.ids,
            "doc_model": "finance.profile",
            "docs": profiles,
            "get_goal_cards": self._prepare_goal_cards,
            "get_portfolio_snapshot": self._prepare_portfolio_snapshot,
        }

    def _prepare_goal_cards(self, profile):
        return [
            {
                "name": goal.name,
                "progress": goal.progress_ratio * 100.0,
                "horizon": goal.horizon_date,
                "state": goal.state,
            }
            for goal in profile.goal_ids
        ]

    def _prepare_portfolio_snapshot(self, profile):
        snapshot = profile.portfolio_snapshot_ids[:1]
        if not snapshot:
            return {}
        return {
            "date": snapshot.snapshot_date,
            "value": snapshot.market_value,
            "warning": snapshot.allocation_warning,
            "positions": [
                {
                    "asset": position.reference_id.display_name,
                    "value": position.market_value,
                    "quantity": position.quantity,
                }
                for position in snapshot.position_ids
            ],
        }
