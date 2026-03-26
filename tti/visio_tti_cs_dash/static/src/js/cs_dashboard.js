//D:\Visiomate\Odoo\odoo18\custom_addons\tti\visio_tti_cs_dash\static\src\js\cs_dashboard.js
/** @odoo-module **/

/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onMounted } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
this.rightDonut = null;
const PERSON_COLORS = ["#0F9ED5", "#196B24", "#156082", "#E97132"]; // Delivered, Due, Assigned, Open



class TTICSDashboard extends Component {
  static template = "TTICSDashboardMain";

  setup() {
    this.leftDonut = null;
    this.rightDonut = null;
    this.personCharts = {};

    this.state = useState({
      date_from: "",
      date_to: "",
      cs_personnel: [],
      selected_personnel: "0",
      can_edit_personnel: true,
      kpis: {
        outsourced: 0,
        regular: 0,
        express: 0,
        shuttle: 0,
        table_data: [],          // << table for the left donut
        report_summary: {},
        daily_table: [],
        person_cards: [],// raw counts for donut
      },
    });

    onMounted(async () => {
      await this.loadFilters();
      await this.fetchKPIs();
      await this.fetchReportStatus();
      await this.fetchDailySummary();
      await this.fetchRightStatus();
      await this.fetchParcelOverview();
      await this.fetchPersonGrid();

    });
  }

  async loadFilters() {
  try {
    const filters = await rpc("/tti_cs_dashboard/filters", {});
    this.state.date_from = filters.default_date_from;
    this.state.date_to = filters.default_date_to;
    this.state.cs_personnel = filters.cs_personnel || [];

    // backend-driven defaults
    this.state.selected_personnel = String(filters.default_user_id ?? 0);
    this.state.can_edit_personnel = !!filters.can_edit_personnel;

    // initial data load
    await this.onFilterChange();
  } catch (err) {
    console.error("Error loading CS Dashboard filters:", err);
  }
}


  async fetchKPIs() {
    if (!this.state.date_from || !this.state.date_to) return;

    const payload = {
      date_from: this.state.date_from,
      date_to: this.state.date_to,
      user_id: Number(this.state.selected_personnel || 0),
    };

    try {
      const res = await rpc("/tti_cs_dashboard/data", payload);
      Object.assign(this.state.kpis, {
        outsourced: res.outsourced ?? 0,
        regular:   res.regular   ?? 0,
        express:   res.express   ?? 0,
        shuttle:   res.shuttle   ?? 0,
      });
    } catch (err) {
      console.error("Error loading CS Dashboard data:", err);
    }
  }

  async fetchReportStatus() {
    if (!this.state.date_from || !this.state.date_to) return;

    const payload = {
      date_from: this.state.date_from,
      date_to: this.state.date_to,
      user_id: Number(this.state.selected_personnel || 0),
    };

    try {
      const res = await rpc("/tti_cs_dashboard/report_status", payload);

      // table_data matches the LEFT donut categories
      this.state.kpis.table_data = res.table_data || [];
      this.state.kpis.report_summary = res.summary || {};

      // draw/update the LEFT donut using the same data
      this.renderLeftDonut();
    } catch (err) {
      console.error("Error loading report status:", err);
    }
  }

  renderLeftDonut() {
  const canvas = document.getElementById("left_donut_chart");
  const s = this.state.kpis.report_summary || {};
  if (!canvas || typeof window.Chart === "undefined") return;

  const labels = ["Delivered Reports", "Late Reports", "Overdue Reports", "Pending Reports"];
  const data = [s.delivered||0, s.late||0, s.overdue||0, s.pending||0];
  const total = data.reduce((a,b)=>a+b, 0);

  // Destroy existing chart
  if (this.leftDonut) {
    this.leftDonut.destroy();
    this.leftDonut = null;
  }

  // --- Color mapping ---
  const colors = ["#156082", "#196b24", "#0f9ed5", "#e97132"];

  // --- Center total text ---
  const centerText = {
    id: "centerText",
    afterDraw(chart) {
      const { ctx, chartArea } = chart;
      const cx = (chartArea.left + chartArea.right) / 2;
      const cy = (chartArea.top + chartArea.bottom) / 2;
      ctx.save();
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.font = "700 28px sans-serif";
      ctx.fillText(String(total), cx, cy - 10);
      ctx.font = "400 14px sans-serif";
      ctx.fillText("Total Reports", cx, cy + 14);
      ctx.restore();
    }
  };

  // --- Labels on slices ---
  const sliceLabels = {
  id: "sliceLabels",
  afterDatasetsDraw(chart) {
    if (!total) return;
    const { ctx } = chart;
    const meta = chart.getDatasetMeta(0);
    ctx.save();
    ctx.font = "bold 12px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";

    meta.data.forEach((arc, i) => {
      const value = data[i];
      if (!value) return;
      const a = (arc.startAngle + arc.endAngle) / 2;
      const r = (arc.outerRadius + arc.innerRadius) / 2;
      const x = arc.x + Math.cos(a) * r * 1.02;
      const y = arc.y + Math.sin(a) * r * 1.02;
      const text = `${labels[i].replace(" Reports","")}, ${value}`;
      ctx.lineWidth = 4;
      ctx.strokeStyle = "#fff";
      ctx.strokeText(text, x, y);
      ctx.fillStyle = "#333";
      ctx.fillText(text, x, y);
    });

    ctx.restore();
  }
};


  // --- Create donut chart ---
  const ctx = canvas.getContext("2d");
  this.leftDonut = new window.Chart(ctx, {
    type: "doughnut",
    data: {
      labels,
      datasets: [
        {
          data,
          backgroundColor: colors, // 👈 custom color set
          borderWidth: 2,
          borderColor: "#fff",
        },
      ],
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
                  text: `${lbl}, ${ds.data[i] ?? 0}`,
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
      layout: {
    padding: { bottom: 24 },
  },

    },
    plugins: [centerText, sliceLabels],
  });
}



  async fetchDailySummary() {
    const payload = { user_id: Number(this.state.selected_personnel || 0) };
    try {
      const res = await rpc("/tti_cs_dashboard/daily_summary", payload);
      this.state.kpis.daily_table = res.rows || [];
    } catch (err) {
      console.error("Error loading daily summary:", err);
    }
  }

  async onFilterChange() {
  await this.fetchKPIs();
  await this.fetchReportStatus();
  await this.fetchDailySummary();
  await this.fetchRightStatus();
  await this.fetchParcelOverview();
  await this.fetchPersonGrid();
}

  async loadFilters() {
  try {
    const filters = await rpc("/tti_cs_dashboard/filters", {});
    this.state.date_from = filters.default_date_from;
    this.state.date_to = filters.default_date_to;
    this.state.cs_personnel = filters.cs_personnel || [];

    // backend-driven defaults
    this.state.selected_personnel = String(filters.default_user_id ?? 0);
    this.state.can_edit_personnel = !!filters.can_edit_personnel;

    // initial data load
    await this.onFilterChange();
  } catch (err) {
    console.error("Error loading CS Dashboard filters:", err);
  }
}


  async fetchRightStatus() {
  if (!this.state.date_from || !this.state.date_to) return;
  const payload = {
    date_from: this.state.date_from,
    date_to: this.state.date_to,
    user_id: Number(this.state.selected_personnel || 0),
  };
  try {
    const res = await rpc("/tti_cs_dashboard/right_status", payload);
    this.renderRightDonut(res.labels || [], res.data || []);
  } catch (err) {
    console.error("Error loading right donut:", err);
  }
}

  renderRightDonut(labels, data) {
  const canvas = document.getElementById("right_donut_chart");
  if (!canvas || typeof window.Chart === "undefined") return;

  if (this.rightDonut) {
    this.rightDonut.destroy();
  }

  // --- Custom color mapping (your defined order) ---
  // 1. Finalised Sale Orders → #156082
  // 2. Open Sale Orders → #E97132
  // 3. Sale Orders In Process → #196B24
  // 4. Cancelled Sale Orders → #0F9ED5
  const colors = ["#156082", "#E97132", "#196B24", "#0F9ED5"];

  // --- Labels on slices ---
  const sliceLabels = {
  id: "sliceLabelsRight",
  afterDatasetsDraw(chart) {
    const total = data.reduce((a, b) => a + b, 0);
    if (!total) return;

    const { ctx } = chart;
    const meta = chart.getDatasetMeta(0);
    ctx.save();
    ctx.font = "bold 12px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";

    meta.data.forEach((arc, i) => {
      const value = data[i];
      if (!value) return;

      // --- pretty label mapping ---
      const raw = labels[i] || "";
      let pretty = raw;
      const low = raw.toLowerCase();
      if (low.includes("cancelled"))        pretty = "Cancelled";
      else if (low.includes("in process"))  pretty = "In Process";
      else if (low.includes("finalised"))   pretty = "Finalised";
      else if (low.includes("open"))        pretty = "Open";

      const a = (arc.startAngle + arc.endAngle) / 2;
      const r = (arc.outerRadius + arc.innerRadius) / 2;
      const x = arc.x + Math.cos(a) * r * 1.02;
      const y = arc.y + Math.sin(a) * r * 1.02;

      const text = `${pretty}, ${value}`;
      ctx.lineWidth = 4;
      ctx.strokeStyle = "#fff";
      ctx.strokeText(text, x, y);
      ctx.fillStyle = "#333";
      ctx.fillText(text, x, y);
    });

    ctx.restore();
  }
};



  // --- Create donut chart ---
  const ctx = canvas.getContext("2d");
  this.rightDonut = new window.Chart(ctx, {
    type: "doughnut",
    data: {
      labels,
      datasets: [
        {
          data,
          backgroundColor: colors,
          borderWidth: 2,
          borderColor: "#fff",
        },
      ],
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
        return labels.map((raw, i) => {
          let pretty = raw || "";
          const low = raw.toLowerCase();
          if (low.includes("cancelled")) pretty = "Cancelled";
          else if (low.includes("in process")) pretty = "In Process";
          else if (low.includes("finalised")) pretty = "Finalised";
          else if (low.includes("open")) pretty = "Open";

          return {
            text: `${pretty}, ${ds.data[i] ?? 0}`,
            fillStyle: Array.isArray(ds.backgroundColor) ? ds.backgroundColor[i] : ds.backgroundColor,
            strokeStyle: "#fff",
            lineWidth: 2,
            hidden: meta.data[i] ? meta.data[i].hidden : false,
            index: i,
            datasetIndex: 0,
          };
        });
      },
    },
  },
  tooltip: { enabled: false },
},
      layout: {
            padding: { bottom: 24 },
          },
    },
    plugins: [sliceLabels],
  });
}

    async fetchParcelOverview() {
      const payload = {
        date_from: this.state.date_from,
        date_to: this.state.date_to,
        user_id: Number(this.state.selected_personnel || 0),
      };
      try {
        const res = await rpc("/tti_cs_dashboard/parcel_overview", payload);
        this.renderParcelBarChart(res.labels || [], res.datasets || []);
      } catch (err) {
        console.error("Error loading parcel overview:", err);
      }
    }
    renderParcelBarChart(labels, datasets) {
  const canvas = document.getElementById("middle_bar_chart");
  if (!canvas || typeof window.Chart === "undefined") return;

  if (this.parcelBar) {
    this.parcelBar.destroy();
    this.parcelBar = null;
  }

  // Colors (consistent with theme)
  const colors = ["#156082", "#E97132", "#196B24"];
  datasets.forEach((ds, i) => ds.backgroundColor = colors[i]);

  // --- Labels above bars ---
  const valueLabels = {
    id: "valueLabels",
    afterDatasetsDraw(chart) {
      const { ctx } = chart;
      ctx.save();
      ctx.font = "bold 12px sans-serif";
      ctx.textAlign = "right";
      ctx.textBaseline = "middle";

      chart.data.datasets.forEach((dataset, i) => {
        const meta = chart.getDatasetMeta(i);
        meta.data.forEach((bar, index) => {
          const val = dataset.data[index];
          if (val !== 0 && val !== null && val !== undefined) {
            const { x, y } = bar.tooltipPosition();
            ctx.fillStyle = "#fff";
            ctx.fillText(val, x - 6, y);
          }
        });
      });

      ctx.restore();
    },
  };

  // --- Create bar chart ---
  const ctx = canvas.getContext("2d");
  this.parcelBar = new window.Chart(ctx, {
    type: "bar",
    data: { labels, datasets },
    options: {
      indexAxis: "y", // horizontal bars
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            boxWidth: 10,
            boxHeight: 10,
            padding: 12,
            generateLabels(chart) {
              const dsList = chart.data.datasets || [];
              return dsList.map((ds, i) => {
                // Sum dataset values for legend display
                const total = (ds.data || []).reduce((a, b) => a + (b || 0), 0);
                const label = ds.label || `Dataset ${i + 1}`;
                return {
                  text: `${label}, ${total}`,
                  fillStyle: Array.isArray(ds.backgroundColor)
                    ? ds.backgroundColor[0]
                    : ds.backgroundColor,
                  strokeStyle: "#fff",
                  lineWidth: 2,
                  hidden: chart.isDatasetVisible(i) === false,
                  datasetIndex: i,
                };
              });
            },
          },
        },
        tooltip: { enabled: true },
      },
      scales: {
        x: { stacked: true, beginAtZero: true },
        y: { stacked: true },
      },
    },
    plugins: [valueLabels],
  });
}


//  renderParcelBarChart(labels, datasets) {
//  const canvas = document.getElementById("middle_bar_chart");
//  if (!canvas || typeof window.Chart === "undefined") return;
//
//  if (this.parcelBar) {
//    this.parcelBar.destroy();
//    this.parcelBar = null;
//  }
//
//  // Colors (consistent with theme)
//  const colors = ["#156082", "#E97132", "#196B24"];
//  datasets.forEach((ds, i) => ds.backgroundColor = colors[i]);
//
//  const valueLabels = {
//    id: "valueLabels",
//    afterDatasetsDraw(chart) {
//      const { ctx } = chart;
//      ctx.save();
//      ctx.font = "bold 12px sans-serif";
//      ctx.fillStyle = "#333";
//      ctx.textAlign = "left";
//      ctx.textBaseline = "middle";
//
//      chart.data.datasets.forEach((dataset, i) => {
//        const meta = chart.getDatasetMeta(i);
//        meta.data.forEach((bar, index) => {
//          const val = dataset.data[index];
//          if (val !== 0 && val !== null && val !== undefined) {
//            const { x, y } = bar.tooltipPosition();
//            ctx.fillStyle = "#fff";
//            ctx.textAlign = "right";
//            ctx.fillText(val, x - 6, y);
//          }
//        });
//      });
//
//      ctx.restore();
//    },
//  };
//
//  const ctx = canvas.getContext("2d");
//  this.parcelBar = new window.Chart(ctx, {
//    type: "bar",
//    data: { labels, datasets },
//    options: {
//      indexAxis: "y", // horizontal bar
//      responsive: true,
//      maintainAspectRatio: false,
//      plugins: {
//      legend: {
//        position: "bottom",
//        labels: {
//          boxWidth: 10,   // smaller color chip
//          boxHeight: 10,
//          padding: 12,
//        },
//      },
//      tooltip: { enabled: true },
//    },
//
//      scales: {
//        x: { stacked: true, beginAtZero: true },
//        y: { stacked: true },
//      },
//    },
//    plugins: [valueLabels],
//  });
//}

  async fetchPersonGrid() {
  if (!this.state.date_from || !this.state.date_to) return;
  const payload = {
    date_from: this.state.date_from,
    date_to: this.state.date_to,
    user_id: Number(this.state.selected_personnel || 0), // 0 = all, otherwise one
  };
  try {
    const res = await rpc("/tti_cs_dashboard/person_grid", payload);
    this.state.kpis.person_cards = res.people || [];
    // defer drawing until DOM updates
    setTimeout(() => this.renderPersonDonuts(), 0);
  } catch (e) {
    console.error("Error loading person grid:", e);
  }
}

  renderPersonDonuts() {
  if (typeof window.Chart === "undefined") return;
  // destroy old charts
  const charts = this.personCharts || {};
  Object.values(this.personCharts).forEach(ch => { try { ch.destroy(); } catch(_){} });
  this.personCharts = {};

  this.state.kpis.person_cards.forEach(p => {
    const cid = `sp_donut_${p.user_id}`;
    const canvas = document.getElementById(cid);
    if (!canvas) return;
    const labels = ["Report Delivered", "Reports Due", "Parcel Assigned", "Open Parcels"];
    const data = [p.delivered||0, p.due||0, p.assigned||0, p.open||0];

    const sliceLabels = {
  id: `sliceLabels_${p.user_id}`,
  afterDatasetsDraw(chart) {
    const total = data.reduce((a,b)=>a+b,0);
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
      const a = (arc.startAngle + arc.endAngle)/2;
      const r = (arc.outerRadius + arc.innerRadius)/2;
      const x = arc.x + Math.cos(a)*r*1.02;
      const y = arc.y + Math.sin(a)*r*1.02;
      const txt = `${labels[i]}, ${val}`;
      ctx.lineWidth = 4;
      ctx.strokeStyle = "#fff";
      ctx.strokeText(txt, x, y);
      ctx.fillStyle = "#333";
      ctx.fillText(txt, x, y);
    });

    ctx.restore();
  }
};


    const ctx = canvas.getContext("2d");
    this.personCharts[p.user_id] = new window.Chart(ctx, {
      type: "doughnut",
      data: {
        labels,
        datasets: [{ data, backgroundColor: PERSON_COLORS, borderWidth: 2, borderColor: "#fff" }],
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
            padding: 10,
            generateLabels(chart) {
              const ds = chart.data.datasets[0] || { data: [], backgroundColor: [] };
              const labels = chart.data.labels || [];
              const meta = chart.getDatasetMeta(0);
              return labels.map((lbl, i) => ({
                text: `${lbl}, ${ds.data[i] ?? 0}`,
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
      plugins: [sliceLabels],
    });
  });
}



}

registry.category("actions").add("tti_cs_dashboard_action", TTICSDashboard);
export default TTICSDashboard;
