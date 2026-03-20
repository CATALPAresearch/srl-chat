<template>
  <div class="researcher-dashboard">
    <h2 class="dashboard-title">Researcher Dashboard</h2>

    <div v-if="isLoading" class="dashboard-loading">
      <p>Loading analytics...</p>
    </div>

    <div v-else-if="error" class="alert alert-danger">{{ error }}</div>

    <div v-else>
      <!-- KPI Cards Row 1 -->
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-value">{{ stats.total_students }}</div>
          <div class="kpi-label">Total Students</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-value">{{ stats.total_completed }}</div>
          <div class="kpi-label">Completed Interviews</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-value">{{ stats.avg_duration_minutes }} min</div>
          <div class="kpi-label">Avg Interview Duration</div>
          <div class="kpi-sub">σ {{ stats.std_duration_minutes }} min &nbsp;|&nbsp; var {{ stats.var_duration_minutes }}</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-value">{{ stats.avg_response_time_seconds }}s</div>
          <div class="kpi-label">Avg LLM Response Time</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-value">{{ stats.survey_count }}</div>
          <div class="kpi-label">Survey Responses</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-value">{{ stats.reattempts }}</div>
          <div class="kpi-label">Students who Re-attempted</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-value">{{ stats.avg_turns_completed }}</div>
          <div class="kpi-label">Avg Turns (Completed)</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-value">{{ stats.avg_turns_incomplete }}</div>
          <div class="kpi-label">Avg Turns (Incomplete)</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-value">{{ stats.avg_messages_per_interview }}</div>
          <div class="kpi-label">Avg Messages per Interview</div>
        </div>
      </div>

      <!-- Charts Row -->
      <div class="charts-grid">
        <!-- Drop-off analysis -->
        <div class="chart-card">
          <h4>Drop-off by Interview Step</h4>
          <p class="chart-desc">At which step do students leave the interview</p>
          <canvas ref="dropoffChart"></canvas>
        </div>

        <!-- Strategy Distribution -->
        <div class="chart-card">
          <h4>Learning Strategy Distribution</h4>
          <p class="chart-desc">Strategies identified via RAG detection</p>
          <canvas ref="strategyChart"></canvas>
        </div>

        <!-- Language Distribution -->
        <div class="chart-card">
          <h4>Language Distribution</h4>
          <canvas ref="languageChart"></canvas>
        </div>

        <!-- Turns comparison -->
        <div class="chart-card">
          <h4>Avg Turns: Completed vs Incomplete</h4>
          <canvas ref="turnsChart"></canvas>
        </div>
      </div>

      <!-- Raw Data Tables -->
      <div class="table-section">
        <h4>Drop-off Details</h4>
        <table class="data-table">
          <thead>
            <tr><th>Interview Step</th><th>Students who left</th></tr>
          </thead>
          <tbody>
            <tr v-if="!stats.dropoff_distribution || !stats.dropoff_distribution.length">
              <td colspan="2">No data yet</td>
            </tr>
            <tr v-for="row in stats.dropoff_distribution" :key="row.step">
              <td>{{ row.step }}</td>
              <td>{{ row.count }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="table-section">
        <h4>Top Learning Strategies Detected</h4>
        <table class="data-table">
          <thead>
            <tr><th>Strategy</th><th>Count</th></tr>
          </thead>
          <tbody>
            <tr v-if="!stats.strategy_distribution || !stats.strategy_distribution.length">
              <td colspan="2">No data yet</td>
            </tr>
            <tr v-for="row in stats.strategy_distribution" :key="row.strategy">
              <td>{{ row.strategy }}</td>
              <td>{{ row.count }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Self-Report Survey -->
      <div class="chart-card" style="margin-bottom: 24px;">
        <h4>Self-Report Survey Results</h4>
        <p v-if="!stats.survey_count" style="color: #6c757d;">No survey responses yet.</p>
        <p v-else>{{ stats.survey_count }} survey responses collected.</p>
      </div>

      <!-- Downloads -->
      <div class="download-section">
        <button class="btn btn-success mr-2" @click="downloadCSV">Download CSV</button>
        <button class="btn btn-primary" @click="downloadExcel">Download Excel</button>
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
      charts: { dropoff: null, strategy: null, language: null, turns: null },
    };
  },
  async mounted() {
    await this.loadStats();
  },
  methods: {
    async loadStats() {
      try {
        const base = window.SRL_BACKEND_URL || "";
        const res = await axios.get(`${base}/dashboard/stats`);
        this.stats = res.data;
        setTimeout(() => this.renderCharts(), 100);
      } catch (e) {
        this.error = "Failed to load dashboard data: " + e.message;
      } finally {
        this.isLoading = false;
      }
    },
    renderCharts() {
      this.destroyCharts();

      // Drop-off chart
      const dCtx = this.$refs.dropoffChart;
      if (dCtx && this.stats.dropoff_distribution && this.stats.dropoff_distribution.length) {
        this.charts.dropoff = new Chart(dCtx, {
          type: "bar",
          data: {
            labels: this.stats.dropoff_distribution.map(s => s.step),
            datasets: [{
              label: "Students who dropped off",
              data: this.stats.dropoff_distribution.map(s => s.count),
              backgroundColor: "rgba(220, 53, 69, 0.6)",
            }],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: { yAxes: [{ ticks: { beginAtZero: true } }] },
          },
        });
      }

      // Strategy chart
      const sCtx = this.$refs.strategyChart;
      if (sCtx && this.stats.strategy_distribution && this.stats.strategy_distribution.length) {
        this.charts.strategy = new Chart(sCtx, {
          type: "bar",
          data: {
            labels: this.stats.strategy_distribution.map(s => s.strategy),
            datasets: [{
              label: "Count",
              data: this.stats.strategy_distribution.map(s => s.count),
              backgroundColor: "rgba(0, 123, 255, 0.6)",
            }],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: { yAxes: [{ ticks: { beginAtZero: true } }] },
          },
        });
      }

      // Language chart
      const lCtx = this.$refs.languageChart;
      if (lCtx && this.stats.language_distribution && this.stats.language_distribution.length) {
        this.charts.language = new Chart(lCtx, {
          type: "doughnut",
          data: {
            labels: this.stats.language_distribution.map(l => l.language),
            datasets: [{
              data: this.stats.language_distribution.map(l => l.count),
              backgroundColor: ["#007bff", "#28a745", "#ffc107", "#dc3545"],
            }],
          },
          options: { responsive: true, maintainAspectRatio: false },
        });
      }

      // Turns comparison chart
      const tCtx = this.$refs.turnsChart;
      if (tCtx) {
        this.charts.turns = new Chart(tCtx, {
          type: "bar",
          data: {
            labels: ["Completed", "Incomplete"],
            datasets: [{
              label: "Avg Turns",
              data: [this.stats.avg_turns_completed, this.stats.avg_turns_incomplete],
              backgroundColor: ["rgba(40, 167, 69, 0.6)", "rgba(220, 53, 69, 0.6)"],
            }],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: { yAxes: [{ ticks: { beginAtZero: true } }] },
          },
        });
      }
    },
    destroyCharts() {
      Object.values(this.charts).forEach(c => { if (c) c.destroy(); });
      this.charts = { dropoff: null, strategy: null, language: null, turns: null };
    },
    downloadCSV() {
      const rows = [
        ["Metric", "Value"],
        ["Total Students", this.stats.total_students],
        ["Completed Interviews", this.stats.total_completed],
        ["Avg Duration (min)", this.stats.avg_duration_minutes],
        ["Std Deviation Duration (min)", this.stats.std_duration_minutes],
        ["Variance Duration", this.stats.var_duration_minutes],
        ["Avg LLM Response Time (s)", this.stats.avg_response_time_seconds],
        ["Survey Responses", this.stats.survey_count],
        ["Students who Re-attempted", this.stats.reattempts],
        ["Avg Turns (Completed)", this.stats.avg_turns_completed],
        ["Avg Turns (Incomplete)", this.stats.avg_turns_incomplete],
        ["Avg Messages per Interview", this.stats.avg_messages_per_interview],
        [],
        ["Drop-off Step", "Count"],
        ...(this.stats.dropoff_distribution || []).map(s => [s.step, s.count]),
        [],
        ["Strategy", "Count"],
        ...(this.stats.strategy_distribution || []).map(s => [s.strategy, s.count]),
        [],
        ["Language", "Count"],
        ...(this.stats.language_distribution || []).map(l => [l.language, l.count]),
      ];
      const csv = rows.map(r => r.join(",")).join("\n");
      const blob = new Blob([csv], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "srl_dashboard.csv";
      a.click();
      URL.revokeObjectURL(url);
    },
    downloadExcel() {
      let html = "<html><head><meta charset='UTF-8'></head><body>";
      html += "<table border='1'><tr><th>Metric</th><th>Value</th></tr>";
      html += `<tr><td>Total Students</td><td>${this.stats.total_students}</td></tr>`;
      html += `<tr><td>Completed Interviews</td><td>${this.stats.total_completed}</td></tr>`;
      html += `<tr><td>Avg Duration (min)</td><td>${this.stats.avg_duration_minutes}</td></tr>`;
      html += `<tr><td>Std Deviation (min)</td><td>${this.stats.std_duration_minutes}</td></tr>`;
      html += `<tr><td>Variance</td><td>${this.stats.var_duration_minutes}</td></tr>`;
      html += `<tr><td>Avg LLM Response Time (s)</td><td>${this.stats.avg_response_time_seconds}</td></tr>`;
      html += `<tr><td>Survey Responses</td><td>${this.stats.survey_count}</td></tr>`;
      html += `<tr><td>Re-attempts</td><td>${this.stats.reattempts}</td></tr>`;
      html += `<tr><td>Avg Turns Completed</td><td>${this.stats.avg_turns_completed}</td></tr>`;
      html += `<tr><td>Avg Turns Incomplete</td><td>${this.stats.avg_turns_incomplete}</td></tr>`;
      html += `<tr><td>Avg Messages</td><td>${this.stats.avg_messages_per_interview}</td></tr>`;
      html += "</table><br>";
      html += "<table border='1'><tr><th>Drop-off Step</th><th>Count</th></tr>";
      (this.stats.dropoff_distribution || []).forEach(s => {
        html += `<tr><td>${s.step}</td><td>${s.count}</td></tr>`;
      });
      html += "</table><br>";
      html += "<table border='1'><tr><th>Strategy</th><th>Count</th></tr>";
      (this.stats.strategy_distribution || []).forEach(s => {
        html += `<tr><td>${s.strategy}</td><td>${s.count}</td></tr>`;
      });
      html += "</table></body></html>";
      const blob = new Blob([html], { type: "application/vnd.ms-excel;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "srl_dashboard.xls";
      a.click();
      URL.revokeObjectURL(url);
    },
    beforeUnmount() {
      this.destroyCharts();
    },
  },
};
</script>

<style scoped>
.researcher-dashboard { padding: 20px; overflow-y: auto; }
.dashboard-title { margin-bottom: 24px; font-size: 1.5rem; }
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 16px;
  margin-bottom: 32px;
}
.kpi-card {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}
.kpi-value { font-size: 2rem; font-weight: bold; color: #007bff; }
.kpi-label { font-size: 0.85rem; color: #6c757d; margin-top: 4px; }
.kpi-sub { font-size: 0.75rem; color: #999; margin-top: 4px; }
.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 32px;
}
.chart-card {
  background: #fafafa;
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 16px;
  min-height: 300px;
  position: relative;
}
.chart-card h4 { margin-bottom: 4px; font-size: 1rem; }
.chart-desc { font-size: 0.8rem; color: #999; margin-bottom: 12px; }
.chart-card canvas { height: 250px !important; width: 100% !important; display: block; }
.table-section { margin-bottom: 24px; }
.table-section h4 { margin-bottom: 8px; }
.data-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
.data-table th, .data-table td { border: 1px solid #dee2e6; padding: 8px 12px; text-align: left; }
.data-table th { background: #f8f9fa; font-weight: 600; }
.data-table tr:nth-child(even) { background: #f8f9fa; }
.download-section { text-align: right; margin-bottom: 32px; }
</style>