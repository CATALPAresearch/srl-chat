<template>
  <div class="landing-student container-fluid py-4">

    <!-- Progress stats -->
    <div class="row justify-content-center mb-4">
      <div class="col-md-10">
        <h5 class="section-label mb-3">
          {{ lang === "de" ? "Ihr Fortschritt" : "Your Progress" }}
        </h5>
        <div class="row">
          <!-- Interview progress -->
          <div class="col-sm-4 mb-3">
            <div class="card text-center border-0 shadow-sm h-100">
              <div class="card-body py-3">
                <div class="stat-value text-primary">{{ progressStats[0].value }}</div>
                <div class="stat-label text-muted small">
                  {{ lang === "de" ? progressStats[0].labelDe : progressStats[0].labelEn }}
                </div>
              </div>
            </div>
          </div>
          <!-- Survey progress -->
          <div class="col-sm-4 mb-3">
            <div class="card text-center border-0 shadow-sm h-100">
              <div class="card-body py-3">
                <div class="stat-value text-primary">{{ progressStats[1].value }}</div>
                <div class="stat-label text-muted small">
                  {{ lang === "de" ? progressStats[1].labelDe : progressStats[1].labelEn }}
                </div>
              </div>
            </div>
          </div>
          <!-- Strategies — clickable -->
          <div class="col-sm-4 mb-3">
            <div
              class="card text-center border-0 shadow-sm h-100 stat-card-clickable"
              @click="strategiesVisible = !strategiesVisible"
              role="button"
              :title="lang === 'de' ? 'Klicken zum Anzeigen' : 'Click to view'"
            >
              <div class="card-body py-3">
                <div class="stat-value text-primary">{{ progressStats[2].value }}</div>
                <div class="stat-label text-muted small">
                  {{ lang === "de" ? progressStats[2].labelDe : progressStats[2].labelEn }}
                </div>
                <div class="text-muted" style="font-size:0.7rem; margin-top:4px;">
                  {{ strategiesVisible ? "▲" : "▼" }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Strategies expandable panel -->
        <div v-show="strategiesVisible" class="strategies-panel mb-3">
          <p class="text-muted small mb-2">
            {{ lang === "de"
              ? "Ihre personalisierten Strategieempfehlungen finden Sie auf der Ergebnisseite."
              : "Your personalised strategy recommendations are available on the results page." }}
          </p>
          <router-link to="/results" class="btn btn-sm btn-outline-primary">
            {{ lang === "de" ? "Ergebnisse anzeigen" : "View Results" }}
          </router-link>
        </div>
      </div>
    </div>

    <!-- Welcome card -->
    <div class="row justify-content-center mb-4">
      <div class="col-md-10">
        <div class="card border-0 shadow-sm">
          <div class="card-body p-4">
            <h3 class="mb-3">{{ lang === "de" ? "Willkommen!" : "Welcome!" }}</h3>
            <p>
              Together with students, researchers, and professors we have developed a system that uses insights
              from learning science and artificial intelligence to help you better understand your learning
              strategies and study skills.
            </p>
            <p>
              In the next step, you will spend about <strong>10 minutes</strong> chatting with the system and
              answering a few questions about how you usually study in your course. Shortly after the
              conversation, the system will analyze your responses and provide you with
              <strong>personalized feedback</strong>.
            </p>
            <p class="mb-3">Our goal is to help you better understand how you study and explore new strategies
              that might make learning easier or more effective for you. You will discover:</p>
            <ul class="discover-list list-unstyled mb-4">
              <li>🧠 The learning strategies you already use most often</li>
              <li>🔍 Other effective strategies that research shows can help students learn</li>
              <li>📊 How your learning approach compares with patterns found in studies of other students</li>
              <li>💡 Practical ideas and simple tips you can try to improve or expand your learning strategies</li>
            </ul>

            <hr />

            <!-- Consent section -->
            <h5 class="mb-3">{{ lang === "de" ? "Bevor wir beginnen" : "Before we start" }}</h5>
            <p>
              To continue, we ask for your <strong>informed consent</strong> to collect and analyze your
              responses. Your data will be:
            </p>
            <ul class="mb-3">
              <li><strong>Anonymous</strong> – it cannot be linked to you personally</li>
              <li><strong>Securely stored</strong></li>
              <li><strong>Used only for research purposes</strong> to help us better understand students'
                learning processes and improve educational tools</li>
            </ul>
            <p>
              Participation is completely voluntary, and you can stop at any time.
            </p>

            <!-- Consent already given -->
            <div v-if="consentGiven" class="alert alert-success d-flex align-items-center mb-4" role="status">
              <span class="mr-2">✅</span>
              <span>{{ lang === "de" ? "Einwilligung bereits erteilt." : "Consent already given." }}</span>
            </div>

            <!-- Inline consent component (when not yet given) -->
            <div v-if="!consentGiven" class="mb-4">
              <div class="row">
                <ChatInformedConsent />
              </div>
            </div>

            <!-- Start button — only visible after consent -->
            <router-link v-if="consentGiven" to="/agent-chat">
              <button class="btn btn-primary btn-lg">
                {{ lang === "de" ? "Interview starten" : "Start Interview" }}
              </button>
            </router-link>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import Vue from "vue";
import ChatInformedConsent from "./ChatInformedConsent.vue";

const CONSENT_KEY = "srl_informed_consent";

export default Vue.extend({
  name: "LandingStudent",

  components: { ChatInformedConsent },

  data() {
    return {
      strategiesVisible: false,
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
    };
  },

  computed: {
    lang() {
      return this.$store.getters.getLanguage || "de";
    },
    consentGiven() {
      return this.$store.getters.getInformedConsentAgreement === "yes";
    },
  },

  watch: {
    consentGiven(val) {
      if (val) {
        localStorage.setItem(CONSENT_KEY, "yes");
      }
    },
  },

  mounted() {
    const stored = localStorage.getItem(CONSENT_KEY);
    if (stored === "yes") {
      this.$store.commit("setInformedConsentAgreement", "yes");
    } else if (this.$store.getters.getInformedConsentAgreement === false) {
      // initialise store to 'none' so ChatInformedConsent renders correctly
      this.$store.commit("setInformedConsentAgreement", "none");
    }
  },
});
</script>

<style scoped>
.landing-student {
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

.stat-value {
  font-size: 1.6rem;
  font-weight: 700;
}

.stat-label {
  font-size: 0.8rem;
  margin-top: 2px;
}

.stat-card-clickable {
  cursor: pointer;
  transition: box-shadow 0.2s, transform 0.2s;
}

.stat-card-clickable:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12) !important;
  transform: translateY(-2px);
}

.strategies-panel {
  background: #f0f4ff;
  border: 1px solid #c5d0e6;
  border-radius: 6px;
  padding: 14px 18px;
}

.discover-list li {
  margin-bottom: 8px;
}
</style>
