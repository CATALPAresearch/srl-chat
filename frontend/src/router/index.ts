import Vue from "vue";
import VueRouter from "vue-router";
import AgentChat from "../components/AgentChat.vue";
import LLMChat from "../components/LLMChat.vue";
import RAGChat from "../components/RAGChat.vue";
import SurveyView from "../components/SurveyView.vue";
import ResearcherDashboard from "../components/ResearcherDashboard.vue";

Vue.use(VueRouter);
const routes = [
  { path: "/", redirect: "/agent-chat" },
  { path: "/agent-chat", component: AgentChat },
  { path: "/llm-chat", component: LLMChat },
  { path: "/document-chat", component: RAGChat },
  { path: "/survey", component: SurveyView },
  { path: "/dashboard/researcher", component: ResearcherDashboard },
  //{ path: "/dashboard/teacher", component: TeacherDashboard },
];
export default new VueRouter({
  mode: "hash",
  routes,
});
