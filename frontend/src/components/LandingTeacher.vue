<template>
  <div class="landing-teacher container-fluid py-4">
    <!-- KPI row: interviews done + completion rate -->
    <div class="row justify-content-center mb-4">
      <div class="col-md-10">
        <div class="row">
          <div class="col-sm-6 mb-3">
            <div class="card text-center border-0 shadow-sm h-100">
              <div class="card-body py-3">
                <div class="kpi-value text-success">{{ kpis[0].value }}</div>
                <div class="kpi-label text-muted small">
                  {{ lang === "de" ? kpis[0].labelDe : kpis[0].labelEn }}
                </div>
              </div>
            </div>
          </div>
          <div class="col-sm-6 mb-3">
            <div class="card text-center border-0 shadow-sm h-100">
              <div class="card-body py-3">
                <div class="kpi-value text-warning">{{ kpis[1].value }}</div>
                <div class="kpi-label text-muted small">
                  {{ lang === "de" ? kpis[1].labelDe : kpis[1].labelEn }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Welcome card -->
    <div class="row justify-content-center mb-4">
      <div class="col-md-10">
        <div class="card border-0 shadow-sm">
          <div class="card-body p-4">
            <!-- Intro text -->
            <h3 class="mb-3">
              {{ lang === "de" ? "Willkommen!" : "Welcome!" }}
            </h3>
            <p v-if="lang === 'de'">
              Wir freuen uns, Sie einzuladen, ein neues System gemeinsam mit
              Ihren Studierenden auszuprobieren. Zusammen mit Studierenden,
              Forschenden und Lehrenden haben wir ein Werkzeug entwickelt, das
              Studierende dabei unterstützt, nachzudenken, wie sie lernen, und
              bessere Lernwege zu finden.
            </p>
            <p v-else>
              We're excited to invite you to try out a new system with your
              students. Together with students, researchers, and professors
              we've created a tool that helps students think about how they
              study and find better ways to learn.
            </p>
            <p v-if="lang === 'de'">
              Studierende verbringen etwa <strong>10 Minuten</strong> damit, mit
              dem System zu chatten und Fragen zu ihren Lerngewohnheiten zu
              beantworten. Das System gibt dann umgehend jedem Studierenden
              <strong>personalisiertes Feedback</strong> – basierend auf
              Lerntheorien und empirisch validierten Instrumenten.
            </p>
            <p v-else>
              Students will spend about <strong>10 minutes</strong> chatting
              with it, answering questions about their study habits. Then, the
              system will promptly give each student
              <strong>personalized feedback</strong> (based on learning theories
              and empirically validated instruments).
            </p>

            <hr />

            <!-- 2×2 feature matrix -->
            <div class="row mt-3 mb-4">
              <!-- Security & Integration -->
              <div class="col-md-6 mb-3">
                <div class="feature-card h-100 p-3 d-flex flex-column">
                  <h6 class="feature-title">
                    {{
                      lang === "de"
                        ? "Systemsicherheit & Integration"
                        : "System Security & Integration"
                    }}
                  </h6>
                  <ul class="feature-list flex-grow-1" v-if="lang === 'de'">
                    <li>Läuft sicher an der FernUniversität Hagen.</li>
                    <li>Als Plugin in die Kurswebseite integriert.</li>
                    <li>Daten der Studierenden werden sicher verarbeitet.</li>
                  </ul>
                  <ul class="feature-list flex-grow-1" v-else>
                    <li>Runs securely at FernUniversität Hagen.</li>
                    <li>Integrated as a plugin on course webpage.</li>
                    <li>Students' data handled safely.</li>
                  </ul>
                  <span class="feature-badge badge-security mt-2">
                    {{
                      lang === "de"
                        ? "SICHER, ERPROBT & EINFACH ZU NUTZEN ✓"
                        : "SAFE, SECURE, AND EASY TO USE ✓"
                    }}
                  </span>
                </div>
              </div>
              <!-- Student Actions -->
              <div class="col-md-6 mb-3">
                <div class="feature-card h-100 p-3 d-flex flex-column">
                  <h6 class="feature-title">
                    {{
                      lang === "de" ? "Was Studierende tun" : "Student Actions"
                    }}
                  </h6>
                  <ul class="feature-list flex-grow-1" v-if="lang === 'de'">
                    <li>Ca. 10 Minuten chatten.</li>
                    <li>Einige Fragen zu Lerngewohnheiten beantworten.</li>
                    <li>Das System gibt personalisiertes Feedback.</li>
                  </ul>
                  <ul class="feature-list flex-grow-1" v-else>
                    <li>Spend ~10 min chatting.</li>
                    <li>Answer a few questions about study habits.</li>
                    <li>System provides personalized feedback.</li>
                  </ul>
                  <span class="feature-badge badge-student-action mt-2">
                    {{
                      lang === "de"
                        ? "WAS STUDIERENDE TUN MÜSSEN"
                        : "WHAT STUDENTS NEED TO DO"
                    }}
                  </span>
                </div>
              </div>
              <!-- Teacher Benefits -->
              <div class="col-md-6 mb-3">
                <div class="feature-card h-100 p-3 d-flex flex-column">
                  <h6 class="feature-title">
                    {{
                      lang === "de" ? "Vorteile für Sie" : "Teacher Benefits"
                    }}
                  </h6>
                  <ul class="feature-list flex-grow-1" v-if="lang === 'de'">
                    <li>
                      Detaillierte Analyse der Lernstrategien Ihrer
                      Studierenden.
                    </li>
                    <li>Praktische Empfehlungen abgestimmt auf Kursziele.</li>
                    <li>Vergleich mit Forschungsmustern.</li>
                  </ul>
                  <ul class="feature-list flex-grow-1" v-else>
                    <li>Detailed analysis of student learning strategies.</li>
                    <li>Practical suggestions aligned with course goals.</li>
                    <li>Comparison to research patterns.</li>
                  </ul>
                  <span class="feature-badge badge-teacher mt-2">
                    {{
                      lang === "de"
                        ? "VORTEILE FÜR SIE ALS LEHRENDE/R"
                        : "BENEFITS FOR YOU, THE TEACHER"
                    }}
                  </span>
                </div>
              </div>
              <!-- Student Benefits -->
              <div class="col-md-6 mb-3">
                <div class="feature-card h-100 p-3 d-flex flex-column">
                  <h6 class="feature-title">
                    {{
                      lang === "de"
                        ? "Vorteile für Ihre Studierenden"
                        : "Student Benefits"
                    }}
                  </h6>
                  <ul class="feature-list flex-grow-1" v-if="lang === 'de'">
                    <li>Verwendete Strategien entdecken.</li>
                    <li>
                      Effektive forschungsbasierte Strategien kennenlernen.
                    </li>
                    <li>Lernansatz mit anderen Studierenden vergleichen.</li>
                    <li>Personalisierte Tipps erhalten.</li>
                  </ul>
                  <ul class="feature-list flex-grow-1" v-else>
                    <li>Discover used strategies.</li>
                    <li>Learn effective research-backed strategies.</li>
                    <li>Compare approach with other students.</li>
                    <li>Get personalized tips.</li>
                  </ul>
                  <span class="feature-badge badge-student-benefit mt-2">
                    {{
                      lang === "de"
                        ? "VORTEILE FÜR IHRE STUDIERENDEN"
                        : "BENEFITS FOR YOUR STUDENTS"
                    }}
                  </span>
                </div>
              </div>
            </div>

            <hr />

            <!-- Closing paragraph -->
            <p v-if="lang === 'de'">
              Mit unserer einfach zu bedienenden Oberfläche unterstützen wir Sie
              bei der Integration des Systems in Ihren Kurs. Sie als Lehrende/r
              erhalten auch Einblick, wie Ihre Studierenden lernen, welche
              Strategien sie nutzen, und hilfreiche Hinweise, wie Sie sie
              effektiv unterstützen können.
            </p>
            <p v-else>
              With our easy-to-use interface, we'll support you in integrating
              the system to your course. You as a teacher will also see how your
              student cohort learn, the strategies they use, and even get
              helpful tips on how to support them effectively.
            </p>
            <p v-if="lang === 'de'">
              Unsere Vision ist es, jedem Studierenden zu helfen,
              selbstbewusster zu lernen und ihnen Werkzeuge zu geben, um als
              unabhängige Lernende zu erkunden, zu experimentieren und zu
              wachsen.
            </p>
            <p v-else>
              Our vision is to help every student learn more confidently while
              giving them the tools to explore, experiment, and grow as
              independent learners.
            </p>

            <!-- Action buttons -->
            <div class="d-flex flex-wrap gap-2 mb-4">
              <router-link to="/agent-chat">
                <button class="btn btn-primary mr-2 mb-2">
                  {{
                    lang === "de"
                      ? "Jetzt selbst ausprobieren"
                      : "Try it yourself"
                  }}
                </button>
              </router-link>
              <router-link to="/dashboard/researcher">
                <button class="btn btn-outline-secondary mb-2">
                  {{
                    lang === "de"
                      ? "Ergebnisse meiner Studierenden ansehen"
                      : "View my students' results"
                  }}
                </button>
              </router-link>
            </div>

            <hr />

            <!-- Consent not yet given -->
            <div v-if="!consentGiven" class="mb-2">
              <p class="mb-3">
                {{
                  lang === "de"
                    ? "Um fortzufahren bitten wir Sie um Ihre Einwilligung zur Erhebung und Auswertung der Daten. Die Teilnahme ist freiwillig und Sie können jederzeit aufhören."
                    : "To continue, we ask for your informed consent to collect and analyze data. Participation is completely voluntary, and you can stop at any time."
                }}
              </p>
              <button class="btn btn-outline-primary" @click="openConsentModal">
                {{
                  lang === "de"
                    ? "Einwilligungserklärung lesen &amp; zustimmen"
                    : "Read &amp; give consent"
                }}
              </button>
            </div>

            <!-- Consent given confirmation -->
            <div v-else class="alert alert-success border-0 mb-0">
              <span class="mr-2">✅</span>
              {{
                lang === "de"
                  ? "Einwilligung erteilt. Vielen Dank."
                  : "Consent given. Thank you."
              }}
            </div>

            <!-- Consent modal -->
            <div
              v-if="showConsentModal"
              class="consent-modal-overlay"
              @click.self="showConsentModal = false"
            >
              <div class="consent-modal-box">
                <button
                  class="consent-modal-close"
                  @click="showConsentModal = false"
                  aria-label="Close"
                >
                  &times;
                </button>
                <ChatInformedConsent />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Vue from "vue";
import axios from "axios";
import ChatInformedConsent from "./ChatInformedConsent.vue";

const CONSENT_KEY = "srl_informed_consent";

export default Vue.extend({
  name: "LandingTeacher",

  components: { ChatInformedConsent },

  data() {
    return {
      showConsentModal: false,
      dashboardStats: null,
    };
  },

  computed: {
    lang() {
      return this.$store.getters.getLanguage || "de";
    },
    consentGiven() {
      return this.$store.getters.getInformedConsentAgreement === "yes";
    },
    kpis() {
      const s = this.dashboardStats;
      const done = s ? s.total_completed : "–";
      const total = s ? s.total_students : 0;
      const rate =
        s && total > 0
          ? Math.round((s.total_completed / total) * 100) + "%"
          : "–";
      return [
        {
          value: done,
          labelDe: "Interview absolviert",
          labelEn: "Interview done",
        },
        { value: rate, labelDe: "Abschlussquote", labelEn: "Completion rate" },
      ];
    },
  },

  watch: {
    consentGiven(val) {
      if (val) {
        localStorage.setItem(CONSENT_KEY, "yes");
        this.showConsentModal = false;
      }
    },
    "$store.getters.getInformedConsentAgreement"(val) {
      if (val === "no" && this.showConsentModal) {
        this.showConsentModal = false;
      }
    },
  },

  mounted() {
    const stored = localStorage.getItem(CONSENT_KEY);
    if (stored === "yes") {
      this.$store.commit("setInformedConsentAgreement", "yes");
    } else if (this.$store.getters.getInformedConsentAgreement === false) {
      this.$store.commit("setInformedConsentAgreement", "none");
    }
    this.loadStats();
  },

  methods: {
    async loadStats() {
      try {
        const base = window.SRL_BACKEND_URL || "";
        const res = await axios.get(`${base}/dashboard/stats`);
        this.dashboardStats = res.data;
      } catch {
        // backend unreachable — kpis stay "–"
      }
    },
    openConsentModal() {
      this.$store.commit("setInformedConsentAgreement", "none");
      this.showConsentModal = true;
    },
  },
});
</script>

<style scoped>
.landing-teacher {
  max-width: 960px;
  margin: 0 auto;
}

.section-label {
  color: #495057;
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.78rem;
  letter-spacing: 0.08em;
}

.kpi-value {
  font-size: 1.8rem;
  font-weight: 700;
}

.kpi-label {
  font-size: 0.78rem;
  margin-top: 2px;
}

/* Feature matrix cards */
.feature-card {
  border: 1px solid #e9ecef;
  border-radius: 8px;
  background: #f8f9fa;
}

.feature-badge {
  display: inline-block;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  padding: 3px 8px;
  border-radius: 4px;
}

.badge-security {
  background: #d4edda;
  color: #155724;
}
.badge-student-action {
  background: #cce5ff;
  color: #004085;
}
.badge-teacher {
  background: #fff3cd;
  color: #856404;
}
.badge-student-benefit {
  background: #d1ecf1;
  color: #0c5460;
}

.feature-title {
  font-weight: 600;
  font-size: 0.95rem;
  color: #343a40;
}

.feature-list {
  padding-left: 1.2rem;
  margin-bottom: 0;
  font-size: 0.88rem;
  color: #495057;
}

.feature-list li {
  margin-bottom: 4px;
}

/* Consent modal */
.consent-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.consent-modal-box {
  background: white;
  border-radius: 10px;
  padding: 28px 32px;
  width: 90%;
  max-width: 720px;
  max-height: 85vh;
  overflow-y: auto;
  position: relative;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.18);
}

.consent-modal-close {
  position: absolute;
  top: 14px;
  right: 18px;
  background: none;
  border: none;
  font-size: 1.6rem;
  line-height: 1;
  cursor: pointer;
  color: #6c757d;
}

.consent-modal-close:hover {
  color: #343a40;
}
</style>
