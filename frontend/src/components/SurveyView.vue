<template>
  <div class="survey-container content">
    <!-- ---------- SUBMITTED STATE ---------- -->
    <div v-if="submitted" class="survey-done alert alert-success" role="status">
      <h4>{{ lang === "de" ? "Vielen Dank!" : "Thank you!" }}</h4>
      <p>
        {{
          lang === "de"
            ? "Ihre Antworten wurden gespeichert."
            : "Your responses have been saved."
        }}
      </p>
    </div>

    <!-- ---------- LOADING ---------- -->
    <div v-else-if="loading" class="text-center p-4">
      <font-awesome-icon icon="spinner" spin />
      {{ lang === "de" ? "Lade Fragebogen…" : "Loading survey…" }}
    </div>

    <!-- ---------- ERROR ---------- -->
    <div v-else-if="errorMsg" class="alert alert-danger" role="alert">
      {{ errorMsg }}
    </div>

    <!-- ---------- SURVEY FORM ---------- -->
    <div v-else-if="survey" class="survey-form">
      <h3>
        {{
          typeof survey.title === "string"
            ? survey.title
            : survey.title[lang] || survey.title.en
        }}
      </h3>
      <p class="survey-desc">
        {{
          typeof survey.description === "string"
            ? survey.description
            : survey.description[lang] || survey.description.en
        }}
      </p>

      <form @submit.prevent="submitSurvey">
        <div
          v-for="(scale, sIdx) in survey.scales"
          :key="scale.id"
          class="survey-scale"
        >
          <h5 class="scale-title">
            {{ sIdx + 1 }}.
            {{
              typeof scale.title === "string"
                ? scale.title
                : scale.title[lang] || scale.title.en
            }}
          </h5>

          <table class="survey-table">
            <thead>
              <tr>
                <th class="item-text-col"></th>
                <th v-for="v in scaleRange" :key="v" class="likert-col">
                  <span class="likert-label">{{ scaleLabel(v) }}</span>
                  <span class="likert-num">{{ v }}</span>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in scale.items"
                :key="item.id"
                :class="{ unanswered: showValidation && !responses[item.id] }"
              >
                <td class="item-text-col">
                  {{
                    typeof item.text === "string"
                      ? item.text
                      : item.text[lang] || item.text.en
                  }}
                </td>
                <td v-for="v in scaleRange" :key="v" class="likert-col">
                  <label class="likert-radio-label">
                    <input
                      type="radio"
                      :name="item.id"
                      :value="v"
                      v-model.number="responses[item.id]"
                      class="likert-radio"
                    />
                  </label>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div
          v-if="showValidation && unansweredCount > 0"
          class="alert alert-warning mt-3"
        >
          {{
            lang === "de"
              ? `Bitte beantworten Sie alle ${unansweredCount} fehlenden Fragen.`
              : `Please answer all ${unansweredCount} remaining questions.`
          }}
        </div>

        <button
          type="submit"
          class="btn btn-primary mt-3 mb-4"
          :disabled="submitting"
        >
          <font-awesome-icon
            v-if="submitting"
            icon="spinner"
            spin
            class="mr-1"
          />
          {{ lang === "de" ? "Absenden" : "Submit" }}
        </button>
      </form>
    </div>
  </div>
</template>

<script>
import Vue from "vue";
import axios from "axios";

export default Vue.extend({
  name: "SurveyView",

  data() {
    return {
      surveyId: "srl-o",
      survey: null,
      responses: {},
      loading: true,
      submitting: false,
      submitted: false,
      errorMsg: "",
      showValidation: false,
      host: "http://localhost:5000",
    };
  },

  computed: {
    lang() {
      // Use the store language (defaults to German)
      return this.$store.getters.getLanguage || "de";
    },

    scaleRange() {
      if (!this.survey) return [];
      const s = this.survey.scale;
      const range = [];
      for (let i = s.min; i <= s.max; i++) range.push(i);
      return range;
    },

    allItemIds() {
      if (!this.survey) return [];
      return this.survey.scales.flatMap((sc) => sc.items.map((it) => it.id));
    },

    unansweredCount() {
      return this.allItemIds.filter((id) => !this.responses[id]).length;
    },
  },

  watch: {
    lang(newLang, oldLang) {
      if (newLang !== oldLang) {
        this.loading = true;
        this.survey = null;
        this.responses = {};
        this.showValidation = false;
        this.errorMsg = "";
        this.loadSurvey();
      }
    },
  },

  methods: {
    scaleLabel(value) {
      if (!this.survey) return "";
      const labels = Array.isArray(this.survey.scale.labels)
        ? this.survey.scale.labels
        : this.survey.scale.labels[this.lang] || this.survey.scale.labels.en;
      return labels[value - this.survey.scale.min] || "";
    },

    async loadSurvey() {
      try {
        const params = {
          lang: this.lang,
          userid: this.$store.getters.getUser,
          client: "standalone",
        };
        const res = await axios.get(`${this.host}/survey/${this.surveyId}`, {
          params,
        });
        this.survey = res.data;

        // Pre-populate responses keys so Vue reactivity tracks them
        const r = {};
        this.survey.scales.forEach((sc) =>
          sc.items.forEach((it) => {
            r[it.id] = null;
          }),
        );
        this.responses = r;
      } catch (e) {
        console.error("Failed to load survey", e);
        this.errorMsg =
          this.lang === "de"
            ? "Fragebogen konnte nicht geladen werden."
            : "Failed to load survey.";
      } finally {
        this.loading = false;
      }
    },

    async submitSurvey() {
      this.showValidation = true;
      if (this.unansweredCount > 0) return;

      this.submitting = true;
      try {
        await axios.post(`${this.host}/survey/${this.surveyId}/submit`, {
          userid: this.$store.getters.getUser,
          client: "standalone",
          language: this.lang,
          responses: this.responses,
        });
        this.submitted = true;
      } catch (e) {
        console.error("Failed to submit survey", e);
        this.errorMsg =
          this.lang === "de"
            ? "Fehler beim Speichern. Bitte versuchen Sie es erneut."
            : "Failed to save. Please try again.";
      } finally {
        this.submitting = false;
      }
    },
  },

  mounted() {
    this.loadSurvey();
  },
});
</script>

<style scoped>
.survey-container {
  max-width: 960px;
  margin: 0 auto;
  padding: 16px;
  overflow-y: auto;
  flex: 1 1 0;
  min-height: 0;
}

.survey-desc {
  color: #555;
  margin-bottom: 24px;
}

.survey-scale {
  margin-bottom: 32px;
}

.scale-title {
  margin-bottom: 8px;
  font-weight: 600;
}

.survey-table {
  width: 100%;
  border-collapse: collapse;
}

.survey-table th,
.survey-table td {
  padding: 6px 4px;
  vertical-align: middle;
}

.item-text-col {
  text-align: left;
  width: 60%;
  font-size: 0.95rem;
}

.likert-col {
  text-align: center;
  width: 8%;
}

.likert-label {
  display: block;
  font-size: 0.7rem;
  color: #666;
  white-space: nowrap;
}

.likert-num {
  display: block;
  font-weight: 600;
  font-size: 0.85rem;
}

.likert-radio-label {
  display: flex;
  justify-content: center;
  cursor: pointer;
  margin: 0;
}

.likert-radio {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.survey-table tbody tr {
  border-bottom: 1px solid #eee;
}

.survey-table tbody tr:hover {
  background: #f8f9fa;
}

.survey-table tbody tr.unanswered {
  background: #fff3cd;
}

.survey-done {
  margin-top: 40px;
  text-align: center;
}
</style>
