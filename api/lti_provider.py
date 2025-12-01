"""
Minimaler LTI Provider mit Vue.js
Zeigt wie man Vue.js in LTI einbindet - ohne CSS

Moodle: coruse > more > lti external tools > add new provider:
URL: localhost:5000
CONSUMER_KEY = "moodle_key"
SHARED_SECRET = "geheimer_schluessel_123"

"""

from flask import Flask, request, render_template_string
import hashlib
import hmac
import base64
from urllib.parse import quote

app = Flask(__name__)

# Konfiguration
CONSUMER_KEY = "moodle_key"
SHARED_SECRET = "geheimer_schluessel_123"

# Minimales HTML Template mit Vue.js
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LTI mit Vue.js</title>
    
    <!-- Vue.js 3 von CDN -->
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
</head>
<body>
    {% raw %}
    <div id="app">
        <h1>{{ title }}</h1>
        
        <h2>Benutzerdaten</h2>
        <div v-if="userData">
            <p>Name: {{ userData.name }}</p>
            <p>Email: {{ userData.email }}</p>
            <p>Kurs: {{ userData.course }}</p>
        </div>
        
        <h2>Counter Component</h2>
        <p>Count: {{ count }}</p>
        <button @click="increment">+</button>
        <button @click="decrement">-</button>
        <button @click="reset">Reset</button>
        
        <h2>Todo Liste</h2>
        <input v-model="newTodo" @keyup.enter="addTodo" placeholder="Neues Todo">
        <button @click="addTodo">Hinzufügen</button>
        
        <ul>
            <li v-for="(todo, index) in todos" :key="index">
                <input type="checkbox" v-model="todo.done">
                <span :style="{ textDecoration: todo.done ? 'line-through' : 'none' }">
                    {{ todo.text }}
                </span>
                <button @click="removeTodo(index)">Löschen</button>
            </li>
        </ul>
    </div>
    {% endraw %}

    <!-- Daten als JSON in Script-Tag -->
    <script id="lti-data" type="application/json">
        {{ lti_data|tojson }}
    </script>

    <script>
        const { createApp } = Vue;
        
        // Daten aus JSON-Tag laden
        const ltiData = JSON.parse(document.getElementById('lti-data').textContent);
        
        createApp({
            data() {
                return {
                    title: 'LTI mit Vue.js',
                    userData: ltiData.user,
                    count: 0,
                    newTodo: '',
                    todos: []
                }
            },
            methods: {
                increment() {
                    this.count++;
                },
                decrement() {
                    this.count--;
                },
                reset() {
                    this.count = 0;
                },
                addTodo() {
                    if (this.newTodo.trim()) {
                        this.todos.push({
                            text: this.newTodo,
                            done: false
                        });
                        this.newTodo = '';
                    }
                },
                removeTodo(index) {
                    this.todos.splice(index, 1);
                }
            },
            mounted() {
                console.log('Vue App gestartet!');
                console.log('LTI Data:', ltiData);
                console.log('User:', this.userData);
            }
        }).mount('#app');
    </script>
</body>
</html>
"""


def verify_oauth_signature(params, secret):
    """Verifiziert die OAuth 1.0 Signatur"""
    signature = params.get('oauth_signature', '')
    base_string = create_oauth_base_string(params)
    key = quote(secret, safe='') + '&'
    computed_signature = base64.b64encode(
        hmac.new(key.encode('utf-8'), base_string.encode('utf-8'), hashlib.sha1).digest()
    ).decode('utf-8')
    return hmac.compare_digest(signature, computed_signature)


def create_oauth_base_string(params):
    """Erstellt den OAuth Base String"""
    method = request.method
    url = request.url.split('?')[0]
    sorted_params = sorted([(k, v) for k, v in params.items() if k != 'oauth_signature'])
    param_string = '&'.join([f"{quote(str(k), safe='')}={quote(str(v), safe='')}" 
                             for k, v in sorted_params])
    return f"{method}&{quote(url, safe='')}&{quote(param_string, safe='')}"


@app.route('/', methods=['GET'])
def index():
    """Infoseite"""
    return """
    <h1>LTI Provider mit Vue.js</h1>
    <p>Server läuft auf: http://localhost:5000</p>
    <p>Launch URL: http://localhost:5000/launch</p>
    <p>Consumer Key: moodle_key</p>
    <p>Shared Secret: geheimer_schluessel_123</p>
    """


@app.route('/launch', methods=['POST'])
def lti_launch():
    """LTI Launch Endpoint"""
    params = request.form.to_dict()
    
    # OAuth verifizieren
    if not verify_oauth_signature(params, SHARED_SECRET):
        return "Ungültige OAuth-Signatur", 401
    
    if params.get('oauth_consumer_key') != CONSUMER_KEY:
        return "Ungültiger Consumer Key", 401
    
    # Daten extrahieren
    user_name = params.get('lis_person_name_full', 'Unbekannt')
    user_email = params.get('lis_person_contact_email_primary', 'Keine Email')
    context_title = params.get('context_title', 'Unbekannter Kurs')
    
    # Daten als Dictionary strukturieren
    lti_data = {
        'user': {
            'name': user_name,
            'email': user_email,
            'course': context_title
        }
    }
    
    # Template rendern
    return render_template_string(HTML_TEMPLATE, lti_data=lti_data)


if __name__ == '__main__':
    print("=" * 60)
    print("Minimaler LTI Provider mit Vue.js gestartet!")
    print("=" * 60)
    print("Launch URL: http://localhost:5000/launch")
    print("Consumer Key: moodle_key")
    print("Shared Secret: geheimer_schluessel_123")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)