import "bootstrap/dist/css/bootstrap.min.css";
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
  faSpinner,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";

library.add(faCopy, faCog, faThumbsDown, faThumbsUp, faCheck, faSpinner);
Vue.component("font-awesome-icon", FontAwesomeIcon);

// Assign a default user ID for standalone usage
store.commit("setUser", "user_" + Date.now());

new Vue({
  el: "#app",
  store,
  router,
  render: (h) => h(ChatApp),
});
