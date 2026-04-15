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
              {{
                lang === "de"
                  ? "Hier sehen Sie die im Interview erkannten Lernstrategien und Ihre Umfrageantworten."
                  : "Below you can see the learning strategies identified in your interview and your survey responses."
              }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="row justify-content-center">
      <div class="col-md-10 text-center py-5 text-muted">
        <font-awesome-icon icon="spinner" spin class="mr-2" />
        {{ lang === "de" ? "Lade Ergebnisse…" : "Loading results…" }}
      </div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="row justify-content-center">
      <div class="col-md-10">
        <div class="alert alert-danger">{{ error }}</div>
      </div>
    </div>

    <template v-else>
      <!-- Status KPIs -->
      <div class="row justify-content-center mb-4">
        <div class="col-md-10">
          <div class="row">
            <div class="col-sm-4 mb-3">
              <div class="card border-0 shadow-sm text-center h-100">
                <div class="card-body py-3">
                  <div
                    class="sr-kpi-value"
                    :class="
                      data.interview_completed
                        ? 'text-success'
                        : 'text-secondary'
                    "
                  >
                    {{ data.interview_completed ? "✓" : "–" }}
                  </div>
                  <div class="sr-kpi-label text-muted">
                    {{ lang === "de" ? "Interview" : "Interview" }}
                  </div>
                </div>
              </div>
            </div>
            <div class="col-sm-4 mb-3">
              <div class="card border-0 shadow-sm text-center h-100">
                <div class="card-body py-3">
                  <div class="sr-kpi-value text-primary">
                    {{ data.strategies.length }}
                  </div>
                  <div class="sr-kpi-label text-muted">
                    {{
                      lang === "de"
                        ? "Erkannte Strategien"
                        : "Strategies Identified"
                    }}
                  </div>
                </div>
              </div>
            </div>
            <div class="col-sm-4 mb-3">
              <div class="card border-0 shadow-sm text-center h-100">
                <div class="card-body py-3">
                  <div
                    class="sr-kpi-value"
                    :class="data.survey ? 'text-success' : 'text-secondary'"
                  >
                    {{ data.survey ? "✓" : "–" }}
                  </div>
                  <div class="sr-kpi-label text-muted">
                    {{ lang === "de" ? "Umfrage" : "Survey" }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Strategies -->
      <div class="row justify-content-center mb-4">
        <div class="col-md-10">
          <div class="card border-0 shadow-sm">
            <div class="card-header bg-white">
              <h5 class="mb-0 sr-section-title">
                {{
                  lang === "de"
                    ? "Ihre Lernstrategien"
                    : "Your Learning Strategies"
                }}
              </h5>
              <p class="text-muted small mb-0">
                {{
                  lang === "de"
                    ? "Diese Strategien wurden im Interview identifiziert."
                    : "These strategies were identified during your interview."
                }}
              </p>
            </div>
            <div class="card-body p-0">
              <div
                v-if="!data.strategies.length"
                class="p-4 text-muted text-center"
              >
                {{
                  lang === "de"
                    ? "Noch keine Strategien erfasst."
                    : "No strategies recorded yet."
                }}
              </div>
              <div
                v-for="(s, i) in data.strategies"
                :key="s.id"
                class="sr-strategy-row d-flex align-items-start p-3"
                :class="{ 'border-top': i > 0 }"
              >
                <div class="sr-strategy-num text-primary font-weight-bold mr-3">
                  {{ i + 1 }}
                </div>
                <div class="flex-grow-1">
                  <div class="font-weight-600">{{ s.name }}</div>
                  <div class="text-muted small mt-1">{{ s.description }}</div>
                </div>
                <div v-if="s.frequency !== null" class="sr-freq-badge ml-3">
                  <span class="badge badge-light border">
                    {{ lang === "de" ? "Häufigkeit" : "Frequency" }}:
                    {{ s.frequency }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Survey results -->
      <div class="row justify-content-center mb-4">
        <div class="col-md-10">
          <div class="card border-0 shadow-sm">
            <div class="card-header bg-white">
              <h5 class="mb-0 sr-section-title">
                {{
                  lang === "de"
                    ? "Umfrageergebnisse (SRL-O)"
                    : "Survey Results (SRL-O)"
                }}
              </h5>
              <p class="text-muted small mb-0">
                {{
                  lang === "de"
                    ? "Ihre Selbsteinschätzung auf einer Skala von 1–5."
                    : "Your self-assessment on a scale of 1–5."
                }}
              </p>
            </div>
            <div class="card-body">
              <div v-if="!data.survey" class="text-muted text-center py-3">
                {{
                  lang === "de"
                    ? "Sie haben die Umfrage noch nicht ausgefüllt."
                    : "You have not completed the survey yet."
                }}
                <div class="mt-2">
                  <router-link
                    to="/survey"
                    class="btn btn-sm btn-outline-primary"
                  >
                    {{ lang === "de" ? "Zur Umfrage" : "Go to Survey" }}
                  </router-link>
                </div>
              </div>
              <template v-else>
                <div class="text-muted small mb-3">
                  {{ lang === "de" ? "Eingereicht am" : "Submitted" }}:
                  {{
                    new Date(data.survey.submitted_at).toLocaleDateString(
                      lang === "de" ? "de-DE" : "en-GB",
                    )
                  }}
                </div>
                <div class="sr-survey-grid">
                  <div
                    v-for="(val, key) in data.survey.responses"
                    :key="key"
                    class="sr-survey-item"
                  >
                    <div class="sr-item-id text-muted">{{ key }}</div>
                    <div class="sr-item-bar-wrap">
                      <div
                        class="sr-item-bar"
                        :style="{ width: (val / 5) * 100 + '%' }"
                        :class="barClass(val)"
                      ></div>
                    </div>
                    <div class="sr-item-val font-weight-600">{{ val }}</div>
                  </div>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>

      <!-- CTA -->
      <div class="row justify-content-center mb-4">
        <div class="col-md-10">
          <div
            class="alert alert-info border-0 shadow-sm d-flex align-items-center"
          >
            <div class="flex-grow-1">
              {{
                lang === "de"
                  ? "Möchten Sie die Umfrage ausfüllen oder das Interview erneut starten?"
                  : "Would you like to complete the survey or restart the interview?"
              }}
            </div>
            <router-link
              v-if="!data.survey"
              to="/survey"
              class="btn btn-primary btn-sm ml-3 text-nowrap"
            >
              {{ lang === "de" ? "Zur Umfrage" : "Take Survey" }}
            </router-link>
            <router-link
              to="/agent-chat"
              class="btn btn-outline-secondary btn-sm ml-2 text-nowrap"
            >
              {{ lang === "de" ? "Interview starten" : "Start Interview" }}
            </router-link>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import Vue from "vue";
import axios from "axios";

export default Vue.extend({
  name: "StudentResults",

  data() {
    return {
      host: "http://localhost:5000",
      loading: true,
      error: null,
      data: {
        strategies: [],
        survey: null,
        interview_completed: false,
      },
    };
  },

  computed: {
    lang() {
      return this.$store.getters.getLanguage || "de";
    },
  },

  methods: {
    barClass(val) {
      if (val >= 4) return "sr-bar-high";
      if (val >= 3) return "sr-bar-mid";
      return "sr-bar-low";
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
    },
  },

  mounted() {
    this.loadResults();
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
</style>
