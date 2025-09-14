from flask import Flask, render_template, request, redirect, url_for
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import secrets
import string
import random

app = Flask(__name__)

def generate_secure_code(length=8):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def clean_email_list(email_text):
  if not email_text:
    return []
  
  # Dividir por líneas y limpiar espacios
  emails = [email.strip() for email in email_text.split('\n')]
  # Filtrar líneas vacías
  emails = [email for email in emails if email]
  return emails

def send_emails(api_key, sender_email, emails, codes):
  sg = SendGridAPIClient(api_key)

  errors = []
  successes = []

  for email, code in zip(emails, codes):
    message = Mail(
      from_email=sender_email,
      to_emails=email,
      subject='Tu código de participación único',
      html_content=f'Hola,<br><br>Tu código único para el formulario es: <strong>{code}</strong>'
    )
    try:
      response = sg.send(message)
      if response.status_code >= 200 and response.status_code < 300:
        successes.append(code)
      else:
        errors.append(f"Error al enviar a {email}: {response.body}")
    except Exception as e:
      errors.append(f"Excepción al enviar a {email}: {e}")

  random.shuffle(successes)
  return {'successes': successes, 'errors': errors}

@app.route("/", methods=["GET", "POST"])
def index():
  if request.method == "POST":
    sender_email = request.form.get("sender_email")
    api_key = request.form.get("api_key")
    email_list = request.form.get("email_list")

    if not sender_email:
      return render_template("index.html", error="El correo del remitente es requerido")
    
    if not api_key:
      return render_template("index.html", error="La API Key es requerida")
    
    if not email_list:
      return render_template("index.html", error="La lista de emails es requerida")
    
    emails = clean_email_list(email_list)
    
    if not emails:
      return render_template("index.html", error="No se encontraron emails válidos")

    return redirect(url_for("send",
                            sender_email=sender_email,
                            api_key=api_key,
                            emails=','.join(emails)))
  
  return render_template("index.html")

@app.route("/enviar")
def send():
  sender_email = request.args.get("sender_email")
  api_key = request.args.get("api_key")
  emails_str = request.args.get("emails")
  
  if not sender_email or not api_key or not emails_str:
    return redirect(url_for("index"))
  
  emails = emails_str.split(',')
  
  codes = [generate_secure_code() for _ in emails]

  result = send_emails(api_key, sender_email, emails, codes)
  successes = result['successes']
  errors = result['errors']
  sent_count = len(successes)

  print(result)

  return render_template("result.html",
                        sent_count=sent_count,
                        codes=successes,
                        total_emails=len(emails),
                        errors=errors)

@app.route("/acerca-de")
def about():
  return render_template("about.html")
