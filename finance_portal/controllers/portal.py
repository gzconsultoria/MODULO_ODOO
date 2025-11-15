# -*- coding: utf-8 -*-
from base64 import b64encode

from markupsafe import escape

from odoo import http, fields
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class FinancePortal(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        profile = self._get_finance_profile()
        values["finance_profile_count"] = 1 if profile else 0
        return values

    def _get_finance_profile(self):
        partner = request.env.user.partner_id
        return (
            request.env["finance.profile"].sudo().search(
                [
                    ("partner_id", "child_of", partner.ids),
                ],
                limit=1,
            )
        )

    @http.route(["/my/finance"], type="http", auth="user", website=True)
    def portal_my_finance(self, **kw):
        profile = self._get_finance_profile()
        if not profile:
            return request.render(
                "finance_portal.portal_no_finance_profile",
                {},
            )
        latest_snapshot = profile.portfolio_snapshot_ids[:1]
        goals = profile.goal_ids.sorted(lambda g: g.horizon_date or fields.Date.today())
        recommendations = profile.recommendation_ids.sorted(lambda r: r.recommendation_date, reverse=True)[:5]
        documents = profile.document_ids.sorted(lambda d: (d.is_expired, d.expiration_date or fields.Date.today()))
        meetings = profile.event_ids.sorted(lambda e: e.start)[:5]
        values = {
            "profile": profile,
            "snapshot": latest_snapshot,
            "goals": goals,
            "recommendations": recommendations,
            "documents": documents,
            "meetings": meetings,
        }
        return request.render("finance_portal.portal_my_finance", values)

    @http.route(["/my/finance/upload"], type="http", auth="user", methods=["POST"], website=True, csrf=True)
    def portal_upload_document(self, **post):
        profile = self._get_finance_profile()
        if not profile:
            return request.redirect("/my/finance")
        file = post.get("document_file")
        category = post.get("category") or "other"
        if file and file.filename:
            content = file.read()
            attachment = request.env["ir.attachment"].sudo().create(
                {
                    "name": file.filename,
                    "datas": b64encode(content),
                    "res_model": "finance.profile",
                    "res_id": profile.id,
                }
            )
            request.env["finance.document"].sudo().create(
                {
                    "profile_id": profile.id,
                    "name": file.filename,
                    "category": category,
                    "attachment_id": attachment.id,
                }
            )
            profile.message_post(body=escape(post.get("message", "Documento enviado via portal.")))
        return request.redirect("/my/finance")

    @http.route(["/my/finance/message"], type="http", auth="user", methods=["POST"], website=True, csrf=True)
    def portal_finance_message(self, **post):
        profile = self._get_finance_profile()
        if not profile:
            return request.redirect("/my/finance")
        body = post.get("message")
        if body:
            self._message_post_helper(
                "finance.profile",
                profile.id,
                message=body,
                **{"message_type": "comment"},
            )
        return request.redirect("/my/finance")
