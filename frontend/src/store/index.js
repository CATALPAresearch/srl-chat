const IS_LTI = window.SRL_CLIENT === "lti";

import Vue from "vue";
import Vuex from "vuex";
import communication from "../classes/communication";

let moodleAjax = null;
let moodleStorage = null;

if (!IS_LTI) {
  try {
    moodleAjax = require("core/ajax");
    moodleStorage = require("core/localstorage");
  } catch (e) {
    console.warn("[Store] Moodle APIs not available:", e);
  }
}

Vue.use(Vuex);

export const store = new Vuex.Store({
  state: {
    systemName: null,
    courseID: null,
    courseModuleID: null,
    pageInstanceId: null,
    contextID: null,
    isAdmin: false,
    showSettings: false,
    strings: {},
    llmModelList: [],
    user: {
      userId: null,
    },
    informedConsentAgreement: false,
    pluginSettings: {
      intro: null,
      hostname: null,
      model: null,
      prompttemplate: null,
      chatmodus: "agent",
      llmhostname: null,
      llmenabled: null,
      raghostname: null,
      ragenabled: null,
      agenthostname: null,
      agentenabled: null,
    },
  },

  mutations: {
    setDocuments(state, docs) {
      state.documents = docs;
    },
    setSystemContext(state, arr) {
      state.systemName = arr.systemName;
      state.courseID = arr.courseID;
    },
    toggleShowSettings(state) {
      state.showSettings = !state.showSettings;
    },
    setCourseModuleID(state, id) {
      state.courseModuleID = parseInt(id);
    },
    setContextID(state, id) {
      state.contextID = id;
    },
    setUserId(state, id) {
      state.user.userId = id;
    },
    setPluginSettings(state, settings) {
      state.pluginSettings.intro =
        settings.intro !== undefined ? settings.intro : null;
      state.pluginSettings.model =
        settings.model !== undefined ? settings.model : null;
      state.pluginSettings.prompttemplate =
        settings.prompttemplate !== undefined ? settings.prompttemplate : null;
      state.pluginSettings.chatmodus =
        settings.chatmodus || state.pluginSettings.chatmodus || "agent";
      if (settings.llm) {
        state.pluginSettings.hostname = settings.llm.llmhostname;
        state.pluginSettings.llmhostname = settings.llm.llmhostname;
        state.pluginSettings.llmenabled = settings.llm.llmenabled;
      }
      if (settings.rag) {
        state.pluginSettings.raghostname = settings.rag.raghostname;
        state.pluginSettings.ragenabled = settings.rag.ragenabled;
        state.pluginSettings.agenthostname = settings.rag.agenthostname;
        state.pluginSettings.agentenabled = settings.rag.agentenabled;
      }
    },
    setIntro(state, intro) {
      state.pluginSettings.intro = intro;
    },
    setPromptTemplate(state, name) {
      state.pluginSettings.prompttemplate = name;
    },
    setLLMModelList(state, list) {
      state.llmModelList = list;
    },
    setModel(state, name) {
      state.pluginSettings.model = name;
    },
    setPageInstanceId(state, id) {
      state.pageInstanceId = id;
    },
    setInformedConsentAgreement(state, value) {
      state.informedConsentAgreement = value;
    },
    setAdmin(state, value) {
      state.isAdmin = value;
    },
    setChatModus(state, value) {
      state.pluginSettings.chatmodus = value || "agent";
    },
    setStrings(state, strings) {
      state.strings = strings;
    },
  },

  getters: {
    getSystemContext(state) {
      return { systemName: state.systemName, courseID: state.courseID };
    },
    showSettings(state) {
      return state.showSettings;
    },
    getIsAdmin(state) {
      return state.isAdmin;
    },
    getChatModus(state) {
      return state.pluginSettings.chatmodus;
    },
    getCMID(state) {
      return state.courseModuleID;
    },
    getPluginSettings(state) {
      return state.pluginSettings;
    },
    getHostname(state) {
      return state.pluginSettings.llmhostname;
    },
    getRAGWebserviceHost(state) {
      return state.pluginSettings.raghostname;
    },
    getLLMModelList(state) {
      return state.llmModelList;
    },
    getModel(state) {
      return state.pluginSettings.model;
    },
    getPromptTemplate(state) {
      return state.pluginSettings.prompttemplate;
    },
    getIntro(state) {
      return state.pluginSettings.intro;
    },
    getPageInstanceId(state) {
      return state.pageInstanceId;
    },
    getInformedConsentAgreement(state) {
      return state.informedConsentAgreement;
    },
    getUser(state) {
      return state.user.userId;
    },
  },

  actions: {
    async loadPluginSettings(context) {
      const cmid = context.getters.getCMID;
      if (!cmid) {
        if (IS_LTI) {
          console.log("[LTI] Skipping loadPluginSettings");
          return;
        }
        throw new Error("cmid undefined at loadPluginSettings");
      }
      const req = await communication.webservice("load_settings", { cmid });
      if (req && req.success) {
        context.commit("setPluginSettings", JSON.parse(req.data));
      }
    },
    async updatePluginSettings(context) {
      if (IS_LTI) {
        console.log("[LTI] Skipping updatePluginSettings");
        return;
      }
      const cmid = context.getters.getCMID;
      if (!cmid) throw new Error("cmid undefined at updatePluginSettings");
      await communication.webservice("update_settings", {
        cmid,
        settings: JSON.stringify(context.getters.getPluginSettings),
      });
    },
    async loadComponentStrings(context) {
      if (IS_LTI || !moodleAjax || !moodleStorage) {
        console.log("[LTI] Skipping Moodle i18n");
        return;
      }
      const html = document.documentElement;
      const lang = html.getAttribute("lang").replace(/-/g, "_");
      const cacheKey = "mod_openchat/strings/" + lang;
      const cached = moodleStorage.get(cacheKey);
      if (cached) {
        context.commit("setStrings", JSON.parse(cached));
        return;
      }
      const request = {
        methodname: "core_get_component_strings",
        args: { component: "mod_openchat", lang },
      };
      const loaded = await moodleAjax.call([request])[0];
      const strings = {};
      loaded.forEach((s) => (strings[s.stringid] = s.string));
      context.commit("setStrings", strings);
      moodleStorage.set(cacheKey, JSON.stringify(strings));
    },
    async loadModelNames(context) {
      const host = context.getters.getHostname;
      if (!host) return;
      const base = new URL(host);
      const url = new URL("./api/tags", base);
      const response = await fetch(url.href);
      const data = await response.json();
      context.commit("setLLMModelList", (data.models || []).map((m) => m.name));
    },
    async loadRAGDocuments(context) {
      const host = context.getters.getRAGWebserviceHost;
      if (!host) return;
      const payload = {
        system: context.state.systemName,
        course_id: context.state.courseID,
      };
      const response = await fetch(
        new URL("./documents/documents_by_course", host),
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        }
      );
      const data = await response.json();
      if (data && data.success) {
        context.commit("setDocuments", data.documents);
      }
    },
  },

  modules: {},
});