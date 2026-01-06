import ajax from 'core/ajax';

const IS_LTI = window.location !== window.parent.location;

export default class Communication {

    /* ---------------- Moodle / OpenChat ---------------- */
    static webservice(method, param = {}) {
        return new Promise((resolve, reject) => {
            ajax.call([{
                methodname: "mod_openchat_" + method,
                args: param,
                timeout: 3000,
                done: resolve,
                fail: reject
            }]);
        });
    }

    /* ---------------- SRL Agent (LTI) ---------------- */
    static async startConversation({ language = "de", userid }) {
        if (!IS_LTI) return;

        const response = await fetch("/startConversation", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                language,
                client: "lti",
                userid
            })
        });

        if (!response.ok) {
            throw new Error("Failed to start SRL conversation");
        }

        return response.json();
    }

    static async sendMessage({ userid, message }) {
        if (!IS_LTI) return;

        const response = await fetch("/reply", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message,
                client: "lti",
                userid
            })
        });

        if (!response.ok) {
            throw new Error("Failed to send message");
        }

        return response.json();
    }

    static async resetConversation({ userid }) {
        return this.sendMessage({ userid, message: "!deleteall" });
    }
}
