<template>
    <div id="container" class="content" role="main">
        <div class="chat-header mb-3 w100">
            <h3 class="d-flex justify-content-betweenx xalign-items-center mb-3">
                <span id="chat-title">Agent-Chat</span>
                <button @click="$store.commit('toggleShowSettings', 1)" class="btn btn-link settings-icon-button"
                    aria-controls="settings-panel" :aria-expanded="$store.getters.showSettings.toString()"
                    aria-label="Einstellungen öffnen oder schließen" title="Einstellungen" style="margin-top:0px;">
                    <font-awesome-icon class="settings-icon" icon="cog" aria-hidden="true" />
                </button>
            </h3>
            <div id="intro">
                {{ $store.getters.getPluginSettings.intro }}
            </div>
            <ChatSettings v-if="$store.getters.showSettings" :documents="[]" />
        </div>

        <button v-if="!chatStarted" @click="startChat" class="btn btn-primary start-btn">
            Start Chat
        </button>
        <ChatUI :messages="messages" @requestChatResponse="requestAgentChat" aria-labelledby="chat-title" />
    </div>
</template>

<script lang="ts">
import axios from "axios";
import Vue from "vue";
//import { mapGetters } from 'vuex'
import ChatSettings from "./ChatSettings.vue";
import ChatUI from "./ChatUI.vue";
import Communication from "../classes/communication";


export default Vue.extend({
    name: "AgentChat",
    components: {
        ChatSettings: ChatSettings,
        ChatUI: ChatUI
    },
    data() {
        return {
            messages: [],
            messageId: 0,
            error_msg: '',
            is_loading: false,
            host: 'http://localhost:5000',
            chatStarted: false,
            userInput: "",
        };
    },

    methods: {
        getNextMessageId: function () {
            this.messageId++;
            return this.messageId;
        },

        startChat: async function () {
            console.log('Started Chat');
            let _this = this;
            // curl -X POST http://localhost:5000/startConversation -H "Content-Type: application/json" -d '{ "language": "en", "client": "discord", "userid": "none"}'
            await axios.post(
                this.host + "/startConversation",
                { language: "en", client: "discord", userid: this.$store.getters.getUser }
            ).then(response => {
                _this.is_loading = false;
                console.log('/startConversation: ', response);
                _this.messages.push({
                    message: response.data || "Chat started!",
                    author: 'bot',
                    id: _this.getNextMessageId()
                });
                _this.chatStarted = true;
            }).catch(error => {
                _this.is_loading = false;
                console.error("Error starting chat:", error);
            });
        },


        requestAgentChat: async function (message) {
            if (this.$store.getters.getChatModus !== 'agent-chat') {
                return;
            }

            this.is_loading = true;

            //@ts-ignore
            let new_message = { author: "user", message: message, id: this.getNextMessageId() };
            this.messages.push(new_message);
            Communication.webservice("triggerEvent", {
                cmid: this.$store.getters.getCMID,
                action: "agent_request",
                value: JSON.stringify(new_message),
            });
            
            // TODO: let admin define the url of the agent webservice
            //const base = new URL(this.$store.getters.getRAGWebserviceHost);

            await axios.post(
                this.host + "/reply", {
                message: message,
                client: "discord",
                userid: this.$store.getters.getUser,
            }).then(response => {
                this.is_loading = false;
                console.log('/reply: ', response);
                new_message = { author: "bot", message: response.data, id: this.getNextMessageId() };
                this.messages.push(new_message);
                this.wait_video_generation = false
            }).catch(error => {
                this.is_loading = false;
                console.error("Error sending message:", error);
                this.messages.push({
                    message: "Error: Unable to get a response.",
                    author: "bot",
                    id: this.getNextMessageId()
                });
            });
        },
    },
});
</script>



<style scoped>
.sr-only {
    position: absolute;
    left: -9999px;
    width: 1px;
    height: 1px;
    overflow: hidden;
}

.chat-widget {
    max-width: 400px;
    margin: auto;
    font-family: Arial, sans-serif;
}


.chat-container {
    border: 1px solid #ccc;
    padding: 10px;
    border-radius: 5px;
    background: #f9f9f9;
}

.messages {
    max-height: 300px;
    overflow-y: auto;
    padding: 10px;
    display: flex;
    flex-direction: column;
}

.user-message {
    align-self: flex-end;
    background-color: #007bff;
    color: white;
    padding: 8px;
    border-radius: 10px;
    margin: 5px;
}

.server-message {
    align-self: flex-start;
    background-color: #e0e0e0;
    padding: 8px;
    border-radius: 10px;
    margin: 5px;
}

.chat-input {
    display: flex;
    margin-top: 10px;
}

.chat-input input {
    flex-grow: 1;
    padding: 8px;
    border: 1px solid #ccc;
    border-radius: 5px;
}

.chat-input button {
    padding: 8px 15px;
    margin-left: 5px;
    border: none;
    background-color: #28a745;
    color: white;
    cursor: pointer;
}
</style>
