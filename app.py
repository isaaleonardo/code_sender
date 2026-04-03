from flask import Flask, render_template, request, redirect, url_for
import requests
import secrets
import string
import random
import os

app = Flask(__name__)

def generate_secure_code(length=8):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def clean_email_list(email_text):
    if not email_text:
        return []
    
    # Reemplazar comas por saltos de línea para manejar ambos formatos
    email_text = email_text.replace(',', '\n')
    # Dividir por líneas y limpiar espacios
    emails = [email.strip() for email in email_text.split('\n')]
    # Filtrar líneas vacías y duplicados manteniendo orden
    seen = set()
    emails = [x for x in emails if x and not (x in seen or seen.add(x))]
    return emails

def send_emails(api_key, domain, sender_email, emails, codes):
    api_key = api_key.strip()
    domain = domain.strip()
    sender_email = sender_email.strip()
    
    # Mailgun API URL
    url = f"https://api.mailgun.net/v3/{domain}/messages"
    auth = ("api", api_key)

    errors = []
    successes = []

    # Cargar el template una sola vez fuera del bucle
    try:
        with open('email_template/index.html', 'r', encoding='utf-8') as file:
            html_template = file.read()
    except Exception as e:
        return {'successes': [], 'errors': [f"Error al cargar el template: {e}"]}

    for email, code in zip(emails, codes):
        html_customed = html_template.format(code=code)

        data = {
            "from": sender_email,
            "to": email,
            "subject": "Tu código de participación único",
            "html": html_customed
        }
        
        try:
            response = requests.post(url, auth=auth, data=data)
            if response.status_code == 200:
                successes.append(code)
            else:
                errors.append(f"Error al enviar a {email}: Status {response.status_code} - {response.text}")
        except Exception as e:
            errors.append(f"Error al enviar a {email}: {e}")

    random.shuffle(successes)
    return {'successes': successes, 'errors': errors}

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        print("DEBUG: Processing POST request in / route (Mailgun V3)")
        sender_email = request.form.get("sender_email")
        api_key = request.form.get("api_key")
        domain = request.form.get("domain")
        email_list = request.form.get("email_list")

        if not sender_email:
            return render_template("index.html", error="El correo del remitente es requerido")
        
        if not api_key:
            return render_template("index.html", error="La API Key es requerida")
        
        if not domain:
            return render_template("index.html", error="El dominio de Mailgun es requerido")
        
        if not email_list:
            return render_template("index.html", error="La lista de emails es requerida")
        
        emails = clean_email_list(email_list)
        
        if not emails:
            return render_template("index.html", error="No se encontraron emails válidos")

        codes = [generate_secure_code() for _ in emails]
        result = send_emails(api_key, domain, sender_email, emails, codes)
        
        successes = result['successes']
        errors = result['errors']
        sent_count = len(successes)

        return render_template("result.html",
                              sent_count=sent_count,
                              codes=successes,
                              total_emails=len(emails),
                              errors=errors)
    
    return render_template("index.html")

@app.route("/acerca-de")
def about():
    return render_template("about.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
