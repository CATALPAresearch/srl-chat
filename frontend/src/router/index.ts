import Vue from 'vue';
import VueRouter from 'vue-router';
import LLMChat from '../components/LLMChat.vue';
import RAGChat from '../components/RAGChat.vue';
import AgentChat from '../components/AgentChat.vue';

Vue.use(VueRouter); // ✅ Important: Use VueRouter before creating the instance

const routes = [
  { path: '/', redirect: '/agent-chat' }, // ✅ Agent Chat default
  { path: '/agent-chat', component: AgentChat },
  { path: '/document-chat', component: RAGChat },
  { path: '/llm-chat', component: LLMChat }
];


// FixMe: add moodle path to routes
const router = new VueRouter({ 
//  mode: 'history', 
// base: '/moodle/'
  routes
});

export default router;
