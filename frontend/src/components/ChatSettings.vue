<template>
  <div class="settings mb-3">
    <button
      type="button"
      class="btn btn-link settings-icon"
      @click="$store.commit('toggleShowSettings', 1)"
      aria-label="Einstellungen schließen"
      style="float: right; cursor: pointer; font-size: 1em; color: #555"
    >
      <font-awesome-icon
        class="ml-3 mt-1 settings-icon"
        icon="close"
        aria-hidden="true"
      />
    </button>
    <h3 class="mb-3">Einstellungen</h3>

    <!-- Chat modus -->
    <div class="form-group">
      <h4>Chat-Modus</h4>
      <fieldset>
        <legend class="sr-only">Chat-Modus wählen</legend>
        <label>
          <input
            type="radio"
            value="llm-chat"
            v-model="chatmodus"
            @change="updateChatModus"
          />
          LLM-Chat (Standard)
        </label>
        <br />
        <label>
          <input
            type="radio"
            value="document-chat"
            v-model="chatmodus"
            @change="updateChatModus"
          />
          Dokumenten-Chat
        </label>
        <br />
        <label>
          <input
            type="radio"
            value="agent-chat"
            v-model="chatmodus"
            @change="updateChatModus"
          />
          SRL-Chat als Interview-Agent
        </label>
      </fieldset>
    </div>
    <!-- Instructions -->
    <div class="form-group">
      <h4>Instructionen</h4>
      <label for="intro-text">
        Instruktionen an die Lernenden zur Nutzung des Chats:<br />
      </label>
      <textarea
        class="instruction-text"
        ref="intro-text"
        v-model="intro"
        @change="updateIntro"
      ></textarea>
      <label hidden>
        Prompt-Template:
        <textarea v-model="prompt" @change="updatePrompt"></textarea>
      </label>
    </div>
    <hr />
    <!-- Settings for the document chat (RAG) -->
    <div v-if="chatmodus == 'document-chat'">
      <h4 id="doc-table-caption">Dokumente für Dokumenten-Chat</h4>
      <span v-if="documents.length > 0" class="bold"
        >Ausgewählte Dokumente</span
      >
      <table
        v-if="documents.length > 0"
        class="document-table"
        aria-labelledby="doc-table-caption"
      >
        <thead>
          <tr>
            <th>Auswahl</th>
            <th class="long">Require Completion</th>
            <th>Dokument</th>
            <th>Typ</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(doc, index) in documents" :key="doc.id">
            <td>
              <input type="checkbox" v-model="doc.selected" />
            </td>
            <td class="long">
              <VueMultiselect
                v-model="value[index]"
                :options="options"
                :multiple="true"
                group-values="items"
                group-label="category"
                :group-select="true"
                placeholder="Select ..."
                searchable="false"
                showLabels="false"
                allow-empty="true"
                selectLabel=""
                selectGroupLabel=""
                deselectLabel=""
                deselectGroupLabel=""
                optionHeight="20"
                track-by="name"
                label="name"
              ></VueMultiselect>
            </td>
            <td v-if="doc.url == ''" class="break">{{ doc.filename }}</td>
            <td v-if="doc.url != ''" class="break">
              <a :href="doc.url">{{ doc.filename }}</a>
            </td>
            <td>{{ doc.activity_type }}</td>
            <td>
              <button
                type="button"
                class="btn btn-link delete-icon"
                @click="removeDocument(doc.id)"
                :aria-label="'Dokument' + doc.file.name + 'löschen'"
              >
                <font-awesome-icon icon="trash" aria-hidden="true" />
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <div class="mt-3">
        <RAGupload @document_uploaded="addDocument"></RAGupload>
        <span style="background-color: red" aria-live="assertive">{{
          error_msg
        }}</span>
      </div>
      <div hidden class="mt-3">
        TODO: Ressource aus dem Kurs als Dokument hinzufügen; [todo: page,
        longpage, wiki, forum, assign]
      </div>
    </div>
    <hr />
    <!-- Standard settings for all chat modi -->
    <div class="form-group">
      <h4>Verwendetes Sprachmodel</h4>
      <label for="llmSelect" class="form-label"
        >Wählen Sie ein Sprachmodell aus:</label
      >
      <select
        id="llmSelect"
        class="form-control w50"
        v-model="model"
        @change="updateModel"
      >
        <option disabled value="">-- Bitte wählen --</option>
        <option
          v-for="(m, index) in $store.getters.getLLMModelList"
          :key="m"
          :value="m"
        >
          {{ m }}
        </option>
      </select>
    </div>
  </div>
</template>

<script>
import RAGupload from "./RAGupload.vue";
import Communication from "../classes/communication";
import { mapGetters } from "vuex";
import VueMultiselect from "vue-multiselect";

export default {
  name: "RAGChatSettings",
  components: {
    RAGupload: RAGupload,
    VueMultiselect,
  },
  props: {
    documents: Object,
  },

  data() {
    return {
      value: [],
      options: [
        {
          category: "Enable on section completion",
          items: [
            { name: "KE1: Design Methods" },
            { name: "KE2: Identity" },
            { name: "KE3: Communities" },
            { name: "KE4: Groups" },
            { name: "KE5: Communication" },
            { name: "KE6: Awareness" },
            { name: "KE7: Mobility" },
          ],
        },
      ],
    };
  },
  created: function () {
    this.intro = this.$store.getters.getIntro;
    this.prompt = this.$store.getters.getPromptTemplate;
    this.model = this.$store.getters.getModel;
    this.chatmodus = this.$store.getters.getChatModus;
    console.log("this.chatmodus", this.chatmodus);
    this.loadDocuments();
  },

  methods: {
    async loadDocuments() {
      const response = await Communication.webservice("document_list", {
        cmid: this.$store.getters.getCMID,
      });
      console.log("start document_list");
      const docs = await response;
      console.log("loaded_docs: ", docs);
      for (var i = 0; i < docs.length; i++) {
        console.log(docs[i]);
        this.documents.push({
          id: Math.floor(Math.random() * 10000),
          file: "",
          filename: docs[i].filename,
          url: docs[i].url,
          activity_type: "pdf", //response.activity_type,
          activity_id: "?", // FixMe: response.activity_id,
          document_index: "?", //FixMe: response.document_index, // needed? FixMe
          selected: "selected",
        });
      }
    },

    addDocument: function (response) {
      console.log("handle adddocument", response);
      if (response.error) {
        this.error_msg = response.msg;
        return;
      }
      this.document_index = response.document_index;
      this.documents.push({
        id: Math.floor(Math.random() * 10000),
        file: response.file,
        filename: response.file.name,
        url: "",
        activity_type: response.activity_type,
        activity_id: response.activity_id,
        document_index: response.document_index, // FixMe: needed?
        selected: "selected",
      });
    },
    removeDocument: function (document_id) {
      let _this = this;
      let doc = this.documents.filter((doc) => doc.id == document_id);
      console.log("doccc ", doc[0]);
      Communication.webservice("document_delete", {
        cmid: _this.$store.getters.getCMID,
        filename: doc[0].filename,
      });
      this.documents = this.documents.filter((doc) => doc.id !== document_id);
    },
    updateChatModus: function () {
      this.$store.commit("setChatModus", this.chatmodus);
      this.$store.dispatch("updatePluginSettings");
      this.$router.push(this.chatmodus);
    },
    updateModel: function () {
      this.$store.commit("setModel", this.model);
      this.$store.dispatch("updatePluginSettings");
    },
    updateIntro: function () {
      this.$store.commit("setIntro", this.intro);
      this.$store.dispatch("updatePluginSettings");
    },
    updatePrompt: function () {
      this.$store.commit("setPromptTemplate", this.prompt);
      this.$store.dispatch("updatePluginSettings");
    },
    fetchUploadedFiles: async function (cmid) {
      const response = await fetch(
        M.cfg.wwwroot + "/lib/ajax/service.php?sesskey=" + M.cfg.sesskey,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify([
            {
              methodname: "mod_openchat_list_files",
              args: { cmid },
            },
          ]),
        }
      );

      const result = await response.json();
      return result[0].data || [];
    },
  },

  computed: {
    chatmodus: {
      get() {
        return this.$store.state.pluginSettings.chatmodus;
      },
      set(value) {
        this.$store.commit("setChatModus", value);
      },
    },
    model: {
      get() {
        return this.$store.state.pluginSettings.model;
      },
      set(value) {
        this.$store.commit("setModel", value);
      },
    },
  },
};
</script>
<style scoped>
.settings {
  display: block;
  /*width: 500px;*/
  background-color: #eee;
  padding: 10px 4px 4px 4px;
  border-radius: 3px;
}

.settings h3 {
  font-size: 1.3em;
}

.settings h4 {
  font-size: 1.1em;
}

.settings textarea {
  display: block;
  width: 100%;
  min-height: 40px;
}

.settings textarea .instruction-text {
  min-height: 40px;
}

.document-table {
  display: block;
  width: 99%;
  max-width: 99%;
  border-collapse: collapse;
  margin-top: 10px;
}

.document-table th,
.document-table td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
  line-break: auto;
}

.document-table th.long,
.document-table td.long {
  min-width: 200px;
}

.document-table td .break {
  word-wrap: break-word;
  word-break: break-all;
}

.document-table th {
  background-color: #f4f4f4;
}

.delete-icon {
  color: #555;
  cursor: pointer;
}

.delete-icon:hover {
  color: red;
}

.multiselect__option--selected.multiselect__option--highlight[data-deselect="Selected"] {
  background: #f3f3f3;
  color: unset;
  display: none;
  &:after {
    background: unset;
    color: unset;
  }
}

.multiselect__option--highlight:hover,
.multiselect__option--highlight {
  background: #f3f3f3;
  color: #333;
}
.multiselect__option--highlight:after {
  background: unset;
  color: #333;
}

.multiselect__option:hover span,
.multiselect__element:hover span,
.multiselect__option.multiselect__option--highlight span,
.multiselect__option:hover.multiselect__option--highlight:hover span {
  background: #f3f3f3;
  color: #333;
}
</style>
