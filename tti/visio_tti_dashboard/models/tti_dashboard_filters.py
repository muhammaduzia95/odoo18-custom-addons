# -*- coding: utf-8 -*-
# \tti\visio_tti_dashboard\models\tti_dashboard_filters.py

from psycopg2 import sql
from odoo import api, fields, models, tools


class TTIDashboardReport(models.Model):
    _name = 'visio.tti.dashboard.report'
    _description = 'TTI Dashboard (Sales Analysis)'
    _auto = False
    _order = 'date desc'

    # Fields present in the SQL view
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    date = fields.Date(string='Invoice Date', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    user_id = fields.Many2one('res.users', string='Salesperson', readonly=True)
    total_sales = fields.Float(string='Total Invoiced', readonly=True)

    # Filters (from SALE ORDER)
    category_id = fields.Many2one('tti.si.category', string='Category', readonly=True)
    subcategory_id = fields.Many2one('tti.si.sub.category', string='Subcategory', readonly=True)
    zone_id = fields.Many2one('tti.city.zone', string='Zone', readonly=True)

    # ---------- helpers ----------
    def _col_exists(self, table, column):
        self.env.cr.execute("""
            SELECT 1 FROM information_schema.columns
            WHERE table_name=%s AND column_name=%s
            LIMIT 1
        """, (table, column))
        return bool(self.env.cr.fetchone())

    def _pick_first_existing(self, table, candidates):
        """Return first existing column name from candidates on given table, else None."""
        for c in candidates:
            if self._col_exists(table, c):
                return c
        return None

    def _detect_rel_table(self):
        """Find the invoice_line <-> sale_order_line relation table name."""
        candidates = [
            'sale_order_line_invoice_rel',                # common recent
            'account_move_line_sale_order_line_rel',      # some variants
            'sale_order_line_account_move_line_rel',      # older/custom
        ]
        for t in candidates:
            self.env.cr.execute("""
                SELECT 1 FROM information_schema.tables
                WHERE table_name=%s LIMIT 1
            """, (t,))
            if self.env.cr.fetchone():
                return t
        return None

    @property
    def _table_query(self):
        # Detect columns present on sale_order
        so_cat = self._pick_first_existing('sale_order', [
            'si_category_id', 'tti_si_category_id', 'category_id', 'x_studio_category', 'x_category_id'
        ])
        so_sub = self._pick_first_existing('sale_order', [
            'si_sub_category_id', 'tti_si_sub_category_id', 'sub_category_id', 'x_studio_subcategory', 'x_subcategory_id'
        ])
        so_zone = self._pick_first_existing('sale_order', [
            'zone_id', 'city_zone_id', 'tti_zone_id', 'x_studio_zone', 'x_zone_id'
        ])

        rel_table = self._detect_rel_table()

        print("\n[TTI Dashboard] DETECTED:")
        print(" - sale_order.category column  :", so_cat or "(none)")
        print(" - sale_order.subcategory col. :", so_sub or "(none)")
        print(" - sale_order.zone column      :", so_zone or "(none)")
        print(" - invoice<->SO line rel table :", rel_table or "(none)", "\n")

        # Build lateral SELECT pieces (cast to integer to match many2one)
        cat_expr = f"so.{so_cat}::integer AS category_id" if so_cat else "NULL::integer AS category_id"
        sub_expr = f"so.{so_sub}::integer AS subcategory_id" if so_sub else "NULL::integer AS subcategory_id"
        zone_expr = f"so.{so_zone}::integer AS zone_id" if so_zone else "NULL::integer AS zone_id"

        # Build FROM with a safe lateral join; if rel table missing, fall back to NULLs
        if rel_table:
            from_sql = f"""
                FROM account_move am
                /* Pick ONE related sale order (if any) for each invoice to avoid duplication */
                LEFT JOIN LATERAL (
                    SELECT
                        {cat_expr},
                        {sub_expr},
                        {zone_expr}
                    FROM account_move_line aml
                    JOIN {rel_table} rel
                        ON rel.invoice_line_id = aml.id
                    JOIN sale_order_line sol
                        ON sol.id = rel.order_line_id
                    JOIN sale_order so
                        ON so.id = sol.order_id
                    WHERE aml.move_id = am.id
                    LIMIT 1
                ) AS so_meta ON TRUE
            """
        else:
            # No relation table found; keep the lateral with NULLs so the view still compiles
            from_sql = f"""
                FROM account_move am
                LEFT JOIN LATERAL (
                    SELECT
                        {cat_expr},
                        {sub_expr},
                        {zone_expr}
                    WHERE TRUE
                    LIMIT 1
                ) AS so_meta ON TRUE
            """

        select = """
            SELECT
                MIN(am.id) AS id,
                am.partner_id AS partner_id,
                am.invoice_date::date AS date,
                am.company_id AS company_id,
                am.invoice_user_id AS user_id,
                SUM(am.amount_total) AS total_sales,
                so_meta.category_id AS category_id,
                so_meta.subcategory_id AS subcategory_id,
                so_meta.zone_id AS zone_id
        """
        where = """
            WHERE am.move_type = 'out_invoice'
              AND am.state = 'posted'
            GROUP BY
              am.partner_id,
              am.invoice_date::date,
              am.company_id,
              am.invoice_user_id,
              so_meta.category_id,
              so_meta.subcategory_id,
              so_meta.zone_id
        """

        query = f"{select}\n{from_sql}\n{where}"
        print("\n[TTI Dashboard] _table_query:\n", query, "\n")
        return query

    def init(self):
        print("\n[TTI Dashboard] Dropping and creating SQL View for visio.tti.dashboard.report...\n")
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            sql.SQL("CREATE OR REPLACE VIEW {} AS ({})").format(
                sql.Identifier(self._table),
                sql.SQL(self._table_query)
            )
        )
        print("\n[TTI Dashboard] SQL View created successfully!\n")
