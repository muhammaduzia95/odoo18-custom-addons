//D:\Visiomate\Odoo\odoo18\custom_addons\tti\visio_tti_cs_dash\static\src\js\cs_live_dashboard.js

/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";

function formatNowPKT() {
  const tz = "Asia/Karachi";
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: tz,
    weekday: "long",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  }).formatToParts(new Date());
  const get = (t) => parts.find((p) => p.type === t)?.value || "";
  const weekday = get("weekday"), day = get("day"), month = get("month");
  const year = get("year"), hour = get("hour"), minute = get("minute");
  const ampm = (get("dayPeriod") || "").toLowerCase();
  return `${weekday} | ${day}/${month}/${year} | ${hour}:${minute} ${ampm}`;
}

class TTICSLiveDashboard extends Component {
  static template = "TTICSLiveDashboardMain";

  async refreshDashboardData() {
  await this.fetchReportDelivery();
  await this.fetchReportsDueToday();
  await this.fetchRightPersonSummary();
}

  setup() {
    this.state = useState({
      date_from: "",
      date_to: "",
      now: "",
      delivery: { delivered: 0, late: 0, pending: 0, total: 0 },
      due_today: [],
      right_rows: [],
    });

    this._clock = null;
    this.leftDonut = null;

    onMounted(async () => {
      // --- live clock update every 30s ---
      this.state.now = formatNowPKT();
      this._clock = setInterval(() => {
        this.state.now = formatNowPKT();
      }, 30000);

      // --- initial load ---
      await this.loadFilters();
      await this.refreshDashboardData();

      // --- auto refresh dashboard every 1 minute ---
      this._refreshInterval = setInterval(async () => {
        console.log("[CS-LIVE] Auto refreshing dashboard...");
        await this.refreshDashboardData();
      }, 60000); // 60,000 ms = 1 minute
    });

    onWillUnmount(() => {
      if (this._clock) clearInterval(this._clock);
      if (this._refreshInterval) clearInterval(this._refreshInterval);
      if (this.leftDonut) {
        try { this.leftDonut.destroy(); } catch(_) {}
      }
});

  }

  async loadFilters() {
    try {
      const res = await rpc("/tti_cs_live_dashboard/filters", {});
      this.state.date_from = res.default_date_from;
      this.state.date_to = res.default_date_to;
    } catch (err) {
      console.error("Error loading filters:", err);
    }
  }

  async fetchReportDelivery() {
    const payload = { date_from: this.state.date_from, date_to: this.state.date_to };
    try {
      const res = await rpc("/tti_cs_live_dashboard/report_delivery", payload);
      this.state.delivery = {
        delivered: res.delivered || 0,
        late: res.late || 0,
        pending: res.pending || 0,
        total: res.total || 0,
      };
      this.renderLiveLeftDonut();  // <-- this exists now
    } catch (err) {
      console.error("Error loading live left donut:", err);
    }
  }

  async fetchReportsDueToday() {
    try {
      const res = await rpc("/tti_cs_live_dashboard/reports_due_today", {});
      this.state.due_today = res.rows || [];
    } catch (err) {
      console.error("Error loading Reports Due Today:", err);
    }
  }

  async fetchRightPersonSummary() {
    try {
      const payload = { date_from: this.state.date_from, date_to: this.state.date_to };
      const res = await rpc("/tti_cs_live_dashboard/right_person_summary", payload);
      this.state.right_rows = res.rows || [];
    } catch (err) {
      console.error("Error loading right table:", err);
    }
  }

  // --------- THE MISSING FUNCTION (now implemented) ----------
  renderLiveLeftDonut() {
    const canvas = document.getElementById("live_left_donut");
    if (!canvas || typeof window.Chart === "undefined") {
      console.warn("Chart.js not found or canvas missing");
      return;
    }

    if (this.leftDonut) {
      try { this.leftDonut.destroy(); } catch(_) {}
      this.leftDonut = null;
    }

    const labels = ["Delivered Reports", "Late Reports", "Pending Reports"];
    const d = this.state.delivery || {};
    const data = [d.delivered || 0, d.late || 0, d.pending || 0];
    const total = data.reduce((a, b) => a + b, 0);
    const colors = ["#156082", "#196B24", "#E97132"];

    const sliceLabels = {
      id: "sliceLabelsLiveLeft",
      afterDatasetsDraw: (chart) => {
        if (!total) return;
        const { ctx } = chart;
        const meta = chart.getDatasetMeta(0);
        ctx.save();
        ctx.font = "bold 12px sans-serif";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        meta.data.forEach((arc, i) => {
          const val = data[i];
          if (!val) return;
          const a = (arc.startAngle + arc.endAngle) / 2;
          const r = (arc.outerRadius + arc.innerRadius) / 2;
          const x = arc.x + Math.cos(a) * r * 1.02;
          const y = arc.y + Math.sin(a) * r * 1.02;
          const txt = `${labels[i].replace(" Reports", "")}, ${val}`;
          ctx.lineWidth = 3;
          ctx.strokeStyle = "#fff";
          ctx.strokeText(txt, x, y);
          ctx.fillStyle = "#333"; ctx.fillText(txt, x, y);
        });
        ctx.restore();
      },
    };

    const centerText = {
      id: "centerTextLiveLeft",
      afterDraw(chart) {
        const { ctx, chartArea } = chart;
        const cx = (chartArea.left + chartArea.right) / 2;
        const cy = (chartArea.top + chartArea.bottom) / 2;
        ctx.save();
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.font = "700 24px sans-serif";
        ctx.fillText(String(total), cx, cy - 8);
        ctx.font = "400 12px sans-serif";
        ctx.fillText("Total Reports", cx, cy + 12);
        ctx.restore();
      },
    };

    const ctx = canvas.getContext("2d");
    this.leftDonut = new window.Chart(ctx, {
      type: "doughnut",
      data: {
        labels,
        datasets: [{
          data,
          backgroundColor: colors,
          borderWidth: 2,
          borderColor: "#fff",
        }],
      },
     options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "60%",
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            boxWidth: 10,
            boxHeight: 10,
            padding: 12,
            generateLabels(chart) {
              const ds = chart.data.datasets[0] || { data: [], backgroundColor: [] };
              const labels = chart.data.labels || [];
              const meta = chart.getDatasetMeta(0);
              return labels.map((lbl, i) => ({
                text: `${lbl.replace(" Reports", "")}, ${ds.data[i] ?? 0}`,
                fillStyle: Array.isArray(ds.backgroundColor) ? ds.backgroundColor[i] : ds.backgroundColor,
                strokeStyle: "#fff",
                lineWidth: 2,
                hidden: meta.data[i] ? meta.data[i].hidden : false,
                index: i,
                datasetIndex: 0,
              }));
            },
          },
        },
        tooltip: { enabled: false },
      },
    },


      plugins: [sliceLabels, centerText],
    });
  }
  // -----------------------------------------------------------

  async onFilterChange() {
    await this.fetchReportDelivery();
    await this.fetchReportsDueToday();
    await this.fetchRightPersonSummary();
  }
}

registry.category("actions").add("tti_cs_live_dashboard_action", TTICSLiveDashboard);
export default TTICSLiveDashboard;
