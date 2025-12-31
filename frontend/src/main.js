import Vue from "vue";
import { store } from "./store";
import router from './router';
import ChatApp from "./components/ChatApp.vue";
import { library } from '@fortawesome/fontawesome-svg-core';
import { faCopy, faCog, faThumbsDown, faThumbsUp, faCheck } from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';

/**
 * 
 * @param {*} context Includes systemName, courseID, course_module_id, contextid, isAdmin, page_instance_id,
 * @param {*} llm Contains: LLMenabled, LLMhostname, LLMapiKey
 * @param {*} rag Includes RAGenabled, RAGhostname, RAGapiKey, 
 * @param {*} agent Includes agentenabled, agenthostname, agentapiKey
 */
function initOpenChat(context /*, llm, rag, agent*/) {
  
  store.commit("setPageInstanceId", context.page_instance_id);
  store.commit("setSystemContext", {"systemName": context.system_name, "courseID": context.course_id });
  store.commit("setAdmin", context.is_admin);
  store.commit("setCourseModuleID", context.course_module_id);
  store.commit("setPageInstanceId", context.page_instance_id)
  store.commit("setContextID", context.context_id);
  //store.commit('setRAGWebserviceHost', rag.RAGhostname)

  store.dispatch("loadPluginSettings");
  store.dispatch("loadPreference");
  store.dispatch("loadComponentStrings");
  
  //store.dispatch("loadRAGDocuments");
  

  library.add(faCopy, faCog, faThumbsDown, faThumbsUp, faCheck);

  Vue.component('font-awesome-icon', FontAwesomeIcon);

  new Vue({
    el: "#OpenChatApp",
    store,
    router,
    render: (h) => h(ChatApp),
  });
}

export { initOpenChat };
