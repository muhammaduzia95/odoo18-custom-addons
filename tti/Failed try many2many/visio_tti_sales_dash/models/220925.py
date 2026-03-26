# D:\Visiomate\Odoo\odoo18\custom_addons\tti\visio_tti_sales_dash\models\tti_dashboard.py
from odoo import models, fields, api
from datetime import date
from calendar import monthrange
from datetime import timedelta
from dateutil.relativedelta import relativedelta


class TTIDashboard(models.AbstractModel):
    _name = "tti.dashboard"
    _description = "TTI Dashboard Helper"

    @api.model
    def get_kpis(self, date_from, date_to, cat_id=False, sub_id=False, zone_id=False):

        SaleOrder = self.env['sale.order'].sudo()
        Invoice = self.env['account.move'].sudo()
        Payment = self.env['account.payment'].sudo()

        # --- Total Sales (posted invoices) ---
        domain = [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to),
        ]
        if zone_id:
            domain.append(('partner_id.tti_city_zone_id', '=', zone_id))

        invoices = Invoice.search(domain)
        total_sales = sum(invoices.mapped('amount_total'))
        print(f"[DASHBOARD] Total Sales Invoices: {len(invoices)}, Amount: {total_sales}")

        # --- Total Recovery (posted customer receipts) ---
        date_field = 'date' if 'date' in Payment._fields else (
            'payment_date' if 'payment_date' in Payment._fields else False
        )

        pay_domain = [('state', '=', 'paid')]
        if date_field:
            pay_domain += [(date_field, '>=', date_from), (date_field, '<=', date_to)]
        if zone_id:
            pay_domain.append(('partner_id.tti_city_zone_id', '=', zone_id))

        payments = Payment.search(pay_domain)

        total_recovery = float(sum(payments.mapped('amount')))
        print(f"[DASHBOARD] Payments found: {len(payments)} | Sum(amount)={total_recovery} | Date field={date_field}")

        # --- Recovered Percentage ---
        recovered_pct = (total_recovery / total_sales * 100) if total_sales else 0.0
        print(f"[DASHBOARD] Recovered Percentage: {recovered_pct}")

        # --- Pending SO (confirmed but not fully invoiced) ---
        domain = [
            ('date_order', '>=', date_from),
            ('date_order', '<=', date_to),
            ('state', '=', 'sale'),
            ('invoice_status', '!=', 'invoiced'),
        ]
        if zone_id:
            domain.append(('partner_id.tti_city_zone_id', '=', zone_id))
        pending_so_orders = SaleOrder.search(domain)
        pending_so = sum(pending_so_orders.mapped('amount_total'))
        print(f"[DASHBOARD] Pending Sale Orders: {len(pending_so_orders)} orders, Total = {pending_so}")

        # --- Open Quotations ---
        domain = [
            ('date_order', '>=', date_from),
            ('date_order', '<=', date_to),
            ('state', 'in', ['draft', 'sent']),
        ]
        if zone_id:
            domain.append(('partner_id.tti_city_zone_id', '=', zone_id))
        open_q_orders = SaleOrder.search(domain)
        open_q = sum(open_q_orders.mapped('amount_total'))
        print(f"[DASHBOARD] Open Quotations: {len(open_q_orders)} orders, Total = {open_q}")

        # --- Month-over-Month Growth ---
        # --- Month-over-Month Growth ---
        cur_year, cur_month = date_from.year, date_from.month

        # Calculate prev month/year
        if cur_month == 1:
            prev_year, prev_month = cur_year - 1, 12
        else:
            prev_year, prev_month = cur_year, cur_month - 1

        # Current month range
        cur_start = date(cur_year, cur_month, 1)
        cur_end = date(cur_year, cur_month, monthrange(cur_year, cur_month)[1])

        # Previous month range
        prev_start = date(prev_year, prev_month, 1)
        prev_end = date(prev_year, prev_month, monthrange(prev_year, prev_month)[1])

        # Fetch invoices with optional zone filter
        cur_domain = [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', cur_start),
            ('invoice_date', '<=', cur_end),
        ]
        prev_domain = [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', prev_start),
            ('invoice_date', '<=', prev_end),
        ]
        if zone_id:
            cur_domain.append(('partner_id.tti_city_zone_id', '=', zone_id))
            prev_domain.append(('partner_id.tti_city_zone_id', '=', zone_id))

        cur_invoices = Invoice.search(cur_domain)
        prev_invoices = Invoice.search(prev_domain)

        sales_current = sum(cur_invoices.mapped('amount_total'))
        sales_prev = sum(prev_invoices.mapped('amount_total'))

        mom_growth = ((sales_current - sales_prev) / sales_prev * 100) if sales_prev else 0.0
        print(f"[DASHBOARD] MoM Growth: Current={sales_current}, Prev={sales_prev}, Growth={mom_growth}%")

        # --- PoP Growth ---
        period_length = (date_to - date_from).days + 1
        prev_start = date_from - timedelta(days=period_length)
        prev_end = date_from - timedelta(days=1)

        cur_domain = [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to),
        ]
        prev_domain = [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', prev_start),
            ('invoice_date', '<=', prev_end),
        ]
        if zone_id:
            cur_domain.append(('partner_id.tti_city_zone_id', '=', zone_id))
            prev_domain.append(('partner_id.tti_city_zone_id', '=', zone_id))

        cur_invoices = Invoice.search(cur_domain)
        sales_current = sum(cur_invoices.mapped('amount_total'))

        prev_invoices = Invoice.search(prev_domain)
        sales_prev = sum(prev_invoices.mapped('amount_total'))

        pop_growth = ((sales_current - sales_prev) / sales_prev * 100) if sales_prev else 0.0
        print(f"[DASHBOARD] PoP Growth: Current={sales_current}, Prev={sales_prev}, Growth={pop_growth}%")

        # --- YoY Growth ---
        fy, ty = date_from.year, date_to.year
        years_length = ty - fy + 1  # total years selected

        prev_from_year = fy - years_length
        prev_to_year = ty - years_length

        # Current period range
        cur_start = date(fy, 1, 1)
        cur_end = date(ty, 12, 31)

        # Previous period range
        prev_start = date(prev_from_year, 1, 1)
        prev_end = date(prev_to_year, 12, 31)

        cur_domain = [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', cur_start),
            ('invoice_date', '<=', cur_end),
        ]
        prev_domain = [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', prev_start),
            ('invoice_date', '<=', prev_end),
        ]
        if zone_id:
            cur_domain.append(('partner_id.tti_city_zone_id', '=', zone_id))
            prev_domain.append(('partner_id.tti_city_zone_id', '=', zone_id))

        cur_invoices = Invoice.search(cur_domain)
        sales_current = sum(cur_invoices.mapped('amount_total'))

        prev_invoices = Invoice.search(prev_domain)
        sales_prev = sum(prev_invoices.mapped('amount_total'))

        yoy_growth = ((sales_current - sales_prev) / sales_prev * 100) if sales_prev else 0.0
        print(f"[DASHBOARD] YoY Growth: Current={sales_current}, Prev={sales_prev}, Growth={yoy_growth}%")

        # --- Samples Run (confirmed SO count) ---
        samples_domain = [
            ('date_order', '>=', date_from),
            ('date_order', '<=', date_to),
            ('state', '=', 'sale'),
        ]
        if zone_id:
            samples_domain.append(('partner_id.tti_city_zone_id', '=', zone_id))
        samples_run = SaleOrder.search_count(samples_domain)
        print(f"[DASHBOARD] Samples Run: {samples_run}")

        # --- Pending Reports (confirmed SO not fully invoiced) ---
        pending_domain = [
            ('date_order', '>=', date_from),
            ('date_order', '<=', date_to),
            ('state', '=', 'sale'),
            ('invoice_status', '!=', 'invoiced'),
        ]
        if zone_id:
            pending_domain.append(('partner_id.tti_city_zone_id', '=', zone_id))
        pending_reports = SaleOrder.search_count(pending_domain)
        print(f"[DASHBOARD] Pending Reports: {pending_reports}")

        # --- Reports Sent (posted invoices count) ---
        reports_domain = [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to),
        ]
        if zone_id:
            reports_domain.append(('partner_id.tti_city_zone_id', '=', zone_id))
        reports_sent = Invoice.search_count(reports_domain)
        print(f"[DASHBOARD] Reports Sent: {reports_sent}")

        # --- Top 10 Clients ---
        query = """
            SELECT am.partner_id, rp.name, SUM(am.amount_total) AS total
            FROM account_move am
            JOIN res_partner rp ON rp.id = am.partner_id
            WHERE am.move_type = 'out_invoice'
              AND am.state = 'posted'
              AND am.invoice_date >= %s
              AND am.invoice_date <= %s
        """
        params = [date_from, date_to]
        if zone_id:
            query += " AND rp.tti_city_zone_id = %s"
            params.append(zone_id)

        query += " GROUP BY am.partner_id, rp.name ORDER BY total DESC LIMIT 10"
        self.env.cr.execute(query, tuple(params))

        top_clients = [
            {"id": int(row[0]), "name": row[1], "total": float(row[2])}
            for row in self.env.cr.fetchall()
        ]
        print(f"[DASHBOARD] Top Clients: {top_clients}")

        # --- Invoice Counts ---
        invoice_domain = [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to),
        ]
        if zone_id:
            invoice_domain.append(('partner_id.tti_city_zone_id', '=', zone_id))
        all_invoices = Invoice.search(invoice_domain)

        total_invoices = len(all_invoices)

        paid_count = sum(1 for inv in all_invoices if inv.payment_state == 'paid')
        not_paid_count = sum(1 for inv in all_invoices if inv.payment_state == 'not_paid')
        partial_count = sum(1 for inv in all_invoices if inv.payment_state == 'partial')

        print(f"[DASHBOARD] Invoices: total={total_invoices}, paid={paid_count}, "
              f"not_paid={not_paid_count}, partial={partial_count}")

        # --- Top 10 Buyers ---
        query = """
            SELECT am.partner_id, rp.name, SUM(am.amount_total) AS total
            FROM account_move am
            JOIN res_partner rp ON rp.id = am.partner_id
            WHERE am.move_type = 'out_invoice'
              AND am.state = 'posted'
              AND am.invoice_date >= %s
              AND am.invoice_date <= %s
              AND rp.tti_company_category = 'buyer'
        """
        params = [date_from, date_to]
        if zone_id:
            query += " AND rp.tti_city_zone_id = %s"
            params.append(zone_id)

        query += " GROUP BY am.partner_id, rp.name ORDER BY total DESC LIMIT 10"
        self.env.cr.execute(query, tuple(params))

        top_buyers = [
            {"id": int(row[0]), "name": row[1], "total": float(row[2])}
            for row in self.env.cr.fetchall()
        ]
        print(f"[DASHBOARD] Top Buyers: {top_buyers}")

        # --- New Clients / New Brands (by create_date) ---
        # New Clients = created in range, not buyer/brand
        query = """
            SELECT COUNT(*) 
            FROM res_partner rp
            WHERE rp.active = TRUE
              AND (rp.tti_company_category IS NULL OR rp.tti_company_category NOT IN ('buyer','brand'))
              AND rp.create_date::date BETWEEN %s AND %s
        """
        params = [date_from, date_to]
        if zone_id:
            query += " AND rp.tti_city_zone_id = %s"
            params.append(zone_id)
        self.env.cr.execute(query, tuple(params))
        new_clients = int(self.env.cr.fetchone()[0] or 0)

        # New Brands = created in range with category 'brand'
        query = """
            SELECT COUNT(*)
            FROM res_partner rp
            WHERE rp.active = TRUE
              AND rp.tti_company_category = 'brand'
              AND rp.create_date::date BETWEEN %s AND %s
        """
        params = [date_from, date_to]
        if zone_id:
            query += " AND rp.tti_city_zone_id = %s"
            params.append(zone_id)
        self.env.cr.execute(query, tuple(params))
        new_brands = int(self.env.cr.fetchone()[0] or 0)

        # --- Lost Clients / Lost Brands ---
        lost_window_end = date_from - timedelta(days=1)
        lost_window_start = date_from - relativedelta(months=4)

        query = """
            WITH prior AS (
                SELECT DISTINCT am.partner_id
                FROM account_move am
                JOIN res_partner rp ON rp.id = am.partner_id
                WHERE am.move_type = 'out_invoice'
                  AND am.state = 'posted'
                  AND am.invoice_date < %s
        """
        params = [lost_window_start]
        if zone_id:
            query += " AND rp.tti_city_zone_id = %s"
            params.append(zone_id)

        query += """
                UNION
                SELECT DISTINCT so.partner_id
                FROM sale_order so
                JOIN res_partner rp2 ON rp2.id = so.partner_id
                WHERE so.date_order::date < %s
        """
        params.append(lost_window_start)
        if zone_id:
            query += " AND rp2.tti_city_zone_id = %s"
            params.append(zone_id)

        query += """
            ),
            win AS (
                SELECT DISTINCT am.partner_id
                FROM account_move am
                JOIN res_partner rp3 ON rp3.id = am.partner_id
                WHERE am.move_type = 'out_invoice'
                  AND am.state = 'posted'
                  AND am.invoice_date BETWEEN %s AND %s
        """
        params.extend([lost_window_start, lost_window_end])
        if zone_id:
            query += " AND rp3.tti_city_zone_id = %s"
            params.append(zone_id)

        query += """
                UNION
                SELECT DISTINCT so.partner_id
                FROM sale_order so
                JOIN res_partner rp4 ON rp4.id = so.partner_id
                WHERE so.date_order::date BETWEEN %s AND %s
        """
        params.extend([lost_window_start, lost_window_end])
        if zone_id:
            query += " AND rp4.tti_city_zone_id = %s"
            params.append(zone_id)

        query += """
            ),
            lost AS (
                SELECT partner_id AS id FROM prior
                EXCEPT
                SELECT partner_id AS id FROM win
            )
            SELECT
              SUM(CASE WHEN rp.tti_company_category = 'brand' THEN 1 ELSE 0 END) AS lost_brands,
              SUM(CASE WHEN COALESCE(rp.tti_company_category, '') NOT IN ('buyer','brand') THEN 1 ELSE 0 END) AS lost_clients
            FROM res_partner rp
            JOIN lost l ON l.id = rp.id
            WHERE rp.active = TRUE
        """
        self.env.cr.execute(query, tuple(params))
        lb, lc = self.env.cr.fetchone() or (0, 0)
        lost_brands = int(lb or 0)
        lost_clients = int(lc or 0)
        print(
            f"[DASHBOARD] New Clients={new_clients}, New Brands={new_brands}, Lost Clients={lost_clients}, Lost Brands={lost_brands}")

        # --- Invoice Partner Split Pie ---
        domain = [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to),
        ]
        if zone_id:
            domain.append(('partner_id.tti_city_zone_id', '=', zone_id))
        invoices = self.env['account.move'].search(domain)

        tti_amt = mts_amt = other_amt = 0.0
        total_amt = 0.0

        for inv in invoices:
            sel = inv.invoice_line_ids.mapped('sale_line_ids.order_id.tti_si_select_partner')
            # take the first non-empty selection if multiple SOs are linked
            sel = sel[0] if sel else None

            amt = float(inv.amount_total or 0.0)

            if sel == 'tti_testing':
                tti_amt += amt
            elif sel == 'mts':
                mts_amt += amt
            else:
                other_amt += amt

            total_amt += amt

        partner_pie = []
        if total_amt > 0:
            partner_pie = [
                {"label": "TTI Nomination", "value": round(tti_amt / total_amt * 100, 2)},
                {"label": "Eurofins", "value": round(mts_amt / total_amt * 100, 2)},
                {"label": "Others", "value": round(other_amt / total_amt * 100, 2)},
            ]
        else:
            if total_sales > 0:
                partner_pie = [{"label": "Others", "value": 100.0}]

        print(f"[DASHBOARD] Partner Pie (subtotal basis): {partner_pie}")

        # --- Sales Trends Line Chart (posted invoices by month, to_year and previous 2) ---
        cur_y = date_to.year
        years = [cur_y - 2, cur_y - 1, cur_y]
        range_start = date(years[0], 1, 1)
        range_end = date(years[-1], 12, 31)

        sql = """
            WITH so_meta AS (
                SELECT DISTINCT aml.move_id, so.tti_si_category, so.tti_si_sub_category
                FROM account_move_line aml
                JOIN sale_order_line_invoice_rel r ON r.invoice_line_id = aml.id
                JOIN sale_order_line sol ON sol.id = r.order_line_id
                JOIN sale_order so ON so.id = sol.order_id
            )
            SELECT
                EXTRACT(YEAR FROM am.invoice_date)::int AS y,
                EXTRACT(MONTH FROM am.invoice_date)::int AS m,
                SUM(am.amount_total) AS total
            FROM account_move am
            LEFT JOIN so_meta sm ON sm.move_id = am.id
            LEFT JOIN res_partner rp ON rp.id = am.partner_id
            WHERE am.move_type = 'out_invoice'
              AND am.state = 'posted'
              AND am.invoice_date BETWEEN %(start)s AND %(end)s
            GROUP BY y, m
        """
        params = {"start": range_start, "end": range_end}
        self.env.cr.execute(sql, params)

        rows = self.env.cr.fetchall()  # [(y, m, total), ...]
        by_year = {y: [0.0] * 12 for y in years}
        for y, m, total in rows:
            if y in by_year and 1 <= m <= 12:
                by_year[y][m - 1] = float(total or 0.0)

        sales_line = {
            "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
            "series": [{"label": str(y), "data": by_year[y]} for y in years],
        }
        print(f"[DASHBOARD] Sales Line: {sales_line}")

        # # --- Division-wise Contribution ---
        # query = """
        #     SELECT d.id, d.name, COALESCE(SUM(am.amount_total), 0) AS total
        #     FROM tti_division d
        #     LEFT JOIN tti_si_category c ON c.division_id = d.id
        #     LEFT JOIN sale_order so ON so.tti_si_category = c.id
        #     LEFT JOIN res_partner rp ON rp.id = so.partner_id
        #     LEFT JOIN sale_order_line sol ON sol.order_id = so.id
        #     LEFT JOIN sale_order_line_invoice_rel rel ON rel.order_line_id = sol.id
        #     LEFT JOIN account_move_line aml ON aml.id = rel.invoice_line_id
        #     LEFT JOIN account_move am ON am.id = aml.move_id
        #     WHERE am.move_type = 'out_invoice'
        #       AND am.state = 'posted'
        #       AND am.invoice_date >= %s
        #       AND am.invoice_date <= %s
        # """
        # params = [date_from, date_to]
        # if zone_id:
        #     query += " AND rp.tti_city_zone_id = %s"
        #     params.append(zone_id)
        #
        # query += " GROUP BY d.id, d.name ORDER BY d.name"
        # self.env.cr.execute(query, tuple(params))
        #
        # division_rows = self.env.cr.fetchall()  # [(id, name, total), ...]
        # division_bar = {
        #     "labels": [row[1] for row in division_rows],
        #     "series": [float(row[2]) for row in division_rows],
        # }
        # print(f"[DASHBOARD] Division Bar: {division_bar}")

        # --- Division-wise Contribution ---
        print("\n[DIVISION] Building division-wise contribution ...")
        division_bar = {"labels": [], "series": []}

        params = [date_from, date_to]
        where_extra = ""

        # Optional filters (apply if provided)
        if zone_id:
            where_extra += " AND rp.tti_city_zone_id = %s"
            params.append(zone_id)
        if cat_id:
            where_extra += " AND so.tti_si_category = %s"
            params.append(cat_id)
        if sub_id:
            # adjust field name if your subcategory field is different
            where_extra += " AND so.tti_si_sub_category = %s"
            params.append(sub_id)

        sql_division = f"""
            WITH relevant_moves AS (
                /* De-duplicate invoices per division to avoid line-level double counting */
                SELECT DISTINCT
                    am.id                         AS move_id,
                    d.id                          AS division_id,
                    d.name                        AS division_name
                FROM tti_division d
                JOIN tti_si_category c           ON c.division_id = d.id
                JOIN sale_order so               ON so.tti_si_category = c.id
                JOIN sale_order_line sol         ON sol.order_id = so.id
                JOIN sale_order_line_invoice_rel rel ON rel.order_line_id = sol.id
                JOIN account_move_line aml       ON aml.id = rel.invoice_line_id
                JOIN account_move am             ON am.id = aml.move_id
                JOIN res_partner rp              ON rp.id = am.partner_id
                WHERE am.state = 'posted'
                  AND am.move_type IN ('out_invoice', 'out_refund')
                  AND am.invoice_date >= %s
                  AND am.invoice_date <= %s
                  {where_extra}
            ),
            div_totals AS (
                SELECT
                    rm.division_id,
                    rm.division_name,
                    SUM(am.amount_total_in_currency_signed) AS total
                FROM relevant_moves rm
                JOIN account_move am ON am.id = rm.move_id
                GROUP BY rm.division_id, rm.division_name
            )
            SELECT
                d.id,
                d.name,
                COALESCE(dt.total, 0) AS total
            FROM tti_division d
            LEFT JOIN div_totals dt ON dt.division_id = d.id
            ORDER BY total DESC, d.name;
        """

        print(f"[DIVISION] SQL params: {params}")
        self.env.cr.execute(sql_division, tuple(params))
        div_rows = self.env.cr.fetchall()
        print(f"[DIVISION] SQL rows: {div_rows}")

        div_labels = []
        div_series = []
        for div_id, div_name, div_total in div_rows:
            div_labels.append(div_name)
            div_series.append(float(div_total or 0.0))
            print(f"[DIVISION] Row -> id={div_id}, name={div_name}, total={float(div_total or 0.0)}")

        division_bar = {"labels": div_labels, "series": div_series}
        print(f"[DIVISION] Final division_bar => labels={div_labels}, series={div_series}")

        # # --- Targets Achieved ---------
        print("\n\n\n\n\n\n\n\n\n\n\n")
        targets_rows = []
        targets_total_pct = 0.0

        if zone_id:
            print(f"[TARGETS] Zone Mode Activated. zone_id={zone_id}")

            # -------- City Zone behavior --------
            self.env.cr.execute("""
                        SELECT
                          rp.tti_city_zone_id AS zone_id,
                          COALESCE(SUM(am.amount_total_in_currency_signed), 0) AS total
                        FROM account_move am
                        JOIN res_partner rp ON rp.id = am.partner_id
                        WHERE am.state = 'posted'
                          AND am.move_type = 'out_invoice'
                          AND am.invoice_date >= %s
                          AND am.invoice_date <= %s
                          AND rp.tti_city_zone_id IS NOT NULL
                        GROUP BY rp.tti_city_zone_id
                    """, (date_from, date_to))

            inv_by_zone = {int(r[0]): float(r[1] or 0.0) for r in self.env.cr.fetchall()}
            print(f"[TARGETS] Invoices by Zone: {inv_by_zone}")

            # All target lines for the selected zone
            self.env.cr.execute("""
                        SELECT tz.id, tz.name, COALESCE(ta.target, 0.0) AS target
                        FROM target_achieve ta
                        JOIN tti_city_zone tz ON tz.id = ta.city_zones
                        WHERE tz.id = %s
                    """, (zone_id,))
            rows = self.env.cr.fetchall()
            print(f"[TARGETS] Target rows for zone: {rows}")

            zone_name = None
            zone_pct_sum = 0.0
            target_sum = 0.0
            invoiced_zone = float(inv_by_zone.get(int(zone_id), 0.0))
            print(f"[TARGETS] Total invoiced for this zone: {invoiced_zone}")

            for zid, zname, target in rows:
                zone_name = zname
                target = float(target or 0.0)
                print(f"[TARGETS] Row: zid={zid}, name={zname}, target={target}")
                if target > 0:
                    pct = (invoiced_zone / target) * 100.0
                    zone_pct_sum += pct
                    target_sum += target
                    print(f"[TARGETS] Contribution -> pct={pct}, zone_pct_sum={zone_pct_sum}, target_sum={target_sum}")

            if zone_name:
                targets_rows.append({
                    "name": zone_name,
                    "percentage": round(zone_pct_sum, 2),
                })
                print(f"[TARGETS] Added row: {targets_rows[-1]}")

            targets_total_pct = round((invoiced_zone / target_sum * 100.0), 2) if target_sum else 0.0
            print(f"[TARGETS] Final Zone Total %: {targets_total_pct}")

        else:
            # -------- City behavior --------
            self.env.cr.execute("""
                        SELECT
                          rp.tti_city_id AS city_id,
                          COALESCE(SUM(am.amount_total_in_currency_signed), 0) AS total
                        FROM account_move am
                        JOIN res_partner rp ON rp.id = am.partner_id
                        WHERE am.state = 'posted'
                          AND am.move_type = 'out_invoice'
                          AND am.invoice_date >= %s
                          AND am.invoice_date <= %s
                          AND rp.tti_city_id IS NOT NULL
                        GROUP BY rp.tti_city_id
                    """, (date_from, date_to))

            inv_by_city = {int(r[0]): float(r[1] or 0.0) for r in self.env.cr.fetchall()}
            print(f"[TARGETS][CITY] Invoices by City: {inv_by_city}")

            # All target lines per city (sum targets per city)
            self.env.cr.execute("""
                        SELECT c.id, c.name, COALESCE(SUM(ta.target), 0.0) AS total_target
                        FROM target_achieve ta
                        JOIN tti_city c ON c.id = ta.region
                        GROUP BY c.id, c.name
                    """)
            rows = self.env.cr.fetchall()
            total_target_sum = 0.0
            total_invoiced_sum = 0.0
            # Build detail rows
            for cid, cname, target_sum in rows:
                cid = int(cid)
                invoiced = float(inv_by_city.get(cid, 0.0))
                target_sum = float(target_sum or 0.0)
                print(f"[TARGETS][CITY] {cname} → Invoiced={invoiced}, Target={target_sum}")
                if target_sum > 0:
                    pct = (invoiced / target_sum) * 100.0
                    print(f"[TARGETS][CITY] {cname} → %Achieved={pct:.2f}%")
                    targets_rows.append({
                        "name": cname,
                        "percentage": round(pct, 2),
                    })
                    total_target_sum += target_sum
                    total_invoiced_sum += invoiced
            # Sort rows
            targets_rows.sort(key=lambda r: r["percentage"], reverse=True)
            # Total (weighted)
            targets_total_pct = round((total_invoiced_sum / total_target_sum * 100.0), 2) if total_target_sum else 0.0

            print(
                f"[TARGETS][CITY] TOTAL → Invoiced={total_invoiced_sum}, Targets={total_target_sum}, %Achieved={targets_total_pct}")
            print(f"[TARGETS] Final City Total %: {targets_total_pct}")

        targets_filters_applied = False


        return {
            'total_sales': round(total_sales, 2),
            'total_recovery': round(total_recovery, 2),
            'recovered_pct': round(recovered_pct, 2),
            'pending_so': round(pending_so, 2),
            'open_quotations': round(open_q, 2),
            'mom_growth': round(mom_growth, 2),
            'pop_growth': round(pop_growth, 2),
            'yoy_growth': round(yoy_growth, 2),
            'samples_run': samples_run,
            'pending_reports': pending_reports,
            'reports_sent': reports_sent,
            'top_clients': top_clients,
            'total_invoices': total_invoices,
            'paid_invoices': paid_count,
            'not_paid_invoices': not_paid_count,
            'partial_invoices': partial_count,
            'top_buyers': top_buyers,
            'new_clients': new_clients,
            'new_brands': new_brands,
            'lost_clients': lost_clients,
            'lost_brands': lost_brands,
            'partner_pie': partner_pie,
            'sales_line': sales_line,
            'division_bar': division_bar,
            'targets_achieved': targets_rows,
            'targets_total_pct': targets_total_pct,
            'targets_filters_applied': targets_filters_applied,

        }
