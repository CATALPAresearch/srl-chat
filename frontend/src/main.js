import Vue from "vue";
import { store } from "./store";
import router from "./router";
import ChatApp from "./components/ChatApp.vue";
import { library } from "@fortawesome/fontawesome-svg-core";
import {
  faCopy,
  faCog,
  faThumbsDown,
  faThumbsUp,
  faCheck,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";

function initOpenChat(context) {
  store.commit("setPageInstanceId", context.page_instance_id);
  store.commit("setSystemContext", {
    systemName: context.system_name,
    courseID: context.course_id,
  });
  store.commit("setAdmin", context.is_admin);
  store.commit("setCourseModuleID", context.course_module_id);
  store.commit("setContextID", context.context_id);
  store.commit("setUserId", context.user_id || window.SRL_USERID || "lti-user");

  store.dispatch("loadPluginSettings");
  store.dispatch("loadPreference");
  store.dispatch("loadComponentStrings");

  library.add(faCopy, faCog, faThumbsDown, faThumbsUp, faCheck);
  Vue.component("font-awesome-icon", FontAwesomeIcon);

  new Vue({
    el: "#OpenChatApp",
    store,
    router,
    render: (h) => h(ChatApp),
  });
}

export { initOpenChat };

if (window.location.hostname === "localhost") {
  console.log("Local development mode: auto-initializing OpenChat");
  initOpenChat({
    page_instance_id: 1,
    system_name: "LocalDev",
    course_id: 1,
    is_admin: true,
    course_module_id: 1,
    context_id: 1,
    user_id: "localhost-dev-user",
  });
}