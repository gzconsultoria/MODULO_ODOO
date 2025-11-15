# -*- coding: utf-8 -*-
from odoo import _, fields, models


class FinanceRebalanceWizard(models.TransientModel):
    _name = "finance.rebalance.wizard"
    _description = "Sugestão de rebalanceamento automático"

    snapshot_id = fields.Many2one("finance.portfolio.snapshot", required=True)
    rebalance_lines = fields.One2many("finance.rebalance.wizard.line", "wizard_id")

    def action_prepare(self):
        self.ensure_one()
        lines = []
        snapshot = self.snapshot_id
        target = snapshot.portfolio_id.target_allocation or {}
        total_value = snapshot.market_value or 1
        actual_totals = {}
        for position in snapshot.position_ids:
            asset_class = position.reference_id.asset_type
            actual_totals.setdefault(asset_class, 0.0)
            actual_totals[asset_class] += position.market_value
        self.rebalance_lines.unlink()
        for asset_class, target_pct in target.items():
            target_value = total_value * (target_pct / 100.0)
            actual_value = actual_totals.get(asset_class, 0.0)
            delta_value = target_value - actual_value
            if abs(delta_value) < total_value * 0.01:
                continue
            lines.append(
                (
                    0,
                    0,
                    {
                        "asset_class": asset_class,
                        "delta_value": delta_value,
                    },
                )
            )
        self.rebalance_lines = lines
        return {
            "type": "ir.actions.act_window",
            "res_model": "finance.rebalance.wizard",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_apply(self):
        self.ensure_one()
        message = []
        for line in self.rebalance_lines:
            suggestion = _(
                "Classe %(asset_class)s: ajustar %(value).2f",
                asset_class=line.asset_class,
                value=line.delta_value,
            )
            message.append(suggestion)
        if message:
            body = "<br/>".join(message)
            self.snapshot_id.portfolio_id.profile_id.message_post(body=body, subject=_("Rebalanceamento sugerido"))
        return {"type": "ir.actions.act_window_close"}


class FinanceRebalanceWizardLine(models.TransientModel):
    _name = "finance.rebalance.wizard.line"
    _description = "Linha do rebalanceamento sugerido"

    wizard_id = fields.Many2one("finance.rebalance.wizard", required=True, ondelete="cascade")
    asset_class = fields.Char(required=True)
    delta_value = fields.Float(required=True)
