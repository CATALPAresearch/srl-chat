"""
Testskript für LTI OAuth-Signatur
Simuliert einen LTI Launch Request
"""

import requests
import hashlib
import hmac
import base64
import time
import uuid
from urllib.parse import quote

# Konfiguration
LAUNCH_URL = "http://localhost:5000/lti/launch"
CONSUMER_KEY = "moodle_key"
SHARED_SECRET = "geheimer_schluessel_123"


def generate_oauth_signature(url, params, secret):
    """Generiert OAuth 1.0 Signatur"""
    # Base String erstellen
    method = "POST"
    sorted_params = sorted([(k, v) for k, v in params.items()])
    param_string = '&'.join([f"{quote(str(k), safe='')}={quote(str(v), safe='')}" 
                             for k, v in sorted_params])
    base_string = f"{method}&{quote(url, safe='')}&{quote(param_string, safe='')}"
    
    # Signatur berechnen
    key = quote(secret, safe='') + '&'
    signature = base64.b64encode(
        hmac.new(key.encode('utf-8'), base_string.encode('utf-8'), hashlib.sha1).digest()
    ).decode('utf-8')
    
    return signature


def create_lti_launch_request():
    """Erstellt einen simulierten LTI Launch Request"""
    
    # OAuth Parameter
    timestamp = str(int(time.time()))
    nonce = str(uuid.uuid4())
    
    params = {
        # OAuth Parameter
        'oauth_consumer_key': CONSUMER_KEY,
        'oauth_signature_method': 'HMAC-SHA1',
        'oauth_timestamp': timestamp,
        'oauth_nonce': nonce,
        'oauth_version': '1.0',
        
        # LTI Standard Parameter
        'lti_message_type': 'basic-lti-launch-request',
        'lti_version': 'LTI-1p0',
        'resource_link_id': '12345',
        
        # Benutzer-Informationen
        'user_id': '98765',
        'lis_person_name_full': 'Max Mustermann',
        'lis_person_contact_email_primary': 'max.mustermann@example.com',
        'roles': 'Learner',
        
        # Kontext-Informationen
        'context_id': '456',
        'context_title': 'Mathematik Grundkurs',
        'context_label': 'MATH101',
        'resource_link_title': 'Übungsaufgaben Algebra',
    }
    
    # Signatur generieren
    signature = generate_oauth_signature(LAUNCH_URL, params, SHARED_SECRET)
    params['oauth_signature'] = signature
    
    return params


def test_lti_launch():
    """Testet den LTI Launch"""
    print("=" * 60)
    print("LTI Launch Request Test")
    print("=" * 60)
    print(f"Launch URL: {LAUNCH_URL}")
    print(f"Consumer Key: {CONSUMER_KEY}")
    print()
    
    # Request erstellen
    params = create_lti_launch_request()
    
    print("Parameter:")
    for key, value in sorted(params.items()):
        if key == 'oauth_signature':
            print(f"  {key}: {value[:20]}...")
        else:
            print(f"  {key}: {value}")
    print()
    
    # Request senden
    try:
        print("Sende Request...")
        response = requests.post(LAUNCH_URL, data=params)
        
        print(f"Status Code: {response.status_code}")
        print()
        
        if response.status_code == 200:
            print("✅ Erfolg! Der LTI Launch war erfolgreich.")
            print()
            print("Antwort (erste 500 Zeichen):")
            print(response.text[:500])
            print("...")
        else:
            print("❌ Fehler!")
            print(f"Antwort: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Verbindungsfehler!")
        print("Ist der Flask-Server gestartet? (python app.py)")
    except Exception as e:
        print(f"❌ Fehler: {e}")


if __name__ == '__main__':
    test_lti_launch()