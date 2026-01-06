<template>
    <div id="container" class="content" role="main">
      <div class="chat-header mb-3 w100">
        <h3 class="d-flex justify-content-betweenx xalign-items-center mb-3">
          <span id="chat-title">Dokumenten-Chat</span>
          <button
            @click="$store.commit('toggleShowSettings', 1)"
            class="btn btn-link settings-icon-button"
            aria-controls="settings-panel"
            :aria-expanded="$store.getters.showSettings.toString()"
            aria-label="Einstellungen öffnen oder schließen"
            title="Einstellungen"
            style="margin-top:0px;"
          >
            <font-awesome-icon class="settings-icon" icon="cog" aria-hidden="true"/>
          </button>
        </h3>
        <div id="intro">
            {{  $store.getters.getPluginSettings.intro }}
        </div> 
        <div id="settings-panel" v-if="$store.getters.showSettings">
          <RAGChatSettings :documents="documents" />
        </div>
      </div>
  
      <ChatUI
        :messages="messages"
        @requestChatResponse="requestDocumentChat"
        aria-labelledby="chat-title"
      />
    </div>
  </template>
  

<script lang="ts">
import Vue from "vue";
import { mapGetters } from 'vuex'
import RAGChatSettings from "./ChatSettings.vue";
import ChatUI from "./ChatUI.vue";
import Communication from "../classes/communication";

export default Vue.extend({
    name: "RAGChat",
    components: {
        RAGChatSettings: RAGChatSettings,
        ChatUI: ChatUI
    },
    data() {
        return {
            messages: [],
            messageId: 0,
            documents: [],
            document_index: [],
            document_filter: [],
            error_msg: '',
        };
    },
    mounted: function () { },
    methods: {
        ...mapGetters({
            //rag_webservice_host: 'getRAGWebserviceHost',
            //pluginSettings: 'getPluginSettings',
        }),
        getNextMessageId: function(){
            this.messageId++;
            return this.messageId;
        },
        requestDocumentChat: async function (message) {
            if(this.$store.getters.getChatModus !== 'document-chat'){
                return;
            }
            console.log('requestDocumentChat');
            console.log('filter', this.updateDocumentFilter())
            
            let _this = this;
            //@ts-ignore
            let new_message = { author: "user", message: message, id: this.getNextMessageId() };
            this.messages.push(new_message);
            Communication.webservice("triggerEvent", {
                cmid: _this.$store.getters.getCMID,
                action: "rag_request",
                value: JSON.stringify(new_message),
            });
            //@ts-ignore
            let message_pos = this.messages.push({ author: "bot", message: "", id: this.getNextMessageId() });

            // default
            const base = new URL(this.$store.getters.getRAGWebserviceHost);
            const url = new URL("llm/query_documents", base);
            let payload = {
                "model": this.model,
                "filter": this.updateDocumentFilter(),
                "prompt": message,
            };
            const apiKey = ""; // Replace with your actual API key

            try {
                // send request
                const response = await fetch(url.href, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        //Authorization: "Bearer " + apiKey,
                    },
                    body: JSON.stringify(payload),
                });
                console.log(response);
                if (!response.ok) {
                    throw new Error("HTTP error! Status:" + response.status);
                }

                // Handle response
                //@ts-ignore
                const reader = response.body != null ? response.body.getReader() : null;
                const decoder = new TextDecoder("utf-8");
                let done = false;

                while (!done) {
                    //@ts-ignore
                    const { value, done: readerDone } = await reader.read();
                    done = readerDone;

                    if (value) {
                        const chunk = decoder.decode(value, { stream: true });
                        let res = "";
                        try {
                            res = JSON.parse(chunk).response;
                        } catch (e) {
                            res = "";
                        }
                        //@ts-ignore
                        _this.messages[message_pos - 1].message = _this.messages[message_pos - 1].message + res;
                    }
                }
                Communication.webservice("triggerEvent", {
                    cmid: _this.$store.getters.getCMID,
                    action: "rag_response",
                    value: JSON.stringify(_this.messages[message_pos - 1]),
                });
            } catch (error) {
                console.error("Error fetching streaming data:", error);
            }
        },
        
        updateDocumentFilter: function () {
            // Expected format: filter = { 'system': ['aple-demo-moodle'], 'course_id': [0], 'activity_longpage': [1,7], }
            // Base filter
            this.document_filter = {
                'system': [ this.$store.getters.getSystemContext.systemName ],
                'courses': [ this.$store.getters.getSystemContext.courseID ],
            }
            // Document-related filter
            for (let i = 0; i < this.documents.length; i++) {
                let doc = this.documents[i];
                console.log('doc ', doc);
                if(this.document_filter['activity_'+doc['activity_type']] == null){
                    this.document_filter['activity_'+doc['activity_type']] = []
                }
                this.document_filter['activity_'+doc['activity_type']].push(doc['activity_id']);
            }
            console.log('resulting filter', this.document_filter)
            return this.document_filter;
        },
    },
});
</script>

<style scoped>
.content {
    border: none;
    max-width: 830px;
    margin: 0 auto;
}

.settings-icon {
    font-size:1.5em; 
    color:#555;
    cursor:pointer;
}

.settings-icon:hover{
    color:#004c97;
}
</style>