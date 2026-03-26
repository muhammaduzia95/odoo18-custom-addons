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
    def get_kpis(self, date_from, date_to, cat_id=False, sub_id=False, zone_id=False, company_id=False):

        SaleOrder = self.env['sale.order'].sudo()
        Invoice = self.env['account.move'].sudo()
        Payment = self.env['account.payment'].sudo()

        company_id = int(company_id or self.env.company.id)
        COMPANY_DOM = [('company_id', '=', company_id)]

        # --- Total Sales (posted invoices) ---
        domain = COMPANY_DOM + [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to),
        ]

        # --- CATEGORY FILTERS ---
        if cat_id:
            domain.append(('invoice_line_ids.sale_line_ids.order_id.tti_si_category', '=', cat_id))
        if sub_id:
            domain.append(('invoice_line_ids.sale_line_ids.order_id.tti_si_sub_category', '=', sub_id))
        # --- ZONE FILTER ---
        if zone_id:
            domain.append(('partner_id.tti_city_zone_id', '=', zone_id))

        invoices = Invoice.search(domain)
        total_sales = sum(invoices.mapped('amount_total'))
        total_sales_ids = invoices.ids

        print(
            f"[DASHBOARD][TOTAL_SALES] Invoices={len(invoices)} | Amount={total_sales} | cat={cat_id} | sub={sub_id} | zone={zone_id}")
        print(f"[DASHBOARD][TOTAL_SALES] Invoices={len(invoices)} | Amount={total_sales}")
        print(f"[DASHBOARD][TOTAL_SALES_IDS] Sending IDs to JS: {total_sales_ids}")

        # --- Total Recovery (from posted invoices ONLY — NO Payments) ---
        recovery_domain = COMPANY_DOM + [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', '=', 'paid'),
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to),
        ]

        # CATEGORY FILTERS
        if cat_id:
            recovery_domain.append(('invoice_line_ids.sale_line_ids.order_id.tti_si_category', '=', cat_id))

        if sub_id:
            recovery_domain.append(('invoice_line_ids.sale_line_ids.order_id.tti_si_sub_category', '=', sub_id))

        # ZONE FILTER
        if zone_id:
            recovery_domain.append(('partner_id.tti_city_zone_id', '=', zone_id))

        paid_invoices = Invoice.search(recovery_domain)
        total_recovery = sum(paid_invoices.mapped('amount_total'))
        total_recovery_ids = paid_invoices.ids

        print(
            f"[DASHBOARD][RECOVERY_NEW] Invoices={len(paid_invoices)} "
            f"| Amount={total_recovery} "
            f"| cat={cat_id} | sub={sub_id} | zone={zone_id}"
        )

        # --- Recovered Percentage ---
        recovered_pct = (total_recovery / total_sales * 100) if total_sales else 0.0
        print(f"[DASHBOARD] Recovered Percentage: {recovered_pct}")

        # --- Pending SO (confirmed but not fully invoiced) ---
        domain = COMPANY_DOM + [
            ('date_order', '>=', date_from),
            ('date_order', '<=', date_to),
            ('state', '=', 'sale'),
            ('invoice_status', '!=', 'invoiced'),
        ]

        # --- CATEGORY FILTERS on Sale Order ---
        if cat_id:
            domain.append(('tti_si_category', '=', cat_id))

        if sub_id:
            domain.append(('tti_si_sub_category', '=', sub_id))

        # --- ZONE FILTER ---
        if zone_id:
            domain.append(('partner_id.tti_city_zone_id', '=', zone_id))

        pending_so_orders = SaleOrder.search(domain)
        pending_so = sum(pending_so_orders.mapped('amount_total'))
        pending_so_ids = pending_so_orders.ids

        print(
            f"[DASHBOARD][PENDING_SO] Orders={len(pending_so_orders)} | Total={pending_so} | cat={cat_id} | sub={sub_id} | zone={zone_id}")

        # --- Open Quotations (draft/sent SO) ---
        domain = COMPANY_DOM + [
            ('date_order', '>=', date_from),
            ('date_order', '<=', date_to),
            ('state', 'in', ['draft', 'sent']),
        ]

        # --- CATEGORY FILTERS ---
        if cat_id:
            domain.append(('tti_si_category', '=', cat_id))
        if sub_id:
            domain.append(('tti_si_sub_category', '=', sub_id))
        # --- ZONE FILTER ---
        if zone_id:
            domain.append(('partner_id.tti_city_zone_id', '=', zone_id))

        open_q_orders = SaleOrder.search(domain)
        open_q = sum(open_q_orders.mapped('amount_total'))
        open_q_ids = open_q_orders.ids

        print(
            f"[DASHBOARD][OPEN_Q] Orders={len(open_q_orders)} | Total={open_q} | cat={cat_id} | sub={sub_id} | zone={zone_id}")

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

        # --- Current Month Domain ---
        cur_domain = COMPANY_DOM + [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', cur_start),
            ('invoice_date', '<=', cur_end),
        ]

        # CATEGORY FILTERS
        if cat_id:
            cur_domain.append(('invoice_line_ids.sale_line_ids.order_id.tti_si_category', '=', cat_id))
        if sub_id:
            cur_domain.append(('invoice_line_ids.sale_line_ids.order_id.tti_si_sub_category', '=', sub_id))

        # ZONE FILTER
        if zone_id:
            cur_domain.append(('partner_id.tti_city_zone_id', '=', zone_id))

        # --- Previous Month Domain ---
        prev_domain = COMPANY_DOM + [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', prev_start),
            ('invoice_date', '<=', prev_end),
        ]

        # CATEGORY FILTERS
        if cat_id:
            prev_domain.append(('invoice_line_ids.sale_line_ids.order_id.tti_si_category', '=', cat_id))
        if sub_id:
            prev_domain.append(('invoice_line_ids.sale_line_ids.order_id.tti_si_sub_category', '=', sub_id))

        # ZONE FILTER
        if zone_id:
            prev_domain.append(('partner_id.tti_city_zone_id', '=', zone_id))

        cur_invoices = Invoice.search(cur_domain)
        prev_invoices = Invoice.search(prev_domain)

        sales_current = sum(cur_invoices.mapped('amount_total'))
        sales_prev = sum(prev_invoices.mapped('amount_total'))

        mom_growth = ((sales_current - sales_prev) / sales_prev * 100) if sales_prev else 0.0

        print(
            f"[DASHBOARD][MOM] Cur={sales_current} Prev={sales_prev} Growth={mom_growth}% | cat={cat_id} | sub={sub_id} | zone={zone_id}")

        sales_current = sum(cur_invoices.mapped('amount_total'))
        sales_prev = sum(prev_invoices.mapped('amount_total'))

        mom_growth = ((sales_current - sales_prev) / sales_prev * 100) if sales_prev else 0.0
        print(f"[DASHBOARD] MoM Growth: Current={sales_current}, Prev={sales_prev}, Growth={mom_growth}%")

        # --- PoP Growth ---
        period_length = (date_to - date_from).days + 1
        prev_start = date_from - timedelta(days=period_length)
        prev_end = date_from - timedelta(days=1)

        # --- PoP Growth (Period-over-Period) ---
        period_length = (date_to - date_from).days + 1
        prev_start = date_from - timedelta(days=period_length)
        prev_end = date_from - timedelta(days=1)

        # --- Current Period Domain ---
        cur_domain = COMPANY_DOM + [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to),
        ]

        # CATEGORY FILTERS
        if cat_id:
            cur_domain.append(('invoice_line_ids.sale_line_ids.order_id.tti_si_category', '=', cat_id))
        if sub_id:
            cur_domain.append(('invoice_line_ids.sale_line_ids.order_id.tti_si_sub_category', '=', sub_id))

        # ZONE FILTER
        if zone_id:
            cur_domain.append(('partner_id.tti_city_zone_id', '=', zone_id))

        # --- Previous Period Domain ---
        prev_domain = COMPANY_DOM + [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', prev_start),
            ('invoice_date', '<=', prev_end),
        ]

        # CATEGORY FILTERS
        if cat_id:
            prev_domain.append(('invoice_line_ids.sale_line_ids.order_id.tti_si_category', '=', cat_id))
        if sub_id:
            prev_domain.append(('invoice_line_ids.sale_line_ids.order_id.tti_si_sub_category', '=', sub_id))

        # ZONE FILTER
        if zone_id:
            prev_domain.append(('partner_id.tti_city_zone_id', '=', zone_id))

        cur_invoices = Invoice.search(cur_domain)
        sales_current = sum(cur_invoices.mapped('amount_total'))

        prev_invoices = Invoice.search(prev_domain)
        sales_prev = sum(prev_invoices.mapped('amount_total'))

        pop_growth = ((sales_current - sales_prev) / sales_prev * 100) if sales_prev else 0.0

        print(
            f"[DASHBOARD][POP] Cur={sales_current} Prev={sales_prev} Growth={pop_growth}% | cat={cat_id} | sub={sub_id} | zone={zone_id}")

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

        # --- Current YoY Domain ---
        cur_domain = COMPANY_DOM + [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', cur_start),
            ('invoice_date', '<=', cur_end),
        ]

        # CATEGORY FILTERS
        if cat_id:
            cur_domain.append(('invoice_line_ids.sale_line_ids.order_id.tti_si_category', '=', cat_id))
        if sub_id:
            cur_domain.append(('invoice_line_ids.sale_line_ids.order_id.tti_si_sub_category', '=', sub_id))

        # ZONE FILTER
        if zone_id:
            cur_domain.append(('partner_id.tti_city_zone_id', '=', zone_id))

        # --- Previous YoY Domain ---
        prev_domain = COMPANY_DOM + [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', prev_start),
            ('invoice_date', '<=', prev_end),
        ]

        # CATEGORY FILTERS
        if cat_id:
            prev_domain.append(('invoice_line_ids.sale_line_ids.order_id.tti_si_category', '=', cat_id))
        if sub_id:
            prev_domain.append(('invoice_line_ids.sale_line_ids.order_id.tti_si_sub_category', '=', sub_id))

        # ZONE FILTER
        if zone_id:
            prev_domain.append(('partner_id.tti_city_zone_id', '=', zone_id))

        cur_invoices = Invoice.search(cur_domain)
        sales_current = sum(cur_invoices.mapped('amount_total'))

        prev_invoices = Invoice.search(prev_domain)
        sales_prev = sum(prev_invoices.mapped('amount_total'))

        yoy_growth = ((sales_current - sales_prev) / sales_prev * 100) if sales_prev else 0.0

        print(f"[DASHBOARD][YOY] Cur={sales_current} Prev={sales_prev} Growth={yoy_growth}% "
              f"| cat={cat_id} | sub={sub_id} | zone={zone_id}")

        # --- Samples Run (confirmed SO count) ---
        samples_domain = COMPANY_DOM + [
            ('date_order', '>=', date_from),
            ('date_order', '<=', date_to),
            ('state', '=', 'sale'),
        ]

        # CATEGORY FILTERS (from Sale Order itself)
        if cat_id:
            samples_domain.append(('tti_si_category', '=', cat_id))
        if sub_id:
            samples_domain.append(('tti_si_sub_category', '=', sub_id))
        # ZONE FILTER (same as before)
        if zone_id:
            samples_domain.append(('partner_id.tti_city_zone_id', '=', zone_id))

        samples_run_orders = SaleOrder.search(samples_domain)
        samples_run_ids = samples_run_orders.ids
        samples_run = len(samples_run_orders)
        print(f"[DASHBOARD][SAMPLES] Samples Run={samples_run} "
              f"| cat={cat_id} | sub={sub_id} | zone={zone_id}")

        # --- Pending Reports (confirmed SO not fully invoiced) ---
        pending_domain = COMPANY_DOM + [
            ('date_order', '>=', date_from),
            ('date_order', '<=', date_to),
            ('state', '=', 'sale'),
            ('invoice_status', '!=', 'invoiced'),
        ]

        # CATEGORY FILTERS (from Sale Order itself)
        if cat_id:
            pending_domain.append(('tti_si_category', '=', cat_id))
        if sub_id:
            pending_domain.append(('tti_si_sub_category', '=', sub_id))
        # ZONE FILTER (same as before)
        if zone_id:
            pending_domain.append(('partner_id.tti_city_zone_id', '=', zone_id))

        pending_reports_orders = SaleOrder.search(pending_domain)
        pending_reports_ids = pending_reports_orders.ids
        pending_reports = len(pending_reports_orders)
        print(f"[DASHBOARD][PENDING] Pending Reports={pending_reports} "
              f"| cat={cat_id} | sub={sub_id} | zone={zone_id}")

        # --- Reports Sent (posted invoices count) ---
        reports_domain = COMPANY_DOM + [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to),
        ]

        # CATEGORY FILTERS (same relation as Pie, MoM, YoY)
        if cat_id:
            reports_domain.append(('invoice_line_ids.sale_line_ids.order_id.tti_si_category', '=', cat_id))
        if sub_id:
            reports_domain.append(('invoice_line_ids.sale_line_ids.order_id.tti_si_sub_category', '=', sub_id))

        # ZONE FILTER
        if zone_id:
            reports_domain.append(('partner_id.tti_city_zone_id', '=', zone_id))

        reports_sent_recs = Invoice.search(reports_domain)
        reports_sent_ids = reports_sent_recs.ids
        reports_sent = len(reports_sent_recs)

        print(f"[DASHBOARD][REPORTS_SENT] Count={reports_sent} "
              f"| cat={cat_id} | sub={sub_id} | zone={zone_id}")

        # --- Top 10 Clients  ---
        query = """
            WITH inv_base AS (
                SELECT DISTINCT
                    am.id AS move_id,
                    am.partner_id,
                    rp.name,
                    am.amount_total
                FROM account_move am
                JOIN res_partner rp ON rp.id = am.partner_id

                -- Join invoice → SO metadata for category/subcategory
                LEFT JOIN account_move_line aml ON aml.move_id = am.id
                LEFT JOIN sale_order_line_invoice_rel rel ON rel.invoice_line_id = aml.id
                LEFT JOIN sale_order_line sol ON sol.id = rel.order_line_id
                LEFT JOIN sale_order so ON so.id = sol.order_id

                WHERE am.move_type = 'out_invoice'
                  AND am.state = 'posted'
                  AND am.company_id = %s
                  AND am.invoice_date >= %s
                  AND am.invoice_date <= %s
        """
        params = [company_id, date_from, date_to]

        # CATEGORY FILTER
        if cat_id:
            query += " AND so.tti_si_category = %s"
            params.append(cat_id)

        # SUB-CATEGORY FILTER
        if sub_id:
            query += " AND so.tti_si_sub_category = %s"
            params.append(sub_id)

        # ZONE FILTER
        if zone_id:
            query += " AND rp.tti_city_zone_id = %s"
            params.append(zone_id)

        query += """
            )
            SELECT
                partner_id,
                name,
                SUM(amount_total) AS total
            FROM inv_base
            GROUP BY partner_id, name
            ORDER BY total DESC
            LIMIT 10
        """
        self.env.cr.execute(query, tuple(params))
        rows = self.env.cr.fetchall()

        top_clients = []
        for partner_id, name, total in rows:
            # Use same filters for drilldown invoices
            inv_domain = COMPANY_DOM + [
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('partner_id', '=', partner_id),
                ('invoice_date', '>=', date_from),
                ('invoice_date', '<=', date_to),
            ]
            if cat_id:
                inv_domain.append(('invoice_line_ids.sale_line_ids.order_id.tti_si_category', '=', cat_id))
            if sub_id:
                inv_domain.append(('invoice_line_ids.sale_line_ids.order_id.tti_si_sub_category', '=', sub_id))
            if zone_id:
                inv_domain.append(('partner_id.tti_city_zone_id', '=', zone_id))

            inv_ids = Invoice.search(inv_domain).ids

            top_clients.append({
                "id": int(partner_id),
                "name": name,
                "total": float(total or 0.0),
                "invoice_ids": inv_ids,
            })

        print(f"[DASHBOARD][TOP_CLIENTS] Filters → cat={cat_id} | sub={sub_id} | zone={zone_id}")
        print(f"[DASHBOARD][TOP_CLIENTS] Result: {top_clients}")

        # --- Invoice Counts (posted invoices) ---
        invoice_domain = COMPANY_DOM + [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to),
        ]

        # CATEGORY FILTERS
        if cat_id:
            invoice_domain.append(('invoice_line_ids.sale_line_ids.order_id.tti_si_category', '=', cat_id))
        if sub_id:
            invoice_domain.append(('invoice_line_ids.sale_line_ids.order_id.tti_si_sub_category', '=', sub_id))

        # ZONE FILTER
        if zone_id:
            invoice_domain.append(('partner_id.tti_city_zone_id', '=', zone_id))

        all_invoices = Invoice.search(invoice_domain)
        total_invoices = len(all_invoices)
        total_invoices_ids = all_invoices.ids
        print("[DEBUG][TOTAL_INVOICES_IDS] →", total_invoices_ids)
        paid_count = sum(1 for inv in all_invoices if inv.payment_state == 'paid')
        paid_invoice_ids = [inv.id for inv in all_invoices if inv.payment_state == 'paid']
        print("[DEBUG][PAID_INVOICE_IDS] →", paid_invoice_ids)

        not_paid_count = sum(1 for inv in all_invoices if inv.payment_state == 'not_paid')
        not_paid_invoice_ids = [inv.id for inv in all_invoices if inv.payment_state == 'not_paid']
        print("[DEBUG][NOT_PAID_INVOICE_IDS] →", not_paid_invoice_ids)

        partial_count = sum(1 for inv in all_invoices if inv.payment_state == 'partial')
        partial_invoice_ids = [inv.id for inv in all_invoices if inv.payment_state == 'partial']
        print("[DEBUG][PARTIAL_INVOICE_IDS] →", partial_invoice_ids)

        print(f"[DASHBOARD][INVOICE_COUNTS] total={total_invoices}, paid={paid_count}, "
              f"not_paid={not_paid_count}, partial={partial_count} "
              f"| cat={cat_id} | sub={sub_id} | zone={zone_id}")

        # --- Top 10 Buyers (based on sale_order.tti_pi_buyer) ---
        # --- Top 10 Buyers (DE-DUPLICATED per invoice, based on so.tti_pi_buyer) ---
        print("\n================= TOP 10 BUYERS DEBUG =================")

        query = """
            WITH buyer_inv AS (
                SELECT DISTINCT
                    am.id AS move_id,
                    so.tti_pi_buyer AS buyer_id,
                    rp_buyer.name AS buyer_name,
                    am.amount_total
                FROM account_move am
                JOIN account_move_line aml ON aml.move_id = am.id
                JOIN sale_order_line_invoice_rel rel ON rel.invoice_line_id = aml.id
                JOIN sale_order_line sol ON sol.id = rel.order_line_id
                JOIN sale_order so ON so.id = sol.order_id
                JOIN res_partner rp_buyer ON rp_buyer.id = so.tti_pi_buyer
                JOIN res_partner rp_cust ON rp_cust.id = am.partner_id
                WHERE am.move_type = 'out_invoice'
                  AND am.state = 'posted'
                  AND am.company_id = %s
                  AND am.invoice_date >= %s
                  AND am.invoice_date <= %s
                  AND so.tti_pi_buyer IS NOT NULL
                  AND (%s IS NULL OR so.tti_si_category = %s)
                  AND (%s IS NULL OR so.tti_si_sub_category = %s)
        """
        params = [
            company_id,
            date_from,
            date_to,
            cat_id or None, cat_id or None,
            sub_id or None, sub_id or None,
        ]

        # ZONE FILTER (on customer partner)
        if zone_id:
            query += " AND rp_cust.tti_city_zone_id = %s"
            params.append(zone_id)

        query += """
            )
            SELECT
                buyer_id,
                buyer_name,
                SUM(amount_total) AS total
            FROM buyer_inv
            GROUP BY buyer_id, buyer_name
            ORDER BY total DESC
            LIMIT 10
        """

        print(f"[TOP_BUYERS][SQL] Query →\n{query}")
        print(f"[TOP_BUYERS][SQL] Params → {params}")

        self.env.cr.execute(query, tuple(params))
        rows = self.env.cr.fetchall()

        print(f"[TOP_BUYERS][SQL] Rows Returned → {rows}")

        top_buyers = []

        for buyer_id, buyer_name, total in rows:
            print("\n---------------------------------------------")
            print(f"[TOP_BUYERS] Processing Buyer → ID={buyer_id}, Name={buyer_name}, Total={total}")

            inv_domain = COMPANY_DOM + [
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('invoice_date', '>=', date_from),
                ('invoice_date', '<=', date_to),
                ('invoice_line_ids.sale_line_ids.order_id.tti_pi_buyer', '=', buyer_id),
            ]

            if cat_id:
                inv_domain.append(('invoice_line_ids.sale_line_ids.order_id.tti_si_category', '=', cat_id))
            if sub_id:
                inv_domain.append(('invoice_line_ids.sale_line_ids.order_id.tti_si_sub_category', '=', sub_id))
            if zone_id:
                inv_domain.append(('partner_id.tti_city_zone_id', '=', zone_id))

            print(f"[TOP_BUYERS] Invoice Domain for Buyer {buyer_name} → {inv_domain}")

            inv_ids = Invoice.search(inv_domain).ids

            print(f"[TOP_BUYERS] Invoice IDs for Buyer {buyer_name} → {inv_ids}")

            top_buyers.append({
                "id": int(buyer_id),
                "name": buyer_name,
                "total": float(total or 0.0),
                "invoice_ids": inv_ids,
            })

        print("\n[TOP_BUYERS] FINAL LIST →")
        for tb in top_buyers:
            print(f"  - {tb['id']} | {tb['name']} | Total={tb['total']} | Invoices={tb['invoice_ids']}")

        print("[TOP_BUYERS] Filters → cat=", cat_id, "sub=", sub_id, "zone=", zone_id)
        print("=========================================================\n")

        # --- New Clients / New Brands (by create_date) ---
        # --- New Clients (created in range & match category/subcategory through SO) ---
        query = """
            SELECT COUNT(DISTINCT rp.id)
            FROM res_partner rp
            LEFT JOIN sale_order so ON so.partner_id = rp.id
            WHERE rp.active = TRUE
              AND (rp.tti_company_category IS NULL OR rp.tti_company_category NOT IN ('buyer','brand'))
              AND so.company_id = %s
              AND rp.create_date::date BETWEEN %s AND %s
        """
        params = [company_id, date_from, date_to]

        # CATEGORY FILTERS
        if cat_id:
            query += " AND so.tti_si_category = %s"
            params.append(cat_id)

        if sub_id:
            query += " AND so.tti_si_sub_category = %s"
            params.append(sub_id)

        # ZONE
        if zone_id:
            query += " AND rp.tti_city_zone_id = %s"
            params.append(zone_id)

        self.env.cr.execute(query, tuple(params))
        query_ids = """
            SELECT DISTINCT rp.id
            FROM res_partner rp
            LEFT JOIN sale_order so ON so.partner_id = rp.id
            WHERE rp.active = TRUE
              AND (rp.tti_company_category IS NULL OR rp.tti_company_category NOT IN ('buyer','brand'))
              AND so.company_id = %s
              AND rp.create_date::date BETWEEN %s AND %s
        """
        params_ids = [company_id, date_from, date_to]

        if cat_id:
            query_ids += " AND so.tti_si_category = %s"
            params_ids.append(cat_id)

        if sub_id:
            query_ids += " AND so.tti_si_sub_category = %s"
            params_ids.append(sub_id)

        if zone_id:
            query_ids += " AND rp.tti_city_zone_id = %s"
            params_ids.append(zone_id)

        self.env.cr.execute(query_ids, tuple(params_ids))
        new_client_ids = [int(r[0]) for r in self.env.cr.fetchall()]

        new_clients = len(new_client_ids)

        print(f"[DASHBOARD][NEW_CLIENTS] Count={new_clients} | cat={cat_id} | sub={sub_id} | zone={zone_id}")

        # --- New Brands ---
        query = """
            SELECT COUNT(DISTINCT rp.id)
            FROM res_partner rp
            LEFT JOIN sale_order so ON so.partner_id = rp.id
            WHERE rp.active = TRUE
              AND rp.tti_company_category = 'brand'
              AND so.company_id = %s
              AND rp.create_date::date BETWEEN %s AND %s
        """
        params = [company_id, date_from, date_to]

        # CATEGORY FILTERS
        if cat_id:
            query += " AND so.tti_si_category = %s"
            params.append(cat_id)

        if sub_id:
            query += " AND so.tti_si_sub_category = %s"
            params.append(sub_id)

        # ZONE
        if zone_id:
            query += " AND rp.tti_city_zone_id = %s"
            params.append(zone_id)

        self.env.cr.execute(query, tuple(params))
        query_brand_ids = """
            SELECT DISTINCT rp.id
            FROM res_partner rp
            LEFT JOIN sale_order so ON so.partner_id = rp.id
            WHERE rp.active = TRUE
              AND rp.tti_company_category = 'brand'
              AND so.company_id = %s
              AND rp.create_date::date BETWEEN %s AND %s
        """
        params_brand_ids = [company_id, date_from, date_to]

        if cat_id:
            query_brand_ids += " AND so.tti_si_category = %s"
            params_brand_ids.append(cat_id)

        if sub_id:
            query_brand_ids += " AND so.tti_si_sub_category = %s"
            params_brand_ids.append(sub_id)

        if zone_id:
            query_brand_ids += " AND rp.tti_city_zone_id = %s"
            params_brand_ids.append(zone_id)

        self.env.cr.execute(query_brand_ids, tuple(params_brand_ids))
        new_brand_ids = [int(r[0]) for r in self.env.cr.fetchall()]
        new_brands = len(new_brand_ids)

        print(f"[DASHBOARD][NEW_BRANDS] Count={new_brands} | cat={cat_id} | sub={sub_id} | zone={zone_id}")

        # --- Lost Clients / Lost Brands ---
        # Definition:
        #   - previous_clients: customers with confirmed SOs BEFORE date_from
        #   - current_clients: customers with confirmed SOs BETWEEN date_from & date_to
        #   - lost = previous_clients - current_clients
        #
        # This respects:
        #   - category (tti_si_category)
        #   - subcategory (tti_si_sub_category)
        #   - zone (partner.tti_city_zone_id)

        # 1) Build domain for SOs BEFORE date_from
        prev_domain = COMPANY_DOM + [
            ("date_order", "<", date_from),
            ("state", "=", "sale"),
        ]
        if cat_id:
            prev_domain.append(("tti_si_category", "=", cat_id))
        if sub_id:
            prev_domain.append(("tti_si_sub_category", "=", sub_id))
        if zone_id:
            prev_domain.append(("partner_id.tti_city_zone_id", "=", zone_id))

        prev_orders = SaleOrder.search(prev_domain)
        previous_partner_ids = set(prev_orders.mapped("partner_id.id"))

        # 2) Build domain for SOs WITHIN selected range
        cur_domain = COMPANY_DOM + [
            ("date_order", ">=", date_from),
            ("date_order", "<=", date_to),
            ("state", "=", "sale"),
        ]
        if cat_id:
            cur_domain.append(("tti_si_category", "=", cat_id))
        if sub_id:
            cur_domain.append(("tti_si_sub_category", "=", sub_id))
        if zone_id:
            cur_domain.append(("partner_id.tti_city_zone_id", "=", zone_id))

        cur_orders = SaleOrder.search(cur_domain)
        current_partner_ids = set(cur_orders.mapped("partner_id.id"))

        # 3) Lost = had sales before, but nothing in current range
        lost_partner_ids = list(previous_partner_ids - current_partner_ids)

        # 4) Classify lost into clients vs brands using partner.tti_company_category
        Partners = self.env["res.partner"].sudo()
        lost_partners = Partners.browse(lost_partner_ids).filtered(lambda p: p.active)

        lost_brand_ids = lost_partners.filtered(
            lambda p: p.tti_company_category == "brand"
        ).ids

        lost_client_ids = lost_partners.filtered(
            lambda p: not p.tti_company_category
                      or p.tti_company_category not in ("buyer", "brand")
        ).ids

        lost_clients = len(lost_client_ids)
        lost_brands = len(lost_brand_ids)

        print(
            f"[DASHBOARD][LOST] lost_clients={lost_clients} "
            f"lost_brands={lost_brands} | cat={cat_id} | sub={sub_id} | zone={zone_id}"
        )

        # --- Invoice Partner Split Pie ---
        domain = COMPANY_DOM + [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to),
        ]
        # --- CATEGORY FILTERS ---
        if cat_id:
            domain.append(('invoice_line_ids.sale_line_ids.order_id.tti_si_category', '=', cat_id))
        if sub_id:
            domain.append(('invoice_line_ids.sale_line_ids.order_id.tti_si_sub_category', '=', sub_id))
        if zone_id:
            domain.append(('partner_id.tti_city_zone_id', '=', zone_id))
        invoices = self.env['account.move'].search(domain)

        print(f"[DASHBOARD][PIE] Invoices in range {date_from} → {date_to} (zone_id={zone_id}): {len(invoices)}")

        tti_amt = mts_amt = other_amt = 0.0
        total_amt = 0.0
        tti_count = mts_count = other_count = 0

        for inv in invoices:
            amt = float(inv.amount_total or 0.0)
            total_amt += amt

            sale_orders = inv.invoice_line_ids.mapped('sale_line_ids.order_id')

            if not sale_orders:
                other_amt += amt
                other_count += 1
                continue

            # Eurofins
            if any(so.tti_si_select_partner == 'mts' for so in sale_orders):
                mts_amt += amt
                mts_count += 1
                continue

            # TTI Nomination
            buyers = sale_orders.mapped('tti_pi_buyer')
            buyer_tag_names = set(buyers.mapped('category_id.name'))
            if 'Tti Nomination' in buyer_tag_names:
                tti_amt += amt
                tti_count += 1
                continue

            # Others
            other_amt += amt
            other_count += 1

        partner_pie = []
        if total_amt > 0:
            partner_pie = [
                {"label": "TTI Nomination", "value": round(tti_amt / total_amt * 100, 2)},
                {"label": "Eurofins", "value": round(mts_amt / total_amt * 100, 2)},
                {"label": "Self Reference", "value": round(other_amt / total_amt * 100, 2)},
            ]
        else:
            if total_sales > 0:
                partner_pie = [{"label": "Others", "value": 100.0}]

        print(f"[DASHBOARD][PIE] Totals: Invoices={len(invoices)} | Amount={total_amt}")
        print(f"[DASHBOARD][PIE]   Eurofins: {mts_count} invoices | {mts_amt}")
        print(f"[DASHBOARD][PIE]   TTI Nomination: {tti_count} invoices | {tti_amt}")
        print(f"[DASHBOARD][PIE]   Others: {other_count} invoices | {other_amt}")
        print(f"[DASHBOARD][PIE] Final Partner Pie: {partner_pie}")

        # --- Sales Trends Line Chart (posted invoices by month, to_year and previous 2) ---
        cur_y = date_to.year
        years = [cur_y - 2, cur_y - 1, cur_y]
        range_start = date(years[0], 1, 1)
        range_end = date(years[-1], 12, 31)

        sql = """
            WITH so_meta AS (
                SELECT DISTINCT 
                    aml.move_id,
                    so.tti_si_category,
                    so.tti_si_sub_category
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
              AND am.company_id = %(company_id)s
              AND am.invoice_date BETWEEN %(start)s AND %(end)s

              -- Category Filters Added Here
              AND (%(cat)s IS NULL OR sm.tti_si_category = %(cat)s)
              AND (%(sub)s IS NULL OR sm.tti_si_sub_category = %(sub)s)

            GROUP BY y, m
        """
        params = {
            "company_id": company_id,
            "start": range_start,
            "end": range_end,
            "cat": cat_id or None,
            "sub": sub_id or None,
        }
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

        # --- Division-wise Contribution (FIXED: no zone/cat/sub filters, sums am.amount_total_in_currency_signed) ---
        print("\n[DIVISION] Building division-wise contribution ...")
        division_bar = {"labels": [], "series": []}

        params = [company_id, date_from, date_to]
        print(f"[DIVISION] Date range: {date_from} -> {date_to}")

        # 1) Quick sanity: how many posted AR moves in range?
        self.env.cr.execute("""
            SELECT COUNT(*) AS cnt, COALESCE(SUM(am.amount_total_in_currency_signed),0) AS sum_signed
            FROM account_move am
            WHERE am.state='posted'
              AND am.move_type IN ('out_invoice','out_refund')
              AND am.company_id = %s
              AND am.invoice_date >= %s AND am.invoice_date <= %s
        """, tuple(params))
        row = self.env.cr.fetchone() or (0, 0.0)
        posted_cnt, posted_sum = int(row[0] or 0), float(row[1] or 0.0)
        print(f"[DIVISION] Posted AR moves in range: {posted_cnt}, Σ(amount_total_in_currency_signed)={posted_sum}")

        # 2) Main totals, mapping invoice -> division via SO category (SO has a single tti_si_category)
        sql_division = """
            WITH inv2div AS (
                SELECT DISTINCT
                    am.id                    AS move_id,
                    d.id                     AS division_id,
                    d.name                   AS division_name
                FROM account_move am
                JOIN account_move_line      aml  ON aml.move_id = am.id
                JOIN sale_order_line_invoice_rel rel ON rel.invoice_line_id = aml.id
                JOIN sale_order_line        sol  ON sol.id = rel.order_line_id
                JOIN sale_order             so   ON so.id = sol.order_id
                JOIN tti_si_category        c    ON c.id = so.tti_si_category
                JOIN tti_division           d    ON d.id = c.division_id
                WHERE am.state='posted'
                  AND am.move_type IN ('out_invoice','out_refund')
                  AND am.company_id = %s
                  AND am.invoice_date >= %s AND am.invoice_date <= %s
                  AND (%s IS NULL OR so.tti_si_category = %s)
                  AND (%s IS NULL OR so.tti_si_sub_category = %s)
            )
            SELECT
                d.id,
                d.name,
                COALESCE(SUM(am.amount_total_in_currency_signed), 0) AS total
            FROM tti_division d
            LEFT JOIN inv2div i ON i.division_id = d.id
            LEFT JOIN account_move am ON am.id = i.move_id
            GROUP BY d.id, d.name
            ORDER BY total DESC, d.name;
        """

        # print(f"[DIVISION] Executing division totals SQL with params={params}")
        # self.env.cr.execute(sql_division, tuple(params))
        # div_rows = self.env.cr.fetchall()
        # print(f"[DIVISION] Raw totals rows (division_id, name, total): {div_rows}")

        # Build params for division SQL (with cat + sub)
        params_div = [
            company_id,
            date_from,
            date_to,
            cat_id or None, cat_id or None,
            sub_id or None, sub_id or None,
        ]

        print(f"[DIVISION] Executing division totals SQL with params={params_div}")
        self.env.cr.execute(sql_division, tuple(params_div))
        div_rows = self.env.cr.fetchall()
        print(f"[DIVISION] Raw totals rows (division_id, name, total): {div_rows}")

        # 3) Debug: how many distinct invoices got mapped? any invoice mapped to >1 division?
        dup_check_sql = """
            WITH inv2div AS (
                SELECT DISTINCT
                    am.id AS move_id,
                    d.id  AS division_id
                FROM account_move am
                JOIN account_move_line      aml  ON aml.move_id = am.id
                JOIN sale_order_line_invoice_rel rel ON rel.invoice_line_id = aml.id
                JOIN sale_order_line        sol  ON sol.id = rel.order_line_id
                JOIN sale_order             so   ON so.id = sol.order_id
                JOIN tti_si_category        c    ON c.id = so.tti_si_category
                JOIN tti_division           d    ON d.id = c.division_id
                WHERE am.state='posted'
                  AND am.move_type IN ('out_invoice','out_refund')
                  AND am.company_id = %s
                  AND am.invoice_date >= %s AND am.invoice_date <= %s
            )
            SELECT COUNT(*) AS mapped_invoice_count
            FROM (SELECT DISTINCT move_id FROM inv2div) t
        """
        self.env.cr.execute(dup_check_sql, tuple(params))
        mapped_inv_cnt = int((self.env.cr.fetchone() or (0,))[0] or 0)
        print(f"[DIVISION] Distinct invoices mapped to a division: {mapped_inv_cnt} (of {posted_cnt} posted in range)")

        dup_list_sql = """
            WITH inv2div AS (
                SELECT DISTINCT
                    am.id AS move_id,
                    d.id  AS division_id
                FROM account_move am
                JOIN account_move_line      aml  ON aml.move_id = am.id
                JOIN sale_order_line_invoice_rel rel ON rel.invoice_line_id = aml.id
                JOIN sale_order_line        sol  ON sol.id = rel.order_line_id
                JOIN sale_order             so   ON so.id = sol.order_id
                JOIN tti_si_category        c    ON c.id = so.tti_si_category
                JOIN tti_division           d    ON d.id = c.division_id
                WHERE am.state='posted'
                  AND am.move_type IN ('out_invoice','out_refund')
                  AND am.company_id = %s
                  AND am.invoice_date >= %s AND am.invoice_date <= %s
            )
            SELECT move_id, COUNT(DISTINCT division_id) AS divs
            FROM inv2div
            GROUP BY move_id
            HAVING COUNT(DISTINCT division_id) > 1
            ORDER BY divs DESC
            LIMIT 10
        """
        self.env.cr.execute(dup_list_sql, tuple(params))
        dup_examples = self.env.cr.fetchall()
        if dup_examples:
            print(f"[DIVISION][WARN] Invoices mapped to multiple divisions (top 10): {dup_examples}")
            print(
                "[DIVISION][NOTE] If this happens, your invoices contain SO lines from multiple categories/divisions. "
                "Current logic assigns the FULL invoice total to EACH mapped division. "
                "If you need proportional allocation by lines, we must switch to line-based sums.")
        else:
            print("[DIVISION] No invoices mapped to multiple divisions (good).")

        # 4) Build the chart payload
        div_labels, div_series = [], []
        grand_sum = 0.0
        for div_id, div_name, div_total in div_rows:
            val = float(div_total or 0.0)
            div_labels.append(div_name)
            div_series.append(val)
            grand_sum += val
            print(f"[DIVISION] Row -> id={div_id}, name={div_name}, total={val}")

        division_bar = {"labels": div_labels, "series": div_series}
        print(f"[DIVISION] Final division_bar => labels={div_labels}, series={div_series}")
        print(f"[DIVISION] Cross-check: Σ(division totals)={grand_sum} vs Σ(all posted invoices)={posted_sum}")
        if abs(grand_sum) > 0 and abs(grand_sum - posted_sum) / max(1.0, abs(posted_sum)) > 0.01:
            print("[DIVISION][WARN] Division totals differ from global posted sum by >1%. "
                  "Likely due to invoices linked to multiple divisions (see WARN above).")

        # # --- Targets Achieved ---------
        print("\n\n\n\n\n\n\n\n\n\n\n")
        targets_rows = []
        targets_total_pct = 0.0

        Target = self.env["target.achieve"].sudo()

        def _count_months_overlap(start_a, end_a, start_b, end_b):
            """How many whole calendar months overlap between [start_a,end_a] and [start_b,end_b]."""
            if not start_a or not end_a:
                return 0
            # overlap window
            start = max(start_a, start_b)
            end = min(end_a, end_b)
            if start > end:
                return 0
            start_m = date(start.year, start.month, 1)
            end_m = date(end.year, end.month, 1)
            return (end_m.year - start_m.year) * 12 + (end_m.month - start_m.month) + 1

        def _compute_target_for_line(t):
            """
            Compute effective target for ONE target.achieve line,
            respecting:
              - v_date_from / v_date_to vs dashboard date_from/date_to
              - month-based target (target * number_of_months)
              - category split (if cat_id selected on dashboard)
            """
            base_target = float(t.target or 0.0)
            if base_target <= 0.0:
                return 0.0

            # Use v_date_* if set; otherwise treat as active only in the dashboard window
            if not t.v_date_from or not t.v_date_to:
                return 0.0

            t_from = t.v_date_from
            t_to = t.v_date_to

            months = _count_months_overlap(t_from, t_to, date_from, date_to)
            if months <= 0:
                return 0.0

            # If a category is selected on dashboard:
            #   - Only consider targets whose categories contain that category
            #   - Split the target equally across the number of categories
            if cat_id:
                cat_ids = t.categories.ids
                if not cat_ids or cat_id not in cat_ids:
                    return 0.0  # this target line doesn't belong to the selected category

                per_cat = base_target / len(cat_ids)
                return per_cat * months

            # No category filter → full target applies
            return base_target * months

        if zone_id:
            print(f"[TARGETS] Zone Mode Activated. zone_id={zone_id}")

            # -------- City Zone behavior: invoices (already filtered by cat/sub) --------
            self.env.cr.execute("""
                        SELECT
                          rp.tti_city_zone_id AS zone_id,
                          COALESCE(SUM(am.amount_total_in_currency_signed), 0) AS total
                        FROM account_move am
                        JOIN res_partner rp ON rp.id = am.partner_id

                        -- JOIN SO metadata for category/subcategory
                        LEFT JOIN account_move_line aml ON aml.move_id = am.id
                        LEFT JOIN sale_order_line_invoice_rel rel ON rel.invoice_line_id = aml.id
                        LEFT JOIN sale_order_line sol ON sol.id = rel.order_line_id
                        LEFT JOIN sale_order so ON so.id = sol.order_id

                        WHERE am.state = 'posted'
                          AND am.move_type = 'out_invoice'
                          AND am.company_id = %s
                          AND am.invoice_date >= %s
                          AND am.invoice_date <= %s
                          AND rp.tti_city_zone_id IS NOT NULL

                          AND (%s IS NULL OR so.tti_si_category = %s)
                          AND (%s IS NULL OR so.tti_si_sub_category = %s)

                        GROUP BY rp.tti_city_zone_id
                    """, (company_id, date_from, date_to,
                          cat_id or None, cat_id or None,
                          sub_id or None, sub_id or None))

            inv_by_zone = {int(r[0]): float(r[1] or 0.0) for r in self.env.cr.fetchall()}
            print(f"[TARGETS] Invoices by Zone: {inv_by_zone}")

            invoiced_zone = float(inv_by_zone.get(int(zone_id), 0.0))
            print(f"[TARGETS] Total invoiced for this zone: {invoiced_zone}")

            # Targets for this zone (month-wise + category split)
            target_lines = Target.search([("city_zones", "=", zone_id)])
            zone_name = None
            zone_target_total = 0.0

            for t in target_lines:
                if t.city_zones:
                    zone_name = t.city_zones.name
                line_target = _compute_target_for_line(t)
                if line_target > 0:
                    print(f"[TARGETS][ZONE] line id={t.id} name={t.name} → effective_target={line_target}")
                    zone_target_total += line_target

            print(f"[TARGETS][ZONE] zone_target_total={zone_target_total}")

            if zone_name and zone_target_total > 0:
                zone_pct = (invoiced_zone / zone_target_total) * 100.0 if zone_target_total else 0.0
                targets_rows.append({
                    "name": zone_name,
                    "percentage": round(zone_pct, 2),
                })
                print(f"[TARGETS] Added row: {targets_rows[-1]}")
                targets_total_pct = round(zone_pct, 2)
            else:
                targets_total_pct = 0.0

            print(f"[TARGETS] Final Zone Total %: {targets_total_pct}")

        else:
            # -------- City behavior --------
            # Invoices summed per city, already filtered by cat/sub
            self.env.cr.execute("""
                        SELECT
                          rp.tti_city_id AS city_id,
                          COALESCE(SUM(am.amount_total_in_currency_signed), 0) AS total
                        FROM account_move am
                        JOIN res_partner rp ON rp.id = am.partner_id

                        LEFT JOIN account_move_line aml ON aml.move_id = am.id
                        LEFT JOIN sale_order_line_invoice_rel rel ON rel.invoice_line_id = aml.id
                        LEFT JOIN sale_order_line sol ON sol.id = rel.order_line_id
                        LEFT JOIN sale_order so ON so.id = sol.order_id

                        WHERE am.state = 'posted'
                          AND am.move_type = 'out_invoice'
                          AND am.company_id = %s
                          AND am.invoice_date >= %s
                          AND am.invoice_date <= %s
                          AND rp.tti_city_id IS NOT NULL

                          AND (%s IS NULL OR so.tti_si_category = %s)
                          AND (%s IS NULL OR so.tti_si_sub_category = %s)

                        GROUP BY rp.tti_city_id
                    """, (company_id, date_from, date_to,
                          cat_id or None, cat_id or None,
                          sub_id or None, sub_id or None))

            inv_by_city = {int(r[0]): float(r[1] or 0.0) for r in self.env.cr.fetchall()}
            print(f"[TARGETS][CITY] Invoices by City: {inv_by_city}")

            # Build city-wise targets using ORM so we can apply:
            #   - v_date_from/v_date_to
            #   - month-based logic
            #   - category split (if cat filter present)
            city_targets = {}  # city_id -> total target
            city_names = {}  # city_id -> name

            target_lines = Target.search([("region", "!=", False)])
            for t in target_lines:
                city = t.region
                if not city:
                    continue

                eff_target = _compute_target_for_line(t)
                cid = city.id

                # Make sure city appears even if eff_target = 0
                city_targets.setdefault(cid, 0.0)
                city_names[cid] = city.name

                if eff_target > 0:
                    city_targets[cid] += eff_target
                    print(f"[TARGETS][CITY] line id={t.id} city={city.name} → +{eff_target}, total={city_targets[cid]}")
                else:
                    print(f"[TARGETS][CITY] line id={t.id} city={city.name} → skipped eff_target=0 but city kept")

            total_target_sum = 0.0
            total_invoiced_sum = 0.0

            # Build detail rows: 1 row per city (old behavior)
            for cid, city_target in city_targets.items():
                invoiced = float(inv_by_city.get(cid, 0.0))
                print(f"[TARGETS][CITY] {city_names[cid]} → Invoiced={invoiced}, Target={city_target}")
                if city_target > 0:
                    pct = (invoiced / city_target) * 100.0
                    print(f"[TARGETS][CITY] {city_names[cid]} → %Achieved={pct:.2f}%")
                    targets_rows.append({
                        "name": city_names[cid],
                        "percentage": round(pct, 2),
                    })
                    total_target_sum += city_target
                    total_invoiced_sum += invoiced

            # Sort rows (same as before)
            targets_rows.sort(key=lambda r: r["percentage"], reverse=True)

            # Total (weighted)
            targets_total_pct = round(
                (total_invoiced_sum / total_target_sum * 100.0), 2
            ) if total_target_sum else 0.0

            print(
                f"[TARGETS][CITY] TOTAL → Invoiced={total_invoiced_sum}, "
                f"Targets={total_target_sum}, %Achieved={targets_total_pct}"
            )
            print(f"[TARGETS] Final City Total %: {targets_total_pct}")

        targets_filters_applied = False

        print("\n[DEBUG][RETURN] Total Sales =", round(total_sales, 2))
        print("[DEBUG][RETURN] Total Sales IDs =", total_sales_ids, "\n")
        print("[DEBUG][RETURN] Total Recovery =", round(total_recovery, 2))
        print("[DEBUG][RETURN] Total Recovery IDs =", total_recovery_ids)
        print("[DEBUG][RETURN] Pending SO Count =", pending_so)
        print("[DEBUG][RETURN] Pending SO IDs =", pending_so_ids)
        print("[DEBUG][RETURN] Open Quotations Count =", open_q)
        print("[DEBUG][RETURN] Open Quotations IDs =", open_q_ids)
        print("[DEBUG][RETURN] Samples Run Count =", samples_run)
        print("[DEBUG][RETURN] Samples Run IDs =", samples_run_ids)

        print("[DEBUG][RETURN] New Client IDs =", len(new_client_ids))
        print("[DEBUG][RETURN] New Brand IDs =", len(new_brand_ids))
        print("[DEBUG][RETURN] Lost Client IDs =", len(lost_client_ids))
        print("[DEBUG][RETURN] Lost Brand IDs =", len(lost_brand_ids))

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

            'total_sales_ids': list(total_sales_ids),
            'total_recovery_ids': list(total_recovery_ids),
            'pending_so_ids': list(pending_so_ids),
            'open_quotations_ids': list(open_q_ids),
            'samples_run_ids': list(samples_run_ids),
            'pending_reports_ids': list(pending_reports_ids),
            'reports_sent_ids': list(reports_sent_ids),
            'new_client_ids': new_client_ids,
            'new_brand_ids': new_brand_ids,
            'lost_client_ids': lost_client_ids,
            'lost_brand_ids': lost_brand_ids,
            'total_invoices_ids': list(total_invoices_ids),
            'paid_invoice_ids': list(paid_invoice_ids),
            'not_paid_invoice_ids': list(not_paid_invoice_ids),
            'partial_invoice_ids': list(partial_invoice_ids),

        }
