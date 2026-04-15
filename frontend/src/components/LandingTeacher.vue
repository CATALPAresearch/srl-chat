<template>
  <div class="landing-teacher container-fluid py-4">
    <!-- Header banner -->
    <div class="row justify-content-center mb-4">
      <div class="col-md-11">
        <div class="card border-0 shadow-sm hero-card">
          <div class="card-body p-4">
            <div class="d-flex align-items-center mb-2">
              <span class="badge badge-warning text-dark mr-2">
                {{ lang === "de" ? "Lehrender" : "Instructor" }}
              </span>
              <h2 class="mb-0">
                {{
                  lang === "de"
                    ? "SRL-Chat – Kursübersicht"
                    : "SRL Chat – Course Overview"
                }}
              </h2>
            </div>
            <p class="text-muted mb-0">
              {{
                lang === "de"
                  ? "Übersicht über Kursaktivität, Lernstrategien und Umfrageergebnisse Ihrer Studierenden."
                  : "Overview of course activity, learning strategies and survey results for your students."
              }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- KPI row -->
    <div class="row justify-content-center mb-4">
      <div class="col-md-11">
        <div class="row">
          <div
            class="col-6 col-md-3 mb-3"
            v-for="kpi in kpis"
            :key="kpi.labelEn"
          >
            <div class="card border-0 shadow-sm text-center h-100">
              <div class="card-body py-3">
                <div class="kpi-value" :class="kpi.color">{{ kpi.value }}</div>
                <div class="kpi-label text-muted small">
                  {{ lang === "de" ? kpi.labelDe : kpi.labelEn }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Main content columns -->
    <div class="row justify-content-center mb-4">
      <div class="col-md-11">
        <div class="row">
          <!-- Student activity table -->
          <div class="col-md-7 mb-3">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-header bg-white border-bottom-0 pb-0">
                <h6 class="font-weight-600 mb-0">
                  {{
                    lang === "de"
                      ? "Aktivität der Studierenden (Demo)"
                      : "Student Activity (Demo)"
                  }}
                </h6>
              </div>
              <div class="card-body p-0">
                <table class="table table-sm table-hover mb-0">
                  <thead class="thead-light">
                    <tr>
                      <th>{{ lang === "de" ? "Studierende/r" : "Student" }}</th>
                      <th>{{ lang === "de" ? "Interview" : "Interview" }}</th>
                      <th>{{ lang === "de" ? "Umfrage" : "Survey" }}</th>
                      <th>
                        {{ lang === "de" ? "Zuletzt aktiv" : "Last Active" }}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="s in demoStudents" :key="s.name">
                      <td>{{ s.name }}</td>
                      <td>
                        <span
                          :class="
                            s.interview
                              ? 'badge badge-success'
                              : 'badge badge-secondary'
                          "
                        >
                          {{ s.interview ? "✓" : "–" }}
                        </span>
                      </td>
                      <td>
                        <span
                          :class="
                            s.survey
                              ? 'badge badge-success'
                              : 'badge badge-secondary'
                          "
                        >
                          {{ s.survey ? "✓" : "–" }}
                        </span>
                      </td>
                      <td class="text-muted small">{{ s.lastActive }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <!-- Quick links -->
          <div class="col-md-5 mb-3">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-header bg-white border-bottom-0 pb-0">
                <h6 class="font-weight-600 mb-0">
                  {{ lang === "de" ? "Werkzeuge" : "Tools" }}
                </h6>
              </div>
              <div class="card-body">
                <router-link
                  v-for="tool in tools"
                  :key="tool.route"
                  :to="tool.route"
                  class="d-flex align-items-center tool-link mb-3 text-decoration-none"
                >
                  <div class="tool-icon mr-3">
                    <font-awesome-icon :icon="tool.icon" class="text-primary" />
                  </div>
                  <div>
                    <div class="font-weight-500">
                      {{ lang === "de" ? tool.titleDe : tool.titleEn }}
                    </div>
                    <div class="text-muted small">
                      {{ lang === "de" ? tool.descDe : tool.descEn }}
                    </div>
                  </div>
                </router-link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Info alert -->
    <div class="row justify-content-center">
      <div class="col-md-11">
        <div class="alert alert-secondary border-0 shadow-sm small mb-0">
          <strong>{{ lang === "de" ? "Hinweis:" : "Note:" }}</strong>
          {{
            lang === "de"
              ? " Die angezeigten Studierendendaten sind Beispieldaten. Die Vollansicht finden Sie im Researcher-Dashboard."
              : " Student data shown here is sample data. For full analysis, open the Researcher Dashboard."
          }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Vue from "vue";

export default Vue.extend({
  name: "LandingTeacher",

  data() {
    return {
      kpis: [
        {
          value: "24",
          labelDe: "Eingeschriebene",
          labelEn: "Enrolled",
          color: "text-primary",
        },
        {
          value: "17",
          labelDe: "Interview absolviert",
          labelEn: "Interview done",
          color: "text-success",
        },
        {
          value: "12",
          labelDe: "Umfrage ausgefüllt",
          labelEn: "Survey completed",
          color: "text-info",
        },
        {
          value: "71%",
          labelDe: "Abschlussquote",
          labelEn: "Completion rate",
          color: "text-warning",
        },
      ],
      demoStudents: [
        { name: "Anna M.", interview: true, survey: true, lastActive: "heute" },
        {
          name: "Ben K.",
          interview: true,
          survey: false,
          lastActive: "gestern",
        },
        {
          name: "Clara S.",
          interview: false,
          survey: false,
          lastActive: "vor 3 Tagen",
        },
        {
          name: "David P.",
          interview: true,
          survey: true,
          lastActive: "heute",
        },
        {
          name: "Eva R.",
          interview: false,
          survey: true,
          lastActive: "vor 1 Woche",
        },
      ],
      tools: [
        {
          route: "/dashboard/researcher",
          icon: "thumbs-up",
          titleDe: "Researcher Dashboard",
          titleEn: "Researcher Dashboard",
          descDe: "Detaillierte Statistiken und Exportfunktionen.",
          descEn: "Detailed statistics and export functions.",
        },
        {
          route: "/survey",
          icon: "copy",
          titleDe: "Umfrage ansehen",
          titleEn: "View Survey",
          descDe: "SRL-O-Fragebogen in der Studierendenansicht.",
          descEn: "SRL-O questionnaire as seen by students.",
        },
        {
          route: "/agent-chat",
          icon: "cog",
          titleDe: "Chat testen",
          titleEn: "Test Chat",
          descDe: "Interview-Chat als Studierende/r ausprobieren.",
          descEn: "Try the interview chat as a student.",
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
.landing-teacher {
  max-width: 1100px;
  margin: 0 auto;
}

.hero-card {
  background: linear-gradient(135deg, #fff8e1 0%, #f8f9fa 100%);
}

.kpi-value {
  font-size: 1.8rem;
  font-weight: 700;
}

.kpi-label {
  font-size: 0.78rem;
  margin-top: 2px;
}

.font-weight-500 {
  font-weight: 500;
}

.font-weight-600 {
  font-weight: 600;
}

.tool-link {
  padding: 8px 10px;
  border-radius: 6px;
  transition: background 0.15s;
}

.tool-link:hover {
  background: #f8f9fa;
}

.tool-icon {
  width: 28px;
  text-align: center;
  font-size: 1.1rem;
}
</style>
