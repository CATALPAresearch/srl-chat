<template>
  <div class="landing-student container-fluid py-4">
    <!-- Hero -->
    <div class="row justify-content-center mb-4">
      <div class="col-md-10">
        <div class="card border-0 shadow-sm hero-card">
          <div class="card-body d-flex align-items-center p-4">
            <div class="hero-icon mr-4">
              <font-awesome-icon
                icon="spinner"
                class="text-primary"
                style="font-size: 2.5rem"
              />
            </div>
            <div>
              <h2 class="mb-1">
                {{
                  lang === "de"
                    ? "Willkommen beim SRL-Chat"
                    : "Welcome to SRL Chat"
                }}
              </h2>
              <p class="text-muted mb-0">
                {{
                  lang === "de"
                    ? "Dieser Bereich unterstützt Sie dabei, Ihre Lernstrategien zu reflektieren und weiterzuentwickeln."
                    : "This tool helps you reflect on and develop your learning strategies."
                }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Progress row -->
    <div class="row justify-content-center mb-4">
      <div class="col-md-10">
        <h5 class="section-label mb-3">
          {{ lang === "de" ? "Ihr Fortschritt" : "Your Progress" }}
        </h5>
        <div class="row">
          <div
            class="col-sm-4 mb-3"
            v-for="stat in progressStats"
            :key="stat.label"
          >
            <div class="card text-center border-0 shadow-sm h-100">
              <div class="card-body py-3">
                <div class="stat-value text-primary">{{ stat.value }}</div>
                <div class="stat-label text-muted small">
                  {{ lang === "de" ? stat.labelDe : stat.labelEn }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick actions -->
    <div class="row justify-content-center mb-4">
      <div class="col-md-10">
        <h5 class="section-label mb-3">
          {{ lang === "de" ? "Schnellzugriff" : "Quick Actions" }}
        </h5>
        <div class="row">
          <div
            class="col-sm-6 col-md-4 mb-3"
            v-for="action in quickActions"
            :key="action.route"
          >
            <router-link :to="action.route" class="text-decoration-none">
              <div class="card action-card border-0 shadow-sm h-100">
                <div class="card-body d-flex align-items-start p-3">
                  <div class="action-icon mr-3">
                    <font-awesome-icon
                      :icon="action.icon"
                      class="text-primary"
                      style="font-size: 1.4rem"
                    />
                  </div>
                  <div>
                    <h6 class="mb-1">
                      {{ lang === "de" ? action.titleDe : action.titleEn }}
                    </h6>
                    <p class="text-muted small mb-0">
                      {{ lang === "de" ? action.descDe : action.descEn }}
                    </p>
                  </div>
                </div>
              </div>
            </router-link>
          </div>
        </div>
      </div>
    </div>

    <!-- Info box -->
    <div class="row justify-content-center">
      <div class="col-md-10">
        <div class="alert alert-info border-0 shadow-sm">
          <strong>{{ lang === "de" ? "Tipp:" : "Tip:" }}</strong>
          {{
            lang === "de"
              ? " Bearbeiten Sie zuerst das Interview, bevor Sie die Umfrage ausfüllen. So erhalten Sie personalisiertere Strategieempfehlungen."
              : " Complete the interview before filling in the survey to receive more personalised strategy recommendations."
          }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Vue from "vue";

export default Vue.extend({
  name: "LandingStudent",

  data() {
    return {
      progressStats: [
        {
          value: "0 / 7",
          labelDe: "Interview-Fragen beantwortet",
          labelEn: "Interview questions answered",
        },
        {
          value: "–",
          labelDe: "Fragebogen abgeschlossen",
          labelEn: "Survey completed",
        },
        {
          value: "3",
          labelDe: "Empfohlene Strategien",
          labelEn: "Recommended strategies",
        },
      ],
      quickActions: [
        {
          route: "/agent-chat",
          icon: "check",
          titleDe: "Interview starten",
          titleEn: "Start Interview",
          descDe: "Reflektieren Sie Ihre Lernstrategien im geführten Gespräch.",
          descEn:
            "Reflect on your learning strategies in a guided conversation.",
        },
        {
          route: "/survey",
          icon: "thumbs-up",
          titleDe: "Umfrage ausfüllen",
          titleEn: "Complete Survey",
          descDe:
            "Selbsteinschätzung zur Selbstregulation beim Online-Lernen (SRL-O).",
          descEn: "Self-assessment on self-regulated online learning (SRL-O).",
        },
      ],
    };
  },

  computed: {
    lang() {
      return this.$store.getters.getLanguage || "de";
    },
  },
});
</script>

<style scoped>
.landing-student {
  max-width: 960px;
  margin: 0 auto;
}

.hero-card {
  background: linear-gradient(135deg, #e8f0fe 0%, #f8f9fa 100%);
}

.hero-icon {
  min-width: 56px;
  text-align: center;
}

.section-label {
  color: #495057;
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.78rem;
  letter-spacing: 0.08em;
}

.stat-value {
  font-size: 1.6rem;
  font-weight: 700;
}

.stat-label {
  font-size: 0.8rem;
  margin-top: 2px;
}

.action-card {
  transition: box-shadow 0.2s, transform 0.2s;
  cursor: pointer;
}

.action-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12) !important;
  transform: translateY(-2px);
}

.action-icon {
  min-width: 32px;
  padding-top: 2px;
}
</style>
