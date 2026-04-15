import Vue from "vue";
import VueRouter from "vue-router";
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
export default new VueRouter({
  mode: "hash",
  routes,
});
