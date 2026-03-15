<template>
  <div class="researcher-dashboard">
    <h2 class="dashboard-title">Researcher Dashboard</h2>

    <div v-if="isLoading" class="dashboard-loading">
      <p>Loading analytics...</p>
    </div>

    <div v-else-if="error" class="alert alert-danger">{{ error }}</div>

    <div v-else>
      <!-- KPI Cards -->
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-value">{{ stats.total_attempts }}</div>
          <div class="kpi-label">Interview Attempts</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-value">{{ stats.total_completed }}</div>
          <div class="kpi-label">Completed Interviews</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-value">{{ stats.completion_rate }}%</div>
          <div class="kpi-label">Completion Rate</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-value">{{ stats.total_students }}</div>
          <div class="kpi-label">Total Students</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-value">{{ stats.students_completed }}</div>
          <div class="kpi-label">Students Completed</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-value">{{ stats.avg_duration_minutes }} min</div>
          <div class="kpi-label">Avg Interview Duration</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-value">{{ stats.avg_response_time_seconds }}s</div>
          <div class="kpi-label">Avg LLM Response Time</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-value">{{ stats.survey_count }}</div>
          <div class="kpi-label">Survey Responses</div>
        </div>
      </div>

      <!-- Charts -->
      <div class="charts-grid">
        <!-- Completion Chart -->
        <div class="chart-card">
          <h4>Completed vs Attempted</h4>
          <canvas ref="completionChart"></canvas>
        </div>

        <!-- Strategy Distribution -->
        <div class="chart-card">
          <h4>Learning Strategy Distribution</h4>
          <canvas ref="strategyChart"></canvas>
        </div>
      </div>

<!-- Survey Results -->
      <div class="chart-card" style="margin-bottom: 24px;" v-if="stats.survey_count > 0">
        <h4>Self-Report Survey Results ({{ stats.survey_count }} responses)</h4>
        <canvas ref="surveyChart"></canvas>
      </div>
      <div class="chart-card" style="margin-bottom: 24px;" v-else>
        <h4>Self-Report Survey Results</h4>
        <p style="color: #6c757d;">No survey responses yet.</p>
      </div>

      <!-- Download -->
      <div class="download-section">
        <button class="btn btn-success mr-2" @click="downloadCSV">
          Download CSV
        </button>
        <button class="btn btn-primary" @click="downloadExcel">
          Download Excel
        </button>
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
      charts: { completion: null, strategy: null },
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
      if (!this.stats) return;

      // Completion donut
      const cCtx = this.$refs.completionChart;
      if (cCtx) {
        this.charts.completion = new Chart(cCtx, {
          type: "doughnut",
          data: {
            labels: ["Completed", "Not Completed"],
            datasets: [{
              data: [
                this.stats.total_completed,
                this.stats.total_attempts - this.stats.total_completed,
              ],
              backgroundColor: ["#28a745", "#dc3545"],
            }],
          },
          options: { responsive: true, maintainAspectRatio: false },
        });
      }

      // Strategy bar chart
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
    },
    destroyCharts() {
      Object.values(this.charts).forEach(c => { if (c) c.destroy(); });
      this.charts = { completion: null, strategy: null };
    },
    downloadExcel() {
      // Build HTML table that Excel can open natively
      let html = "<html><head><meta charset='UTF-8'></head><body>";
      html += "<table border='1'>";
      html += "<tr><th>Metric</th><th>Value</th></tr>";
      html += `<tr><td>Total Attempts</td><td>${this.stats.total_attempts}</td></tr>`;
      html += `<tr><td>Total Completed</td><td>${this.stats.total_completed}</td></tr>`;
      html += `<tr><td>Completion Rate (%)</td><td>${this.stats.completion_rate}</td></tr>`;
      html += `<tr><td>Total Students</td><td>${this.stats.total_students}</td></tr>`;
      html += `<tr><td>Students Completed</td><td>${this.stats.students_completed}</td></tr>`;
      html += `<tr><td>Avg Duration (min)</td><td>${this.stats.avg_duration_minutes}</td></tr>`;
      html += `<tr><td>Avg LLM Response Time (s)</td><td>${this.stats.avg_response_time_seconds}</td></tr>`;
      html += `<tr><td>Avg Turns (completed)</td><td>${this.stats.avg_turns_completed}</td></tr>`;
      html += `<tr><td>Survey Responses</td><td>${this.stats.survey_count}</td></tr>`;
      html += "</table><br>";
      html += "<table border='1'>";
      html += "<tr><th>Strategy</th><th>Count</th></tr>";
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
    downloadCSV() {
      const rows = [
        ["Metric", "Value"],
        ["Total Attempts", this.stats.total_attempts],
        ["Total Completed", this.stats.total_completed],
        ["Completion Rate (%)", this.stats.completion_rate],
        ["Total Students", this.stats.total_students],
        ["Students Completed", this.stats.students_completed],
        ["Avg Duration (min)", this.stats.avg_duration_minutes],
        ["Avg LLM Response Time (s)", this.stats.avg_response_time_seconds],
        ["Avg Turns (completed)", this.stats.avg_turns_completed],
        ["Survey Responses", this.stats.survey_count],
        [],
        ["Strategy", "Count"],
        ...(this.stats.strategy_distribution || []).map(s => [s.strategy, s.count]),
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
.chart-card h4 { margin-bottom: 12px; font-size: 1rem; }
.chart-card canvas {
  height: 250px !important;
  width: 100% !important;
  display: block;
}
.download-section { text-align: right; }
</style>