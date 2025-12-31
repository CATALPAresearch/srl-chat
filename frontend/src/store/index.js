import Vue from "vue";
import Vuex from "vuex";
import communication from "../classes/communication";
import moodleAjax from 'core/ajax';
import moodleStorage from 'core/localstorage';


Vue.use(Vuex);

export const store = new Vuex.Store({
  state: {
    // system context
    systemName: null,
    courseID: null,
    courseModuleID: null,
    pageInstanceId: null,
    isAdmin: false,
    showSettings: false,
    strings: {},
    llmModelList: [],

    // user context
    user: {
      userId: null,
    },
    informedConsentAgreement: false,
    

    // plugin context
    pluginSettings: {
      intro: null,
      hostname: null,
      model: null,
      prompttemplate: null,
      chatmodus: null,
      //
      llmhostname: null,
      llmenabled: null,
      raghostname: null,
      ragenabled: null,
      agenthostname: null,
      agentenabled: null,
    },
  },
  mutations: {
    setDocuments: function (state, docs) {
      state.documents = docs;
    },
    setSystemContext: function (state, arr) {
      state.systemName = arr['systemName'];
      state.courseID = arr['courseID'];
    },
    toggleShowSettings: function (state, id) {
      state.showSettings = !state.showSettings;
    },
    setCourseModuleID: function (state, id) {
      state.courseModuleID = parseInt(id);
    },
    setPluginSettings: function (state, settings) {
      //Object.assign(state.pluginSettings, settings); 

      // Set local settings of the opchchat instance
      //state.courseModuleID = settings.courseModuleID;
      state.pluginSettings.intro = settings.intro;
      state.pluginSettings.model = settings.model;
      state.pluginSettings.prompttemplate = settings.prompttemplate;
      state.pluginSettings.chatmodus = settings.chatmodus;

      // Set global openchat settings
      state.pluginSettings.hostname = settings.llm.llmhostname;
      state.pluginSettings.llmhostname = settings.llm.llmhostname;
      state.pluginSettings.llmenabled = settings.llm.llmenabled;
      state.pluginSettings.raghostname = settings.rag.raghostname;
      state.pluginSettings.ragenabled = settings.llm.ragenabled;
      state.pluginSettings.agenthostname = settings.rag.agenthostname;
      state.pluginSettings.agentenabled = settings.llm.agentenabled;
      
      this.dispatch("loadModelNames");
      //console.log('storr', state.getters.pluginSettings.model)
    },
    setIntro(state, intro) {
      state.pluginSettings.intro = intro;
    },
    setPromptTemplate(state, name) {
      state.pluginSettings.prompttemplate = name;
    },
    setLLMModelList(state, list) {
      state.llmModelList = list
    },
    setModel(state, name) {
      state.pluginSettings.model = name;
    },
    setPageInstanceId(state, name) {
      state.pageInstanceId = name;
    },
    setInformedConsentAgreement: function (state, value) {
      state.informedConsentAgreement = value;
      this.dispatch("updatePreference");
    },
    setAdmin: function (state, value) {
      state.isAdmin = value;
    },
    setChatModus: function (state, value) {
      state.pluginSettings.chatmodus = value;
    },
    setStrings(state, strings) {
			state.strings = strings;
		},
  },
  getters: {
    getSystemContext: function (state) {
      return {
        systemName: state.systemName,
        courseID: state.courseID
      };
    },
    showSettings: function (state) {
      return state.showSettings;
    },
    getIsAdmin: function (state) {
      return state.isAdmin;
    },
    getChatModus: function (state) {
      return state.pluginSettings.chatmodus;
    },
    getCMID: function (state) {
      return state.courseModuleID;
    },
    getPluginSettings: function (state) {
      return state.pluginSettings;
    },
    getHostname: function (state) {
      return state.pluginSettings.llmhostname;
    },
    getRAGWebserviceHost: function (state) {
      return state.pluginSettings.raghostname
    },
    getLLMModelList(state) {
      return state.llmModelList;
    },
    getModel: function (state) {
      return state.pluginSettings.model;
    },
    getPromptTemplate: function (state) {
      return state.pluginSettings.prompttemplate
    },
    getIntro(state) {
      return state.pluginSettings.intro;
    },
    getCourseModuleId: function (state) {
      return parseInt(state.courseModuleId);
    },
    getPageInstanceId: function (state) {
      return state.pageInstanceId;
    },
    getInformedConsentAgreement: function (state) {
      return state.informedConsentAgreement;
    },
    getUser: function(state){
      return state.user.userId;
    }
  },
  actions: {
    loadPluginSettings: async function (context) {
      try {
        const cmid = context.getters.getCMID;
        if (!cmid){
          throw new Error('cmid undefined at store > actions > loadPluginSettings.');
        }
        const req = await communication.webservice("load_settings", {
          cmid: cmid,
        });
        if (req.success) {
          const settings = JSON.parse(req.data);
          context.commit('setPluginSettings', settings);
          console.log("@store: loadPluginSettings: ", settings);
          
        } else {
          console.log('@store: loadPluginSettings without success: ', req);
        }
      } catch (error) {
        console.error('msg', error, "@store: Failed to load plugin settings. ");
        throw error;
      }
    },
    updatePluginSettings: async function (context) {
      try {
        const cmid = context.getters.getCMID
        if (!cmid){
          throw new Error('cmid undefined at store > actions > updatePluginSettings: ' + cmid);
        }
        const response = await communication.webservice("update_settings", {
          cmid: cmid,
          settings: JSON.stringify(context.getters.getPluginSettings)
        });

        if (!response.success) {
          console.error(response);
          throw new Error("@store: Failed to update plugin settings. Webservice return ressult. ");
        } else {
          console.log('Stored settings', context.getters.getPluginSettings)
        }

      } catch (error) {
        console.error(error);
        throw new Error("@store: Failed to update plugin settings. Webservice not reachable. ");
      }
    },
    /**
     * Fetches the i18n data for the current language.
     *
     * @param context
     * @returns {Promise<void>}
     */
    async loadComponentStrings(context) {
      const html = document.getElementsByTagName('html');
      const lang = html[0].getAttribute('lang').replace(/-/g, '_');
      const cacheKey = 'mod_openchat/strings/' + lang;
      const cachedStrings = moodleStorage.get(cacheKey);
      if (cachedStrings) {
        context.commit('setStrings', JSON.parse(cachedStrings));
      } else {
        const request = {
          methodname: 'core_get_component_strings',
          args: {
            'component': 'mod_openchat',
            lang,
          },
        };
        const loadedStrings = await moodleAjax.call([request])[0];
        let strings = {};
        loadedStrings.forEach((s) => {
          strings[s.stringid] = s.string;
        });
        context.commit('setStrings', strings);
        moodleStorage.set(cacheKey, JSON.stringify(strings));
      }
    },
    loadPreference: async function (context) {
      try {
        const req = await communication.webservice("preference", {
          preference: 'accepted-informed-consent',
          preference_value: 'none'
        });
        if (req.success) {
          console.log('pref', req.preference)
          context.informedConsentAgreement = req.preference;
          context.commit('setInformedConsentAgreement', req.preference);
        } else {
          console.log('loadPluginpreference', req);
        }
      } catch (error) {
        console.error(error);
        throw new Error("@store: Failed to load plugin preference. ");
      }
    },
    updatePreference: async function (context) {
      try {
        const req = await communication.webservice("preference", {
          preference: 'accepted-informed-consent',
          preference_value: context.getters.getInformedConsentAgreement,
        });
        if (req.success) {
          console.log('loadPluginpreference done', req);//context.commit('setInformedConsentAgreement', JSON.parse(req.preference));
        } else {
          console.log('loadPluginpreference failed', req);
        }
      } catch (error) {
        console.error(error);
        throw new Error("@store: Failed to load plugin preference. ");
      }
    },
    loadModelNames: async function (context) {
      const base = new URL(context.getters.getPluginSettings.hostname);
      const url = new URL('./api/tags', base);
      console.log('setLLMModelList', url)
      const response = await fetch(url.href); // or your base_url
      const data = await response.json();
      console.log('Availab. models', data.models)
      let models = data.models.map(m => m.name);
      context.commit('setLLMModelList', models);
    },
    loadRAGDocuments: async function (context) {
      // Loads documents already indexed for RAG
      const sc = context.getters.getSystemContext;
      const payload = {
        system: sc.systemName,
        course_id: sc.courseID
      };
      const base = new URL(this.getters.getRAGWebserviceHost);
      const url = new URL('./documents/documents_by_course', base);
      let response = await fetch(url.href, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          //Authorization: "Bearer " + apiKey,
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        console.error("Failed to fetch models:", response.statusText);
        return;
      }
      let data = await response.json();

      if (data.success) {
        console.log('rag do', data.documents)
        context.commit('setDocuments', data.documents);
      }

    },
    /*
    loadRAGModelNames: async function(context) {
      let path = "llm/models/list";
      let response = await fetch(this.getters.getRAGWebserviceHost + path, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          //Authorization: "Bearer " + apiKey,
        },
      });

      if (!response.ok) {
        console.error("Failed to fetch models:", response.statusText);
        return;
      }
  
      let data = await response.json();

      if (data.success) {
        context.commit('setLLMModelList', data.data);
      }

    },*/
  },
  modules: {},
});
