<template>
  <div class="rd-root">
    <!-- Header -->
    <div class="rd-header">
      <div class="rd-header-left">
        <span class="rd-badge">RESEARCH</span>
        <h1 class="rd-title">Analytics Dashboard</h1>
      </div>
      <div class="rd-header-right">
        <div class="rd-filter-group">
          <div class="rd-date-field">
            <label>FROM</label>
            <input type="date" v-model="dateFrom" />
          </div>
          <div class="rd-date-field">
            <label>TO</label>
            <input type="date" v-model="dateTo" />
          </div>
          <button class="rd-btn rd-btn-primary" @click="loadStats">Apply</button>
          <button class="rd-btn rd-btn-ghost" @click="clearFilter">Clear</button>
          <button class="rd-btn rd-btn-ghost" @click="loadStats">↻</button>
        </div>
        <div class="rd-download-group">
          <button class="rd-btn rd-btn-outline" @click="downloadCSV">CSV</button>
          <button class="rd-btn rd-btn-outline" @click="downloadExcel">Excel</button>
          <button class="rd-btn rd-btn-danger" @click="downloadPDF">PDF</button>
        </div>
      </div>
    </div>

    <div v-if="isLoading" class="rd-loading">
      <div class="rd-spinner"></div>
      <p>Loading analytics…</p>
    </div>
    <div v-else-if="error" class="rd-error">{{ error }}</div>

    <div v-else id="dashboard-content">

      <!-- KPI Grid -->
      <div class="rd-kpi-grid">
        <div class="rd-kpi" v-for="kpi in kpiCards" :key="kpi.label" :style="`--accent: ${kpi.color}`">
          <div class="rd-kpi-value">{{ kpi.value }}</div>
          <div class="rd-kpi-label">{{ kpi.label }}</div>
          <div class="rd-kpi-sub" v-if="kpi.sub">{{ kpi.sub }}</div>
          <div class="rd-kpi-bar"></div>
        </div>
      </div>

      <!-- Charts Row 1 -->
      <div class="rd-charts-row">
        <div class="rd-chart-card rd-chart-wide">
          <div class="rd-chart-header">
            <span class="rd-chart-title">Drop-off by Interview Step</span>
            <span class="rd-chart-sub">where students leave</span>
          </div>
          <div class="rd-canvas-wrap">
            <canvas ref="dropoffChart"></canvas>
            <div v-if="!stats.dropoff_distribution || !stats.dropoff_distribution.length" class="rd-empty">No data yet</div>
          </div>
        </div>
        <div class="rd-chart-card rd-chart-narrow">
          <div class="rd-chart-header">
            <span class="rd-chart-title">Language Split</span>
            <span class="rd-chart-sub">DE vs EN</span>
          </div>
          <div class="rd-canvas-wrap">
            <canvas ref="languageChart"></canvas>
            <div v-if="!stats.language_distribution || !stats.language_distribution.length" class="rd-empty">No data yet</div>
          </div>
        </div>
      </div>

      <!-- Charts Row 2 -->
      <div class="rd-charts-row">
        <div class="rd-chart-card rd-chart-narrow">
          <div class="rd-chart-header">
            <span class="rd-chart-title">Completion Funnel</span>
            <span class="rd-chart-sub">students per step</span>
          </div>
          <div class="rd-canvas-wrap">
            <canvas ref="funnelChart"></canvas>
            <div v-if="!stats.completion_funnel || !stats.completion_funnel.length" class="rd-empty">No data yet</div>
          </div>
        </div>
        <div class="rd-chart-card rd-chart-narrow">
          <div class="rd-chart-header">
            <span class="rd-chart-title">Avg Turns</span>
            <span class="rd-chart-sub">completed vs incomplete</span>
          </div>
          <div class="rd-canvas-wrap">
            <canvas ref="turnsChart"></canvas>
          </div>
        </div>
        <div class="rd-chart-card rd-chart-narrow">
          <div class="rd-chart-header">
            <span class="rd-chart-title">LLM Response Time</span>
            <span class="rd-chart-sub">seconds by step</span>
          </div>
          <div class="rd-canvas-wrap">
            <canvas ref="responseTimeChart"></canvas>
            <div v-if="!stats.response_time_by_step || !stats.response_time_by_step.length" class="rd-empty">No data yet</div>
          </div>
        </div>
      </div>

      <!-- Charts Row 3 -->
      <div class="rd-charts-row">
        <div class="rd-chart-card rd-chart-wide">
          <div class="rd-chart-header">
            <span class="rd-chart-title">Weekly Activity</span>
            <span class="rd-chart-sub">messages &amp; unique users per week</span>
          </div>
          <div class="rd-canvas-wrap">
            <canvas ref="weeklyChart"></canvas>
            <div v-if="!stats.weekly_activity || !stats.weekly_activity.length" class="rd-empty">No data yet</div>
          </div>
        </div>
        <div class="rd-chart-card rd-chart-narrow">
          <div class="rd-chart-header">
            <span class="rd-chart-title">Strategy Distribution</span>
            <span class="rd-chart-sub">RAG detected</span>
          </div>
          <div class="rd-canvas-wrap">
            <canvas ref="strategyChart"></canvas>
            <div v-if="!stats.strategy_distribution || !stats.strategy_distribution.length" class="rd-empty">No data yet</div>
          </div>
        </div>
      </div>

      <!-- Tables Row -->
      <div class="rd-tables-row">
        <div class="rd-table-card">
          <div class="rd-table-title">Drop-off Details</div>
          <table class="rd-table">
            <thead><tr><th>Step</th><th>Students</th></tr></thead>
            <tbody>
              <tr v-if="!stats.dropoff_distribution || !stats.dropoff_distribution.length"><td colspan="2" class="rd-empty-row">No data yet</td></tr>
              <tr v-for="r in stats.dropoff_distribution" :key="r.step"><td>{{ r.step }}</td><td>{{ r.count }}</td></tr>
            </tbody>
          </table>
        </div>
        <div class="rd-table-card">
          <div class="rd-table-title">Completion Funnel</div>
          <table class="rd-table">
            <thead><tr><th>Step</th><th>Reached</th></tr></thead>
            <tbody>
              <tr v-if="!stats.completion_funnel || !stats.completion_funnel.length"><td colspan="2" class="rd-empty-row">No data yet</td></tr>
              <tr v-for="r in stats.completion_funnel" :key="r.step"><td>{{ r.step }}</td><td>{{ r.count }}</td></tr>
            </tbody>
          </table>
        </div>
        <div class="rd-table-card">
          <div class="rd-table-title">Top Strategies</div>
          <table class="rd-table">
            <thead><tr><th>Strategy</th><th>Count</th></tr></thead>
            <tbody>
              <tr v-if="!stats.strategy_distribution || !stats.strategy_distribution.length"><td colspan="2" class="rd-empty-row">No data yet</td></tr>
              <tr v-for="r in stats.strategy_distribution" :key="r.strategy"><td>{{ r.strategy }}</td><td>{{ r.count }}</td></tr>
            </tbody>
          </table>
        </div>
        <div class="rd-table-card">
          <div class="rd-table-title">Weekly Activity</div>
          <table class="rd-table">
            <thead><tr><th>Week</th><th>Msgs</th><th>Users</th></tr></thead>
            <tbody>
              <tr v-if="!stats.weekly_activity || !stats.weekly_activity.length"><td colspan="3" class="rd-empty-row">No data yet</td></tr>
              <tr v-for="r in stats.weekly_activity" :key="r.week"><td>{{ r.week }}</td><td>{{ r.messages }}</td><td>{{ r.users }}</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Survey -->
      <div class="rd-survey-card">
        <div class="rd-table-title">Self-Report Survey Results
          <span class="rd-badge-sm">{{ stats.survey_count }} responses</span>
        </div>
        <p v-if="!stats.survey_count" style="color:#d1d5db; font-size:0.82rem;">No survey responses yet.</p>
        <table v-else-if="stats.survey_avg_scores && stats.survey_avg_scores.length" class="rd-table">
          <thead><tr><th>Question</th><th>Avg Score</th></tr></thead>
          <tbody>
            <tr v-for="r in stats.survey_avg_scores" :key="r.question"><td>{{ r.question }}</td><td>{{ r.avg }}</td></tr>
          </tbody>
        </table>
      </div>

    </div>
  </div>
</template>

<script>
import axios from "axios";
import Chart from "chart.js";

export default {
  name: "ResearcherDashboard",
  data() {
    return {
      isLoading: true,
      error: null,
      stats: {},
      dateFrom: "",
      dateTo: "",
      charts: { dropoff: null, strategy: null, language: null, turns: null, funnel: null, weekly: null, responseTime: null },
    };
  },
  computed: {
    kpiCards() {
      return [
        { label: "Total Students", value: this.stats.total_students, color: "#3b82f6" },
        { label: "Completed Interviews", value: this.stats.total_completed, color: "#10b981" },
        { label: "Avg Duration", value: `${this.stats.avg_duration_minutes} min`, sub: `σ ${this.stats.std_duration_minutes} min · var ${this.stats.var_duration_minutes}`, color: "#8b5cf6" },
        { label: "Avg LLM Response", value: `${this.stats.avg_response_time_seconds}s`, color: "#f59e0b" },
        { label: "Survey Responses", value: this.stats.survey_count, color: "#06b6d4" },
        { label: "Re-attempts", value: this.stats.reattempts, color: "#ef4444" },
        { label: "Avg Turns (Done)", value: this.stats.avg_turns_completed, color: "#10b981" },
        { label: "Avg Turns (Drop)", value: this.stats.avg_turns_incomplete, color: "#f97316" },
        { label: "Avg Messages", value: this.stats.avg_messages_per_interview, color: "#6366f1" },
        { label: "Total Messages", value: this.stats.total_messages, color: "#14b8a6" },
      ];
    }
  },
  async mounted() { await this.loadStats(); },
  methods: {
    async loadStats() {
      this.isLoading = true;
      try {
        const base = window.SRL_BACKEND_URL || "";
        let url = `${base}/dashboard/stats`;
        const params = [];
        if (this.dateFrom) params.push(`date_from=${Math.floor(new Date(this.dateFrom).getTime()/1000)}`);
        if (this.dateTo) params.push(`date_to=${Math.floor(new Date(this.dateTo).getTime()/1000)}`);
        if (params.length) url += "?" + params.join("&");
        const res = await axios.get(url);
        this.stats = res.data;
        setTimeout(() => this.renderCharts(), 150);
      } catch(e) {
        this.error = "Failed to load: " + e.message;
      } finally {
        this.isLoading = false;
      }
    },
    clearFilter() { this.dateFrom = ""; this.dateTo = ""; this.loadStats(); },
    renderCharts() {
      this.destroyCharts();
      const opts = (extra) => ({ responsive: true, maintainAspectRatio: false, legend: { display: false }, ...extra });

      const dCtx = this.$refs.dropoffChart;
      if (dCtx && this.stats.dropoff_distribution && this.stats.dropoff_distribution.length) {
        this.charts.dropoff = new Chart(dCtx, { type: "bar", data: { labels: this.stats.dropoff_distribution.map(s=>s.step), datasets: [{ data: this.stats.dropoff_distribution.map(s=>s.count), backgroundColor: ["#ef4444","#f97316","#f59e0b","#10b981","#3b82f6"], borderRadius: 6 }] }, options: opts({ scales: { yAxes: [{ ticks: { beginAtZero: true } }], xAxes: [{ gridLines: { display: false } }] } }) });
      }

      const lCtx = this.$refs.languageChart;
      if (lCtx && this.stats.language_distribution && this.stats.language_distribution.length) {
        this.charts.language = new Chart(lCtx, { type: "doughnut", data: { labels: this.stats.language_distribution.map(l=>l.language), datasets: [{ data: this.stats.language_distribution.map(l=>l.count), backgroundColor: ["#3b82f6","#10b981","#f59e0b","#ef4444"], borderWidth: 3, borderColor: "#fff" }] }, options: { responsive: true, maintainAspectRatio: false, legend: { position: "bottom" } } });
      }

      const fCtx = this.$refs.funnelChart;
      if (fCtx && this.stats.completion_funnel && this.stats.completion_funnel.length) {
        this.charts.funnel = new Chart(fCtx, { type: "bar", data: { labels: this.stats.completion_funnel.map(f=>f.step), datasets: [{ data: this.stats.completion_funnel.map(f=>f.count), backgroundColor: "#06b6d4" }] }, options: opts({ scales: { yAxes: [{ ticks: { beginAtZero: true } }], xAxes: [{ gridLines: { display: false } }] } }) });
      }

      const tCtx = this.$refs.turnsChart;
      if (tCtx) {
        this.charts.turns = new Chart(tCtx, { type: "bar", data: { labels: ["Completed","Incomplete"], datasets: [{ data: [this.stats.avg_turns_completed, this.stats.avg_turns_incomplete], backgroundColor: ["#10b981","#ef4444"] }] }, options: opts({ scales: { yAxes: [{ ticks: { beginAtZero: true } }], xAxes: [{ gridLines: { display: false } }] } }) });
      }

      const rCtx = this.$refs.responseTimeChart;
      if (rCtx && this.stats.response_time_by_step && this.stats.response_time_by_step.length) {
        this.charts.responseTime = new Chart(rCtx, { type: "bar", data: { labels: this.stats.response_time_by_step.map(r=>r.step), datasets: [{ data: this.stats.response_time_by_step.map(r=>r.avg_seconds), backgroundColor: "#f59e0b" }] }, options: opts({ scales: { yAxes: [{ ticks: { beginAtZero: true } }], xAxes: [{ gridLines: { display: false } }] } }) });
      }

      const wCtx = this.$refs.weeklyChart;
      if (wCtx && this.stats.weekly_activity && this.stats.weekly_activity.length) {
        this.charts.weekly = new Chart(wCtx, { type: "line", data: { labels: this.stats.weekly_activity.map(w=>w.week), datasets: [{ label: "Messages", data: this.stats.weekly_activity.map(w=>w.messages), borderColor: "#3b82f6", backgroundColor: "rgba(59,130,246,0.08)", fill: true, tension: 0.4 }, { label: "Users", data: this.stats.weekly_activity.map(w=>w.users), borderColor: "#10b981", backgroundColor: "rgba(16,185,129,0.08)", fill: true, tension: 0.4 }] }, options: { responsive: true, maintainAspectRatio: false, legend: { position: "bottom" }, scales: { yAxes: [{ ticks: { beginAtZero: true } }] } } });
      }

      const sCtx = this.$refs.strategyChart;
      if (sCtx && this.stats.strategy_distribution && this.stats.strategy_distribution.length) {
        this.charts.strategy = new Chart(sCtx, { type: "horizontalBar", data: { labels: this.stats.strategy_distribution.map(s=>s.strategy), datasets: [{ data: this.stats.strategy_distribution.map(s=>s.count), backgroundColor: "#8b5cf6" }] }, options: opts({ scales: { xAxes: [{ ticks: { beginAtZero: true } }] } }) });
      }
    },
    destroyCharts() {
      Object.values(this.charts).forEach(c => { if (c) c.destroy(); });
      this.charts = { dropoff:null, strategy:null, language:null, turns:null, funnel:null, weekly:null, responseTime:null };
    },
    downloadCSV() {
      const rows = [
        ["Metric","Value"],
        ["Total Students",this.stats.total_students],
        ["Completed Interviews",this.stats.total_completed],
        ["Avg Duration (min)",this.stats.avg_duration_minutes],
        ["Std Deviation (min)",this.stats.std_duration_minutes],
        ["Variance",this.stats.var_duration_minutes],
        ["Avg LLM Response (s)",this.stats.avg_response_time_seconds],
        ["Survey Responses",this.stats.survey_count],
        ["Re-attempts",this.stats.reattempts],
        ["Avg Turns Completed",this.stats.avg_turns_completed],
        ["Avg Turns Incomplete",this.stats.avg_turns_incomplete],
        ["Avg Messages",this.stats.avg_messages_per_interview],
        ["Total Messages",this.stats.total_messages],
        [],["Drop-off Step","Count"],
        ...(this.stats.dropoff_distribution||[]).map(s=>[s.step,s.count]),
        [],["Strategy","Count"],
        ...(this.stats.strategy_distribution||[]).map(s=>[s.strategy,s.count]),
        [],["Funnel Step","Count"],
        ...(this.stats.completion_funnel||[]).map(f=>[f.step,f.count]),
      ];
      const csv = rows.map(r=>r.join(",")).join("\n");
      const a = document.createElement("a");
      a.href = URL.createObjectURL(new Blob([csv],{type:"text/csv"}));
      a.download = "srl_dashboard.csv"; a.click();
    },
    downloadExcel() {
      let html = "<html><head><meta charset='UTF-8'></head><body><table border='1'>";
      html += "<tr><th>Metric</th><th>Value</th></tr>";
      [["Total Students",this.stats.total_students],["Completed",this.stats.total_completed],["Avg Duration",this.stats.avg_duration_minutes],["Std Dev",this.stats.std_duration_minutes],["Variance",this.stats.var_duration_minutes],["Avg LLM Response",this.stats.avg_response_time_seconds],["Survey Responses",this.stats.survey_count],["Re-attempts",this.stats.reattempts],["Total Messages",this.stats.total_messages]].forEach(([k,v])=>{ html+=`<tr><td>${k}</td><td>${v}</td></tr>`; });
      html += "</table></body></html>";
      const a = document.createElement("a");
      a.href = URL.createObjectURL(new Blob([html],{type:"application/vnd.ms-excel;charset=utf-8"}));
      a.download = "srl_dashboard.xls"; a.click();
    },
    downloadPDF() { window.print(); },
    beforeUnmount() { this.destroyCharts(); },
  },
};
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

.rd-root {
  font-family: 'DM Sans', sans-serif;
  background: #f0f2f7;
  min-height: 100vh;
  padding: 24px 32px;
  color: #1a1d2e;
  overflow-y: auto;
}

/* Header */
.rd-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 28px;
  flex-wrap: wrap;
  gap: 16px;
}
.rd-header-left { display: flex; flex-direction: column; gap: 4px; }
.rd-badge {
  font-family: 'DM Mono', monospace;
  font-size: 0.65rem;
  font-weight: 500;
  letter-spacing: 0.15em;
  color: #6366f1;
  background: #eef2ff;
  padding: 3px 8px;
  border-radius: 4px;
  width: fit-content;
}
.rd-title { font-size: 1.75rem; font-weight: 600; margin: 0; letter-spacing: -0.02em; }
.rd-header-right { display: flex; flex-direction: column; gap: 8px; align-items: flex-end; }
.rd-filter-group, .rd-download-group { display: flex; align-items: center; gap: 8px; }
.rd-date-field { display: flex; flex-direction: column; gap: 2px; }
.rd-date-field label { font-size: 0.6rem; font-weight: 600; letter-spacing: 0.1em; color: #9ca3af; }
.rd-date-field input { border: 1px solid #e5e7eb; border-radius: 6px; padding: 5px 8px; font-size: 0.8rem; font-family: 'DM Sans', sans-serif; background: white; }

/* Buttons */
.rd-btn { font-family: 'DM Sans', sans-serif; font-size: 0.8rem; font-weight: 500; padding: 6px 14px; border-radius: 6px; border: none; cursor: pointer; transition: all 0.15s; }
.rd-btn-primary { background: #6366f1; color: white; }
.rd-btn-primary:hover { background: #4f46e5; }
.rd-btn-ghost { background: white; color: #374151; border: 1px solid #e5e7eb; }
.rd-btn-ghost:hover { background: #f9fafb; }
.rd-btn-outline { background: white; color: #374151; border: 1px solid #d1d5db; }
.rd-btn-outline:hover { background: #f3f4f6; }
.rd-btn-danger { background: #ef4444; color: white; }
.rd-btn-danger:hover { background: #dc2626; }

/* Loading */
.rd-loading { text-align: center; padding: 60px; color: #9ca3af; }
.rd-spinner { width: 36px; height: 36px; border: 3px solid #e5e7eb; border-top-color: #6366f1; border-radius: 50%; animation: spin 0.8s linear infinite; margin: 0 auto 16px; }
@keyframes spin { to { transform: rotate(360deg); } }
.rd-error { background: #fef2f2; border: 1px solid #fecaca; color: #dc2626; padding: 12px 16px; border-radius: 8px; margin-bottom: 20px; }

/* KPI Grid */
.rd-kpi-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  margin-bottom: 24px;
}
.rd-kpi {
  background: white;
  border-radius: 10px;
  padding: 16px 18px;
  position: relative;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.rd-kpi-bar {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 3px;
  background: var(--accent);
}
.rd-kpi-value {
  font-size: 1.6rem;
  font-weight: 600;
  color: var(--accent);
  line-height: 1;
  margin-bottom: 4px;
  font-family: 'DM Mono', monospace;
}
.rd-kpi-label { font-size: 0.75rem; color: #6b7280; font-weight: 500; }
.rd-kpi-sub { font-size: 0.68rem; color: #9ca3af; margin-top: 3px; }

/* Charts */
.rd-charts-row {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}
.rd-chart-card {
  background: white;
  border-radius: 10px;
  padding: 18px 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  display: flex;
  flex-direction: column;
}
.rd-chart-wide { flex: 2; }
.rd-chart-narrow { flex: 1; }
.rd-chart-header { margin-bottom: 12px; }
.rd-chart-title { font-size: 0.9rem; font-weight: 600; display: block; }
.rd-chart-sub { font-size: 0.72rem; color: #9ca3af; }
.rd-canvas-wrap { position: relative; height: 200px; }
.rd-canvas-wrap canvas { height: 200px !important; }
.rd-empty { position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); color: #d1d5db; font-size: 0.82rem; white-space: nowrap; }

/* Tables */
.rd-tables-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}
.rd-table-card {
  background: white;
  border-radius: 10px;
  padding: 16px 18px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.rd-table-title {
  font-size: 0.82rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.rd-badge-sm {
  font-size: 0.65rem;
  background: #f3f4f6;
  color: #6b7280;
  padding: 2px 7px;
  border-radius: 99px;
  font-weight: 500;
}
.rd-table { width: 100%; border-collapse: collapse; font-size: 0.78rem; }
.rd-table th { padding: 5px 8px; text-align: left; color: #9ca3af; font-weight: 600; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid #f3f4f6; }
.rd-table td { padding: 6px 8px; border-bottom: 1px solid #f9fafb; color: #374151; }
.rd-table tr:last-child td { border-bottom: none; }
.rd-empty-row { color: #d1d5db; text-align: center; padding: 12px; }

/* Survey */
.rd-survey-card {
  background: white;
  border-radius: 10px;
  padding: 18px 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  margin-bottom: 16px;
}

/* Print */
@media print {
  .rd-header-right { display: none; }
  .rd-root { background: white; padding: 16px; }
  .rd-chart-card, .rd-kpi, .rd-table-card { box-shadow: none; border: 1px solid #e5e7eb; }
}
</style>