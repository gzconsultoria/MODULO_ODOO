# -*- coding: utf-8 -*-
from odoo import _, fields, models


class FinancePortfolioSnapshotWizard(models.TransientModel):
    _name = "finance.portfolio.snapshot.wizard"
    _description = "Assistente de snapshot de carteira"

    portfolio_id = fields.Many2one("finance.portfolio", required=True)
    snapshot_date = fields.Date(default=fields.Date.context_today, required=True)
    include_liabilities = fields.Boolean(default=True)

    def action_create_snapshot(self):
        self.ensure_one()
        snapshot = self.env["finance.portfolio.snapshot"].create(
            {
                "portfolio_id": self.portfolio_id.id,
                "snapshot_date": self.snapshot_date,
            }
        )
        # Auto populate positions from last snapshot to acelerar workflow
        last_snapshot = self.env["finance.portfolio.snapshot"].search(
            [
                ("portfolio_id", "=", self.portfolio_id.id),
                ("snapshot_date", "<", self.snapshot_date),
            ],
            order="snapshot_date desc",
            limit=1,
        )
        if last_snapshot:
            for position in last_snapshot.position_ids:
                snapshot.position_ids.create(
                    {
                        "snapshot_id": snapshot.id,
                        "reference_id": position.reference_id.id,
                        "quantity": position.quantity,
                        "avg_price": position.avg_price,
                        "market_price": position.market_price,
                    }
                )
        if self.include_liabilities and self.portfolio_id.profile_id.liability_ids:
            self.portfolio_id.profile_id.advisory_alert_ids.create(
                {
                    "profile_id": self.portfolio_id.profile_id.id,
                    "name": _("Revisar passivos na carteira"),
                    "category": "portfolio",
                    "description": _("Revise os passivos para o snapshot de %(date)s.", date=self.snapshot_date),
                }
            )
        snapshot.with_delay(priority=10).job_post_process_snapshot()
        return {
            "type": "ir.actions.act_window",
            "res_model": "finance.portfolio.snapshot",
            "res_id": snapshot.id,
            "view_mode": "form",
        }
