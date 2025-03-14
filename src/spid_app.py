# spid_app.py
import os
from flask import Flask, request, redirect, session
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from spid_config import SP_CONFIG

app = Flask(__name__)
app.secret_key = 'INSERISCI_UN_SECRET_KEY_MOLTO_COMPLESSO'

def init_saml_auth(req):
    # In questo esempio usiamo la configurazione SPID presente in spid_config.py
    from onelogin.saml2.settings import OneLogin_Saml2_Settings
    settings = OneLogin_Saml2_Settings(SP_CONFIG, custom_base_path=os.path.join(os.path.dirname(__file__), 'saml'))
    auth = OneLogin_Saml2_Auth(req, old_settings=settings)
    return auth

def prepare_flask_request(request):
    # Prepara i dati necessari per il parser SAML dalla richiesta Flask
    return {
        'https': 'on' if request.scheme == 'https' else 'off',
        'http_host': request.host,
        'server_port': request.host.split(':')[-1] if ':' in request.host else '80',
        'script_name': request.path,
        'get_data': request.args.copy(),
        'post_data': request.form.copy()
    }

@app.route('/sso')
def sso():
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    # Effettua il redirect al login SPID
    return redirect(auth.login())

@app.route('/acs', methods=['POST'])
def acs():
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    auth.process_response()
    errors = auth.get_errors()
    if errors:
        return "Errori nell'autenticazione: " + ", ".join(errors), 400
    if auth.is_authenticated():
        # Recupera l’identificativo utente; qui possiamo ad esempio usare il NameID
        user_id = auth.get_nameid()
        session['samlUserdata'] = auth.get_attributes()
        session['samlNameId'] = user_id
        # Dopo l'autenticazione, reindirizza alla dashboard Streamlit passando l'identificativo
        return redirect(f"http://localhost:8501/?user={user_id}")
    return 'Autenticazione fallita', 400

if __name__ == '__main__':
    app.run(port=5000, debug=True)
