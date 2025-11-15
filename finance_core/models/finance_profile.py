# -*- coding: utf-8 -*-
import base64
import json
from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class FinanceProfile(models.Model):
    _name = "finance.profile"
    _description = "Perfil financeiro do cliente"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "display_name"

    partner_id = fields.Many2one(
        "res.partner",
        string="Cliente",
        required=True,
        ondelete="cascade",
        index=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Empresa",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    display_name = fields.Char(compute="_compute_display_name", store=True)
    advisor_id = fields.Many2one(
        "res.users",
        string="Consultor responsável",
        tracking=True,
        default=lambda self: self.env.user,
    )
    onboarding_stage = fields.Selection(
        [
            ("new", "Onboarding"),
            ("diagnosis", "Diagnóstico"),
            ("planning", "Planejamento"),
            ("execution", "Execução"),
            ("review", "Acompanhamento"),
        ],
        string="Etapa atual",
        default="new",
        tracking=True,
    )
    investor_type = fields.Selection(
        [
            ("pf", "Pessoa Física"),
            ("pj", "Pessoa Jurídica"),
        ],
        string="Tipo de cliente",
        required=True,
        default="pf",
        tracking=True,
    )
    suitability_score = fields.Integer(string="Pontuação suitability", tracking=True)
    suitability_profile = fields.Selection(
        [
            ("conservative", "Conservador"),
            ("moderate", "Moderado"),
            ("bold", "Arrojado"),
        ],
        string="Perfil de risco",
        tracking=True,
    )
    suitability_last_review = fields.Date(string="Última revisão de suitability", tracking=True)
    suitability_next_review = fields.Date(
        string="Próxima revisão de suitability",
        compute="_compute_suitability_next_review",
        store=True,
    )
    suitability_state = fields.Selection(
        [
            ("draft", "Em análise"),
            ("valid", "Válido"),
            ("expiring", "Próximo do vencimento"),
            ("expired", "Expirado"),
        ],
        compute="_compute_suitability_state",
        store=True,
        string="Status suitability",
    )
    compliance_status = fields.Selection(
        [
            ("clean", "Em conformidade"),
            ("pending", "Pendências"),
            ("restricted", "Restrito"),
        ],
        string="Status de compliance",
        default="clean",
        tracking=True,
    )
    annual_income = fields.Monetary(string="Renda anual", currency_field="currency_id", tracking=True)
    net_worth = fields.Monetary(string="Patrimônio líquido", currency_field="currency_id", tracking=True)
    emergency_fund_months = fields.Float(string="Meses de reserva", tracking=True)
    saving_capacity = fields.Monetary(string="Capacidade de poupança mensal", currency_field="currency_id", tracking=True)
    household_notes = fields.Text(string="Notas pessoais")
    risk_warnings = fields.Text(string="Alertas de risco")
    objective_summary = fields.Text(string="Resumo dos objetivos do cliente")
    last_meeting_id = fields.Many2one("calendar.event", string="Última reunião")
    next_meeting_id = fields.Many2one("calendar.event", string="Próxima reunião")
    currency_id = fields.Many2one(
        "res.currency",
        string="Moeda",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    advisory_alert_ids = fields.One2many("finance.alert", "profile_id", string="Alertas inteligentes")
    advisory_score = fields.Float(
        string="Score financeiro",
        compute="_compute_advisory_score",
        store=True,
    )
    cashflow_balance = fields.Monetary(
        string="Balanço de fluxo de caixa",
        currency_field="currency_id",
        compute="_compute_financial_snapshots",
        store=True,
    )
    goals_progress = fields.Float(
        string="Progresso médio das metas",
        compute="_compute_financial_snapshots",
        store=True,
        group_operator="avg",
    )
    portfolio_value = fields.Monetary(
        string="AUM consolidado",
        currency_field="currency_id",
        compute="_compute_financial_snapshots",
        store=True,
    )
    pending_documents = fields.Integer(
        string="Documentos pendentes",
        compute="_compute_pending_documents",
        store=True,
    )
    privacy_deletion_requested = fields.Boolean(
        string="Exclusão solicitada",
        tracking=True,
    )
    privacy_requested_date = fields.Date(
        string="Data da solicitação",
        tracking=True,
    )

    _sql_constraints = [
        ("finance_profile_partner_unique", "unique(partner_id)", "Cada cliente só pode ter um perfil financeiro."),
    ]

    def name_get(self):
        return [(profile.id, profile.display_name) for profile in self]

    @api.depends("partner_id", "partner_id.name")
    def _compute_display_name(self):
        for profile in self:
            partner_name = profile.partner_id.name or _("Sem nome")
            company_name = profile.company_id.name if profile.company_id else False
            profile.display_name = (
                "%s · %s" % (partner_name, company_name)
                if company_name
                else "%s · Perfil financeiro" % partner_name
            )

    @api.constrains("partner_id", "company_id")
    def _check_company_alignment(self):
        for profile in self:
            if profile.partner_id.company_id and profile.partner_id.company_id != profile.company_id:
                raise ValidationError(
                    _(
                        "O contato pertence à empresa %(partner_company)s. Atualize a empresa do perfil para manter consistência.",
                        partner_company=profile.partner_id.company_id.display_name,
                    )
                )

    @api.depends("suitability_last_review")
    def _compute_suitability_next_review(self):
        for profile in self:
            if profile.suitability_last_review:
                profile.suitability_next_review = profile.suitability_last_review.replace(
                    year=profile.suitability_last_review.year + 1
                )
            else:
                profile.suitability_next_review = False

    @api.depends("suitability_last_review", "suitability_next_review")
    def _compute_suitability_state(self):
        today = date.today()
        for profile in self:
            if not profile.suitability_last_review:
                profile.suitability_state = "draft"
                continue
            if profile.suitability_next_review and profile.suitability_next_review < today:
                profile.suitability_state = "expired"
            elif profile.suitability_next_review and (
                profile.suitability_next_review - today
            ).days <= 30:
                profile.suitability_state = "expiring"
            else:
                profile.suitability_state = "valid"

    @api.depends(
        "annual_income",
        "saving_capacity",
        "emergency_fund_months",
        "suitability_state",
        "compliance_status",
    )
    def _compute_advisory_score(self):
        for profile in self:
            score = 0.0
            if profile.annual_income:
                score += min(profile.annual_income / 100000.0, 1.0) * 25
            if profile.saving_capacity:
                score += min(profile.saving_capacity / 5000.0, 1.0) * 25
            if profile.emergency_fund_months:
                score += min(profile.emergency_fund_months / 6.0, 1.0) * 15
            if profile.suitability_state == "valid":
                score += 15
            elif profile.suitability_state == "expiring":
                score += 5
            if profile.compliance_status == "clean":
                score += 20
            elif profile.compliance_status == "pending":
                score += 10
            profile.advisory_score = round(score, 2)

    @api.depends("partner_id")
    def _compute_financial_snapshots(self):
        for profile in self:
            goals_progress = 0.0
            goal_count = 0
            cashflow_balance = 0.0
            aum_total = 0.0
            if hasattr(profile, "goal_ids"):
                goals = profile.goal_ids.filtered(lambda g: g.state != "archived")
                if goals:
                    goal_progress_total = sum(goal.progress_ratio for goal in goals)
                    goals_progress = goal_progress_total / len(goals)
                    goal_count = len(goals)
            if hasattr(profile, "cashflow_plan_ids"):
                latest_plan = profile.cashflow_plan_ids[:1]
                if latest_plan:
                    cashflow_balance = latest_plan.monthly_surplus
            if hasattr(profile, "portfolio_snapshot_ids"):
                latest_snapshot = profile.portfolio_snapshot_ids[:1]
                if latest_snapshot:
                    aum_total = latest_snapshot.market_value
            profile.goals_progress = goals_progress if goal_count else 0.0
            profile.cashflow_balance = cashflow_balance
            profile.portfolio_value = aum_total

    @api.depends("advisory_alert_ids", "advisory_alert_ids.state")
    def _compute_pending_documents(self):
        for profile in self:
            alert_count = len(
                profile.advisory_alert_ids.filtered(lambda alert: alert.category == "document" and alert.state != "done")
            )
            document_count = 0
            if "finance.document" in self.env:
                document_count = self.env["finance.document"].search_count(
                    [
                        ("profile_id", "=", profile.id),
                        ("is_expired", "=", True),
                    ]
                )
            profile.pending_documents = alert_count + document_count

    @api.constrains("suitability_state", "compliance_status")
    def _check_compliance_alignment(self):
        for profile in self:
            if profile.suitability_state == "expired" and profile.compliance_status == "clean":
                raise ValidationError(
                    _("Atualize o status de compliance quando a suitability estiver expirada para manter consistência.")
                )

    def action_open_partner(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "res.partner",
            "view_mode": "form",
            "res_id": self.partner_id.id,
        }

    def action_refresh_alerts(self):
        self._generate_smart_alerts()
        return True

    def _generate_smart_alerts(self):
        today = date.today()
        activity_type = self.env.ref("mail.mail_activity_data_todo", raise_if_not_found=False)
        for profile in self:
            alerts_to_create = []
            if profile.suitability_state in {"expiring", "expired"}:
                alerts_to_create.append(
                    {
                        "name": _(
                            "Suitability a vencer"
                            if profile.suitability_state == "expiring"
                            else "Suitability vencida"
                        ),
                        "category": "compliance",
                        "description": _(
                            "Revise a suitability de %(client)s. A última revisão foi em %(date)s.",
                            client=profile.partner_id.name,
                            date=profile.suitability_last_review,
                        ),
                    }
                )
            if hasattr(profile, "goal_ids"):
                delayed_goals = profile.goal_ids.filtered(lambda g: g.is_late)
                for goal in delayed_goals:
                    alerts_to_create.append(
                        {
                            "name": _("Meta em atraso: %(goal)s", goal=goal.name),
                            "category": "goal",
                            "description": goal.alert_message,
                        }
                    )
            if hasattr(profile, "portfolio_snapshot_ids"):
                deviations = profile.portfolio_snapshot_ids[:1].mapped("allocation_warning")
                if deviations:
                    alerts_to_create.append(
                        {
                            "name": _("Carteira fora do alvo"),
                            "category": "portfolio",
                            "description": deviations[0],
                        }
                    )
            existing_alerts = {alert.name for alert in profile.advisory_alert_ids if alert.state != "done"}
            for alert_vals in alerts_to_create:
                if alert_vals["name"] in existing_alerts:
                    continue
                alert_vals.update({"profile_id": profile.id, "trigger_date": today})
                alert = self.env["finance.alert"].create(alert_vals)
                if activity_type:
                    has_activity = self.env["mail.activity"].search_count(
                        [
                            ("res_id", "=", profile.id),
                            ("res_model", "=", profile._name),
                            ("note", "=", alert.description or alert.name),
                            ("activity_type_id", "=", activity_type.id),
                        ]
                    )
                    if not has_activity:
                        self.env["mail.activity"].create(
                            {
                                "res_model_id": self.env["ir.model"]._get_id(profile._name),
                                "res_id": profile.id,
                                "activity_type_id": activity_type.id,
                                "summary": alert.name,
                                "note": alert.description or alert.name,
                                "user_id": profile.advisor_id.id or self.env.user.id,
                                "date_deadline": today,
                            }
                        )

    def action_open_onboarding_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "finance.onboarding.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_partner_id": self.partner_id.id,
                "default_advisor_id": self.advisor_id.id,
                "default_investor_type": self.investor_type,
            },
        }

    def action_open_goal_wizard(self):
        self.ensure_one()
        if "finance.goal.wizard" not in self.env:
            raise UserError(_("Instale o módulo de planejamento financeiro para criar metas guiadas."))
        return {
            "type": "ir.actions.act_window",
            "res_model": "finance.goal.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_profile_id": self.id},
        }

    def action_open_review_wizard(self):
        self.ensure_one()
        if "finance.review.wizard" not in self.env:
            raise UserError(_("Instale o módulo de investimentos para executar a revisão trimestral."))
        return {
            "type": "ir.actions.act_window",
            "res_model": "finance.review.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_profile_id": self.id},
        }

    def action_open_recommendation_wizard(self):
        self.ensure_one()
        if "finance.recommendation.wizard" not in self.env:
            raise UserError(_("Instale o módulo de compliance para emitir recomendações guiadas."))
        return {
            "type": "ir.actions.act_window",
            "res_model": "finance.recommendation.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_profile_id": self.id},
        }

    def action_schedule_review(self):
        self.ensure_one()
        if "calendar.event" not in self.env:
            raise UserError(_("Instale a integração de calendário para agendar revisões."))
        return {
            "type": "ir.actions.act_window",
            "res_model": "calendar.event",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_name": _("Revisão financeira"),
                "default_finance_profile_id": self.id,
            },
        }

    def action_export_personal_data(self):
        self.ensure_one()
        goal_data = []
        if "finance.goal" in self.env and hasattr(self, "goal_ids"):
            goal_data = self.goal_ids.read()
        portfolio_data = []
        if "finance.portfolio" in self.env and hasattr(self, "portfolio_ids"):
            portfolio_data = self.portfolio_ids.read()
        document_data = []
        if "finance.document" in self.env:
            document_data = self.env["finance.document"].search_read([("profile_id", "=", self.id)])
        data = {
            "profile": self.read()[0],
            "partner": self.partner_id.read()[0],
            "goals": goal_data,
            "portfolios": portfolio_data,
            "documents": document_data,
        }
        payload = json.dumps(data, default=str, ensure_ascii=False, indent=2)
        attachment = self.env["ir.attachment"].create(
            {
                "name": "export_%s.json" % self.partner_id.id,
                "datas": base64.b64encode(payload.encode("utf-8")),
                "res_model": self._name,
                "res_id": self.id,
                "mimetype": "application/json",
            }
        )
        self.message_post(body=_("Exportação de dados pessoais gerada."), attachment_ids=[attachment.id])
        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/%s?download=true" % attachment.id,
            "target": "self",
        }

    def action_request_data_deletion(self):
        self.ensure_one()
        self.write(
            {
                "privacy_deletion_requested": True,
                "privacy_requested_date": fields.Date.context_today(self),
            }
        )
        self.message_post(body=_("Solicitação de exclusão registrada conforme LGPD."))
        return True

    def action_anonymize_partner(self):
        self.ensure_one()
        partner = self.partner_id
        anonymized_vals = {
            "name": _("Cliente Anonimizado %s") % self.id,
            "email": False,
            "phone": False,
            "mobile": False,
            "street": False,
            "street2": False,
            "zip": False,
            "city": False,
            "state_id": False,
            "vat": False,
            "website": False,
        }
        partner.write(anonymized_vals)
        self.write(
            {
                "household_notes": False,
                "objective_summary": False,
            }
        )
        self.message_post(body=_("Dados pessoais foram anonimizados mediante solicitação."))
        return True


class ResPartner(models.Model):
    _inherit = "res.partner"

    finance_profile_id = fields.One2many(
        "finance.profile",
        "partner_id",
        string="Perfil financeiro",
    )

    def action_open_finance_profile(self):
        self.ensure_one()
        profile = self.finance_profile_id[:1]
        action = {
            "type": "ir.actions.act_window",
            "res_model": "finance.profile",
            "view_mode": "form",
            "target": "current",
        }
        if profile:
            action.update({"res_id": profile.id})
        else:
            action.update({"context": {"default_partner_id": self.id}})
        return action
