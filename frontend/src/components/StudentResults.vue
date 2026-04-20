<template>
  <div class="sr-root container-fluid py-4">
    <!-- Header -->
    <div class="row justify-content-center mb-4">
      <div class="col-md-10">
        <div class="card border-0 shadow-sm sr-hero">
          <div class="card-body p-4">
            <div class="d-flex align-items-center mb-1">
              <span class="badge badge-success mr-2">
                {{ lang === "de" ? "Abgeschlossen" : "Completed" }}
              </span>
              <h2 class="mb-0">
                {{ lang === "de" ? "Ihre Ergebnisse" : "Your Results" }}
              </h2>
            </div>
            <p class="text-muted mb-0">
              Thank you for taking the time to share how you learn with us!
              We've carefully analysed your answers, and your results are now
              shown in the two graphs below so you can explore them.
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="row justify-content-center">
      <div class="col-md-10">
        <div class="alert alert-danger">{{ error }}</div>
      </div>
    </div>

    <template v-else>
      <div class="row justify-content-center mb-4">
        <div class="col-md-10">
          <div class="card border-0 shadow-sm">
            <div class="card-body">
              <p>
                The spider chart shows the learning strategies you mentioned
                when describing how you study. Higher values mean that you
                reported using that strategy more often and more frequently. It
                is completely normal that the whole chart is not filled.
                Everyone learns in different ways, and no one uses all
                strategies equally. However, the chart may help you notice
                strategies that you use less often.
              </p>

              <div class="row mt-3">
                <!-- Radar chart -->
                <div class="col-md-7 mb-3">
                  <canvas ref="radarCanvas" style="max-width: 100%"></canvas>
                </div>
                <!-- Strategies not mentioned -->
                <div class="col-md-5 mb-3">
                  <h6 class="font-weight-600 mb-2">
                    Strategies not yet mentioned
                  </h6>
                  <p class="text-muted small mb-2">
                    These have been shown to be helpful — consider trying them:
                  </p>
                  <div
                    v-if="!unmentiondStrategies.length"
                    class="text-muted small"
                  >
                    Great — you mentioned all strategies!
                  </div>
                  <div v-else class="sr-tag-cloud">
                    <span
                      v-for="s in unmentiondStrategies"
                      :key="s.id"
                      class="sr-strategy-tag"
                      :data-tip="s.description"
                      >{{ s.name }}</span
                    >
                  </div>
                </div>
              </div>

              <p class="mt-2">
                On the right side of the chart, you will also see some
                strategies that were not mentioned in your answers. These
                strategies have been shown in educational research to be helpful
                for many students. You might want to explore whether some of
                them could work for you too.
              </p>
              <p>
                If you'd like to learn more about any of these strategies, get
                tips on how to use them, or if something in the graph isn't
                clear, feel free to send us a mail below.
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Motivation and Learning Beliefs section -->
      <div hidden class="row justify-content-center mb-4">
        <div class="col-md-10">
          <div class="card border-0 shadow-sm">
            <div class="card-header bg-white">
              <h5 class="mb-0 sr-section-title">
                Your Motivation and Learning Beliefs
              </h5>
            </div>
            <div class="card-body">
              <p>
                The second graph shows your beliefs about your motivation and
                learning skills.
              </p>
              <ul>
                <li>
                  <strong>How to read this graph:</strong> The blue line shows
                  your answers and the orange line shows the average results
                  from other students in a recent large scale study.
                </li>
              </ul>
              <p>
                This comparison can help you reflect on your learning habits and
                beliefs. There are no "good" or "bad" results here — it simply
                shows how your views compare with those of other students.
                However, higher scores are often correlated with better academic
                success.
              </p>

              <!-- Line chart placeholder -->
              <div
                class="sr-chart-placeholder d-flex align-items-center justify-content-center mb-3"
              >
                <span class="text-muted">[ Line Chart ]</span>
              </div>

              <p>
                If you have specific questions, or would like ideas on how to
                strengthen your motivation or improve certain learning skills
                presented here (like metacognition), please ask in the chat
                below. We are happy to share practical tips and helpful
                suggestions.
              </p>
              <p class="mb-0">
                We hope these results help you learn more about your own
                learning process and discover strategies that work best for you.
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Question textarea -->
      <div class="row justify-content-center mb-4">
        <div class="col-md-10">
          <div class="card border-0 shadow-sm">
            <div class="card-header bg-white">
              <h5 class="mb-0 sr-section-title">Ask a Question</h5>
              <p class="text-muted small mb-0">
                Is something unclear? Would you like tips on a specific
                strategy?
              </p>
            </div>
            <div class="card-body">
              <label for="sr-question" class="sr-only">Your question</label>
              <textarea
                id="sr-question"
                v-model="question"
                class="form-control mb-2"
                rows="3"
                placeholder="Type your question here…"
              />
              <button
                class="btn btn-primary"
                :disabled="!question.trim()"
                @click="submitQuestion"
              >
                Send
              </button>
              <div v-if="questionSent" class="text-success mt-2 small">
                Your question has been sent. You can follow the conversation in
                the chat.
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import Vue from "vue";
import axios from "axios";
import Chart from "chart.js";

export default Vue.extend({
  name: "StudentResults",

  data() {
    return {
      loading: true,
      error: null,
      data: {
        strategies: [],
        survey: null,
        interview_completed: false,
      },
      question: "",
      questionSent: false,
      radarChart: null,
    };
  },

  computed: {
    host() {
      return this.$store.getters.getApiHost;
    },
    lang() {
      return this.$store.getters.getLanguage || "de";
    },
    unmentiondStrategies() {
      if (!this.data.radar_data) return [];
      return this.data.radar_data.filter(
        (s) => !s.frequency || s.frequency === 0,
      );
    },
  },

  methods: {
    renderRadarChart() {
      const radarData = this.data.radar_data;
      if (!radarData || !radarData.length) return;
      const canvas = this.$refs.radarCanvas;
      if (!canvas) return;

      if (this.radarChart) {
        this.radarChart.destroy();
      }

      const truncate = (s, n) =>
        s.length > n ? s.slice(0, n - 1) + "\u2026" : s;
      const shortLabels = radarData.map((s) => truncate(s.name, 20));
      const fullLabels = radarData.map((s) => s.name);
      const descriptions = radarData.map((s) => s.description || "");
      const freqs = radarData.map((s) => s.frequency || 0);
      const avgs = radarData.map(
        (s) => Math.round((s.avg_frequency || 0) * 10) / 10,
      );
      const tickLabels = [
        "",
        "Seldom",
        "Sometimes",
        "Often",
        "Most of the time",
      ];
      const wrapText = (text, maxLen) => {
        const words = text.split(" ");
        const lines = [];
        let line = "";
        for (const w of words) {
          if ((line + " " + w).trim().length > maxLen) {
            if (line) lines.push(line);
            line = w;
          } else {
            line = (line + " " + w).trim();
          }
        }
        if (line) lines.push(line);
        return lines;
      };
      const freqLabel = (v) => {
        const i = Math.round(v);
        return tickLabels[i] ? tickLabels[i] + ` (${v})` : String(v);
      };

      this.radarChart = new Chart(canvas.getContext("2d"), {
        type: "radar",
        data: {
          labels: shortLabels,
          datasets: [
            {
              label: "You",
              data: freqs,
              backgroundColor: "rgba(54, 162, 235, 0.15)",
              borderColor: "rgba(54, 162, 235, 1)",
              pointBackgroundColor: "rgba(54, 162, 235, 1)",
              pointBorderColor: "#fff",
              borderWidth: 2,
              pointRadius: 4,
            },
            {
              label: "Course average",
              data: avgs,
              backgroundColor: "rgba(255, 153, 0, 0.12)",
              borderColor: "rgba(255, 153, 0, 0.85)",
              pointBackgroundColor: "rgba(255, 153, 0, 0.85)",
              pointBorderColor: "#fff",
              borderWidth: 2,
              borderDash: [5, 4],
              pointRadius: 3,
            },
          ],
        },
        options: {
          responsive: true,
          scale: {
            ticks: {
              beginAtZero: true,
              max: 4,
              min: 0,
              stepSize: 1,
              callback: () => "",
              backdropColor: "transparent",
            },
            pointLabels: { fontSize: 10 },
          },
          tooltips: {
            mode: "index",
            callbacks: {
              title: (items) => fullLabels[items[0].index],
              beforeBody: (items) => {
                const desc = descriptions[items[0].index];
                if (!desc) return [];
                return wrapText(desc, 48).map((l) => " " + l);
              },
              label: (item) => {
                const prefix = item.datasetIndex === 0 ? " You" : " Course avg";
                return prefix + ": " + freqLabel(parseFloat(item.value));
              },
            },
          },
          legend: { display: true, position: "bottom" },
        },
      });
    },

    barClass(val) {
      if (val >= 4) return "sr-bar-high";
      if (val >= 3) return "sr-bar-mid";
      return "sr-bar-low";
    },

    submitQuestion() {
      if (!this.question.trim()) return;
      this.$emit("question", this.question.trim());
      this.question = "";
      this.questionSent = true;
      setTimeout(() => (this.questionSent = false), 5000);
    },

    async loadResults() {
      this.loading = true;
      this.error = null;
      try {
        const res = await axios.get(`${this.host}/student/results`, {
          params: {
            userid: this.$store.getters.getUser,
            client: "standalone",
          },
        });
        this.data = res.data;
      } catch (e) {
        this.error =
          this.lang === "de"
            ? "Ergebnisse konnten nicht geladen werden."
            : "Failed to load results.";
      } finally {
        this.loading = false;
      }
      // Canvas is only in the DOM once loading is false, so render after.
      await this.$nextTick();
      this.renderRadarChart();
    },
  },

  mounted() {
    this.loadResults();
  },

  beforeDestroy() {
    if (this.radarChart) this.radarChart.destroy();
  },
});
</script>

<style scoped>
.sr-root {
  max-width: 960px;
  margin: 0 auto;
}

.sr-hero {
  background: linear-gradient(135deg, #e6f4ea 0%, #f8f9fa 100%);
}

.sr-kpi-value {
  font-size: 2rem;
  font-weight: 700;
}

.sr-kpi-label {
  font-size: 0.8rem;
  margin-top: 2px;
}

.sr-section-title {
  font-size: 1rem;
  font-weight: 600;
}

.font-weight-600 {
  font-weight: 600;
}

.sr-strategy-num {
  font-size: 1.2rem;
  min-width: 28px;
}

.sr-strategy-row {
  transition: background 0.15s;
}

.sr-strategy-row:hover {
  background: #f8f9fa;
}

/* Survey result bars */
.sr-survey-grid {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.sr-survey-item {
  display: grid;
  grid-template-columns: 90px 1fr 28px;
  align-items: center;
  gap: 8px;
  font-size: 0.82rem;
}

.sr-item-id {
  font-family: monospace;
  font-size: 0.75rem;
}

.sr-item-bar-wrap {
  background: #e9ecef;
  border-radius: 4px;
  height: 10px;
  overflow: hidden;
}

.sr-item-bar {
  height: 100%;
  border-radius: 4px;
  transition: width 0.4s ease;
}

.sr-bar-high {
  background: #28a745;
}
.sr-bar-mid {
  background: #ffc107;
}
.sr-bar-low {
  background: #dc3545;
}

.sr-item-val {
  text-align: right;
}

.sr-chart-placeholder {
  background: #f1f3f5;
  border: 2px dashed #ced4da;
  border-radius: 8px;
  height: 260px;
  font-size: 1rem;
  color: #adb5bd;
}

.sr-tag-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.sr-strategy-tag {
  position: relative;
  display: inline-block;
  padding: 3px 10px;
  border-radius: 12px;
  background: #e8f0fe;
  color: #3367d6;
  font-size: 0.75rem;
  line-height: 1.4;
  white-space: normal;
  word-break: break-word;
  cursor: default;
}

.sr-strategy-tag::before {
  content: attr(data-tip);
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  background: rgba(33, 37, 41, 0.93);
  color: #fff;
  border-radius: 6px;
  padding: 7px 11px;
  font-size: 0.72rem;
  line-height: 1.5;
  width: 240px;
  white-space: normal;
  z-index: 200;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.15s;
}

.sr-strategy-tag:hover::before {
  opacity: 1;
}
</style>
