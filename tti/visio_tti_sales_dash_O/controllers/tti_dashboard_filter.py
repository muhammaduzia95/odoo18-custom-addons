# D:\Visiomate\Odoo\odoo18\custom_addons\tti\visio_tti_sales_dash\controllers\tti_dashboard_filter.py
# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.http import request
from calendar import monthrange
from odoo.exceptions import UserError
from datetime import date
import calendar
import logging

_logger = logging.getLogger(__name__)


class TTISalesDashCtl(http.Controller):

    @http.route('/tti_sales_dashboard/filters', type='json', auth='user')
    def get_filters(self):
        """Return periods, years, categories, subcategories, zones + defaults."""
        user = request.env.user
        dbname = request.env.cr.dbname
        _logger.info(
            "[TTI DASH] /tti_sales_dashboard/filters called by user %s (id=%s) on db %s",
            user.login, user.id, dbname,
        )

        try:
            # Periods as month names
            periods = [{'id': i, 'name': calendar.month_name[i]} for i in range(1, 13)]
            _logger.debug("[TTI DASH] Period list built: %s", periods)

            # Years from invoices/refunds, use invoice_date or accounting date
            request.env.cr.execute("""
                SELECT DISTINCT EXTRACT(YEAR FROM COALESCE(invoice_date, date))::int AS y
                FROM account_move
                WHERE move_type IN ('out_invoice','out_refund') AND state='posted'
                ORDER BY y
            """)
            years_raw = [r[0] for r in request.env.cr.fetchall()]
            _logger.debug("[TTI DASH] Raw years from account_move: %s", years_raw)

            years = years_raw[:]
            current_year = date.today().year
            if not years:
                years = [current_year]
                _logger.info(
                    "[TTI DASH] No posted invoices found, defaulting years to current_year=%s",
                    current_year,
                )

            # expand to contiguous range; if single year, show last 5 years up to current
            if len(years) == 1:
                start = min(years[0], current_year) - 4
                years = list(range(start, current_year + 1))
            else:
                years = list(range(min(years), max(years) + 1))

            _logger.debug("[TTI DASH] Final years range used in filters: %s", years)

            cats = [{'id': r['id'], 'name': r['name']}
                    for r in request.env['tti.si.category'].sudo().search([]).read(['name'])]
            subs = [{'id': r['id'], 'name': r['name']}
                    for r in request.env['tti.si.sub.category'].sudo().search([]).read(['name'])]
            zones = [{'id': r['id'], 'name': r['name']}
                     for r in request.env['tti.city.zone'].sudo().search([]).read(['name'])]

            _logger.debug(
                "[TTI DASH] Loaded filter lists: categories=%s, subcategories=%s, zones=%s",
                cats, subs, zones,
            )

            current_date = date.today()
            resp = {
                'years': years,
                'periods': periods,
                'categories': cats,
                'subcategories': subs,
                'zones': zones,
                'default_from_period': current_date.month,
                'default_to_period': current_date.month,
                'default_from_year': current_date.year,
                'default_to_year': current_date.year,
            }

            _logger.info(
                "[TTI DASH] /filters response prepared. defaults: fp=%s, tp=%s, fy=%s, ty=%s",
                resp['default_from_period'],
                resp['default_to_period'],
                resp['default_from_year'],
                resp['default_to_year'],
            )
            return resp

        except Exception:
            _logger.exception("[TTI DASH] Error while building filters response")
            # let Odoo propagate as RPC_ERROR so frontend catches it
            raise

    @http.route('/tti_sales_dashboard/filter_data', type='json', auth='user')
    def get_data(self, **kw):
        """Return KPI data for given filters."""
        user = request.env.user
        dbname = request.env.cr.dbname
        _logger.info(
            "[TTI DASH] /tti_sales_dashboard/filter_data called by user %s (id=%s) on db %s with kw=%s",
            user.login, user.id, dbname, kw,
        )

        p = kw.get('data', {}) or {}
        _logger.debug("[TTI DASH] Raw payload 'data' dict: %s", p)

        def _as_int(val, default):
            """Strict int for REQUIRED fields (months/years)."""
            if val in (None, "", "null", "none"):
                _logger.debug("[TTI DASH] _as_int: empty value %r, using default %r", val, default)
                return default
            try:
                res = int(val)
                _logger.debug("[TTI DASH] _as_int: converted %r -> %r", val, res)
                return res
            except Exception as ex:
                _logger.warning(
                    "[TTI DASH] _as_int failed for value=%r (%s). Using default=%r. ex=%s",
                    val, type(val), default, ex,
                )
                return default

        def _as_opt_int(val):
            """Optional filter: return False if empty/null, else int."""
            if val in (None, "", "null", "none"):
                _logger.debug("[TTI DASH] _as_opt_int: empty value %r -> False", val)
                return False
            try:
                res = int(val)
                _logger.debug("[TTI DASH] _as_opt_int: converted %r -> %r", val, res)
                return res
            except Exception as ex:
                _logger.warning(
                    "[TTI DASH] _as_opt_int failed for value=%r (%s). Returning False. ex=%s",
                    val, type(val), ex,
                )
                return False

        today_year = date.today().year
        fp = _as_int(p.get('from_period'), 1)
        fy = _as_int(p.get('from_year'), today_year)
        tp = _as_int(p.get('to_period'), 12)
        ty = _as_int(p.get('to_year'), today_year)

        # Optional filters (coming from JS as null or a number)
        cat_id = _as_opt_int(p.get('category'))
        sub_id = _as_opt_int(p.get('subcategory'))
        zone_id = _as_opt_int(p.get('zone'))

        _logger.info(
            "[TTI DASH] Parsed filters -> fp=%s, fy=%s, tp=%s, ty=%s, cat_id=%s, sub_id=%s, zone_id=%s",
            fp, fy, tp, ty, cat_id, sub_id, zone_id,
        )

        # Validate the period range (raise popup via UserError)
        if fy > ty or (fy == ty and fp > tp):
            _logger.warning(
                "[TTI DASH] Invalid period range detected: from=(%s-%s) to=(%s-%s)",
                fy, fp, ty, tp,
            )
            raise UserError("Invalid period range: ‘From’ is after ‘To’. Please correct the months/years.")

        try:
            date_from = date(fy, fp, 1)
            date_to = date(ty, tp, monthrange(ty, tp)[1])
        except Exception as ex:
            _logger.exception(
                "[TTI DASH] Bad date combination fy=%s, fp=%s, ty=%s, tp=%s. ex=%s",
                fy, fp, ty, tp, ex,
            )
            raise UserError("Please select valid months/years.")

        _logger.info(
            "[TTI DASH] Final date range: %s -> %s (cat_id=%s, sub_id=%s, zone_id=%s)",
            date_from, date_to, cat_id, sub_id, zone_id,
        )

        try:
            kpi_result = request.env['tti.dashboard'].get_kpis(
                date_from, date_to, cat_id, sub_id, zone_id
            )
            if isinstance(kpi_result, dict):
                _logger.debug(
                    "[TTI DASH] get_kpis returned dict with keys: %s",
                    list(kpi_result.keys()),
                )
            else:
                _logger.debug(
                    "[TTI DASH] get_kpis returned non-dict result of type %s",
                    type(kpi_result),
                )
            return kpi_result
        except Exception:
            _logger.exception(
                "[TTI DASH] Exception raised inside tti.dashboard.get_kpis "
                "(date_from=%s, date_to=%s, cat_id=%s, sub_id=%s, zone_id=%s)",
                date_from, date_to, cat_id, sub_id, zone_id,
            )
            # propagate so RPC_ERROR shows in UI
            raise
