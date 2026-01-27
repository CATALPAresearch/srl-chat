import Vue from "vue";
import VueRouter from "vue-router";

import AgentChat from "../components/AgentChat.vue";
import LLMChat from "../components/LLMChat.vue";
import RAGChat from "../components/RAGChat.vue";

Vue.use(VueRouter);

const isLTI = window.SRL_CLIENT === "lti";

const routes = [
  { path: "/", redirect: "/agent-chat" },
  { path: "/agent-chat", component: AgentChat },
  { path: "/llm-chat", component: LLMChat },
  { path: "/document-chat", component: RAGChat },
];

export default new VueRouter({
  mode: "history",
  base: isLTI ? "/lti/ui/" : "/",
  routes,
});
