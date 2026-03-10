import Vue from "vue";
import VueRouter from "vue-router";

import AgentChat from "../components/AgentChat.vue";
import LLMChat from "../components/LLMChat.vue";
import RAGChat from "../components/RAGChat.vue";
import SurveyView from "../components/SurveyView.vue";

Vue.use(VueRouter);

const routes = [
  { path: "/", redirect: "/agent-chat" }, // Agent chat default
  { path: "/agent-chat", component: AgentChat },
  { path: "/llm-chat", component: LLMChat },
  { path: "/document-chat", component: RAGChat },
  { path: "/survey", component: SurveyView },
];

export default new VueRouter({
  mode: "hash", //  REQUIRED for LTI + Flask
  routes,
});
