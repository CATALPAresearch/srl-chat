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
  faArrowUp,
  faCommentDots,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";

library.add(
  faCopy,
  faCog,
  faThumbsDown,
  faThumbsUp,
  faCheck,
  faSpinner,
  faArrowUp,
  faCommentDots,
);
Vue.component("font-awesome-icon", FontAwesomeIcon);

// Set API host: prefer SRL_CONFIG.apiBaseUrl, then current origin
const _apiBase =
  (window.SRL_CONFIG && window.SRL_CONFIG.apiBaseUrl) || window.location.origin;
store.commit("setApiHost", _apiBase);

// Assign user ID: prefer SRL_CONFIG, then URL param ?userid=, then persisted localStorage ID, then fresh random
const _configUserId = window.SRL_CONFIG && window.SRL_CONFIG.userId;
const _urlUserId = new URLSearchParams(window.location.search).get("userid");
const _persistedUserId = localStorage.getItem("srl_userid");
const _userId =
  _configUserId || _urlUserId || _persistedUserId || "user_" + Date.now();
// Persist so the same user is restored after close/reopen (skip for config/URL-provided IDs)
if (!_configUserId && !_urlUserId) {
  localStorage.setItem("srl_userid", _userId);
}
store.commit("setUser", _userId);

new Vue({
  el: "#app",
  store,
  router,
  render: (h) => h(ChatApp),
});
