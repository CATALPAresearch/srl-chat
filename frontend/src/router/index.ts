import Vue from "vue";
import VueRouter from "vue-router";
import axios from "axios";
import AgentChat from "../components/AgentChat.vue";
import LLMChat from "../components/LLMChat.vue";
import RAGChat from "../components/RAGChat.vue";
import SurveyView from "../components/SurveyView.vue";
import ProtocolEditor from "../components/ProtocolEditor.vue";
import DashboardResearcher from "../components/DashboardResearcher.vue";
import TeacherDashboard from "../components/DashboardTeacher.vue";
import LandingPage from "../components/LandingPage.vue";
import StudentResults from "../components/StudentResults.vue";

Vue.use(VueRouter);
const routes = [
  { path: "/", component: LandingPage },
  { path: "/agent-chat", component: AgentChat },
  { path: "/llm-chat", component: LLMChat },
  { path: "/document-chat", component: RAGChat },
  { path: "/survey", component: SurveyView },
  { path: "/protocols", component: ProtocolEditor },
  { path: "/results", component: StudentResults },
  { path: "/dashboard/researcher", component: DashboardResearcher },
  { path: "/dashboard/teacher", component: TeacherDashboard },
];
const router = new VueRouter({
  mode: "hash",
  routes,
});

// Log every page navigation to the backend activity_log
router.afterEach((to) => {
  const apiBase =
    (window.SRL_CONFIG && window.SRL_CONFIG.apiBaseUrl) ||
    window.location.origin;
  const userid =
    (window.SRL_CONFIG && window.SRL_CONFIG.userId) ||
    new URLSearchParams(window.location.search).get("userid") ||
    localStorage.getItem("srl_userid");

  axios
    .post(apiBase + "/log/page_view", {
      userid,
      client: "web",
      path: to.fullPath,
      timestamp: Math.floor(Date.now() / 1000),
    })
    .catch(() => {
      /* non-critical */
    });
});

export default router;
