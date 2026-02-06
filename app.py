from flask import Flask, request, redirect, abort
from flask import render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, datetime
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "chiave-super-segreta")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///laboratorio.db"
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# ---------------- MODELLI ----------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    ruolo = db.Column(db.String(20))

class Paziente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    cognome = db.Column(db.String(100))
    studio = db.Column(db.String(150))

class Consegna(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False)
    tipo_lavoro = db.Column(db.String(100))
    stato = db.Column(db.String(50))
    note = db.Column(db.Text)
    paziente_id = db.Column(db.Integer, db.ForeignKey("paziente.id"))
    paziente = db.relationship("Paziente")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------- SFONDI ----------------
def get_bg(page="celestino"):
    if page=="stellato":
        return """
        <style>
        body { margin:0; padding:0; overflow:hidden; background: #0b0c2a; position: relative;}
        #stars {position: absolute; top:0; left:0; width:100%; height:100%; z-index:0;}
        .star {position: absolute; width:2px; height:2px; background:white; border-radius:50%; animation: twinkle linear infinite;}
        @keyframes twinkle {0%{opacity:0.1;}50%{opacity:1;}100%{opacity:0.1;}}
        </style>
        <div id="stars"></div>
        <script>
        const numStars=150; const container=document.getElementById("stars");
        for(let i=0;i<numStars;i++){const star=document.createElement('div'); star.className='star';
        star.style.top=Math.random()*100+'%'; star.style.left=Math.random()*100+'%';
        star.style.animationDuration=(Math.random()*3+2)+'s'; container.appendChild(star);}
        </script>
        """
    else:
        return """
        <style>body{margin:0;padding:0;min-height:100vh;background-color:#c0e7ff;}</style>
        """

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET","POST"])
def login():
    html=f"""
    <!doctype html>
    <html lang="it">
    <head><meta charset="utf-8"><title>Login</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/css/bootstrap.min.css" rel="stylesheet">
    {get_bg("celestino")}</head>
    <body>
    <div class="container mt-5" style="max-width:400px; position:relative; z-index:1;">
    <h2 class="text-center mb-4 text-dark">Login Laboratorio</h2>
    <form method="post" class="bg-light text-dark p-4 rounded shadow">
    <div class="mb-3"><input name="username" class="form-control" placeholder="Username" required></div>
    <div class="mb-3"><input type="password" name="password" class="form-control" placeholder="Password" required></div>
    <button class="btn btn-primary w-100">Accedi</button>
    </form></div></body></html>
    """
    if request.method=="POST":
        user=User.query.filter_by(username=request.form["username"]).first()
        if user and check_password_hash(user.password, request.form["password"]):
            login_user(user)
            return redirect("/dashboard")
    return render_template_string(html)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
@login_required
def dashboard():
    html=f"""
    <!doctype html>
    <html lang="it">
    <head><meta charset="utf-8"><title>Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/css/bootstrap.min.css" rel="stylesheet">
    {get_bg('stellato')}</head>
    <body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary mb-4" style="position:relative; z-index:1;">
    <div class="container-fluid">
    <a class="navbar-brand" href="/dashboard">Laboratorio</a>
    <div class="collapse navbar-collapse">
    <ul class="navbar-nav me-auto">
    <li class="nav-item"><a class="nav-link" href="/agenda">Agenda</a></li>
    <li class="nav-item"><a class="nav-link" href="/pazienti">Pazienti</a></li>
    <li class="nav-item"><a class="nav-link" href="/consegne">Consegne</a></li>
    {"<li class='nav-item'><a class='nav-link' href='/utenti'>Utenti</a></li>" if current_user.ruolo=="admin" else ""}
    <li class="nav-item"><a class="nav-link" href="/logout">Logout</a></li>
    </ul></div></div></nav>
    <div class="container" style="position:relative; z-index:1;">
    <h2 class="text-white">Benvenuto, {current_user.username}</h2>
    <p class="text-white">Seleziona un modulo dal menu sopra.</p>
    </div></body></html>
    """
    return render_template_string(html)

# ---------------- PAZIENTI ----------------
@app.route("/pazienti", methods=["GET","POST"])
@login_required
def pazienti():
    if request.method=="POST":
        p=Paziente(nome=request.form["nome"],cognome=request.form["cognome"],studio=request.form["studio"])
        db.session.add(p)
        db.session.commit()
    pazienti=Paziente.query.all()
    html=f"<div class='container mt-4' style='position:relative; z-index:1;'><h2>Pazienti</h2>{get_bg('celestino')}"
    html+="<form method='post' class='row g-3 mb-3 bg-light p-3 rounded'>"
    html+="<div class='col-md-4'><input name='nome' placeholder='Nome' class='form-control'></div>"
    html+="<div class='col-md-4'><input name='cognome' placeholder='Cognome' class='form-control'></div>"
    html+="<div class='col-md-3'><input name='studio' placeholder='Studio' class='form-control'></div>"
    html+="<div class='col-md-1'><button class='btn btn-primary w-100'>Aggiungi</button></div></form>"
    html+="<table class='table table-striped table-bordered'><thead class='table-primary'><tr><th>Nome</th><th>Cognome</th><th>Studio</th><th>Azioni</th></tr></thead><tbody>"
    for p in pazienti:
        html+=f"<tr><td>{p.nome}</td><td>{p.cognome}</td><td>{p.studio}</td>"
        html+=f"<td><a href='/modifica_paziente/{p.id}' class='btn btn-warning btn-sm me-1'>✏️</a>"
        html+=f"<a href='/elimina_paziente/{p.id}' class='btn btn-danger btn-sm'>❌</a></td></tr>"
    html+="</tbody></table><a class='btn btn-secondary' href='/dashboard'>⬅ Torna</a></div>"
    return render_template_string(html)

@app.route("/modifica_paziente/<int:paziente_id>", methods=["GET","POST"])
@login_required
def modifica_paziente(paziente_id):
    paziente=Paziente.query.get_or_404(paziente_id)
    if request.method=="POST":
        paziente.nome=request.form["nome"]
        paziente.cognome=request.form["cognome"]
        paziente.studio=request.form["studio"]
        db.session.commit()
        return redirect("/pazienti")
    html=f"""
    <!doctype html><html lang="it"><head><meta charset="utf-8"><title>Modifica Paziente</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/css/bootstrap.min.css" rel="stylesheet">
    {get_bg('celestino')}</head><body>
    <div class="container mt-4" style='position:relative; z-index:1;'>
    <h2>Modifica Paziente</h2>
    <form method="post" class="bg-light p-3 rounded">
    <div class="mb-3"><input name="nome" value="{paziente.nome}" class="form-control"></div>
    <div class="mb-3"><input name="cognome" value="{paziente.cognome}" class="form-control"></div>
    <div class="mb-3"><input name="studio" value="{paziente.studio}" class="form-control"></div>
    <button class="btn btn-primary">Salva</button></form>
    <a class="btn btn-secondary mt-2" href='/pazienti'>⬅ Torna</a>
    </div></body></html>"""
    return render_template_string(html)

@app.route("/elimina_paziente/<int:paziente_id>", methods=["GET","POST"])
@login_required
def elimina_paziente(paziente_id):
    paziente=Paziente.query.get_or_404(paziente_id)
    if request.method=="POST":
        if request.form.get("conferma")=="si":
            Consegna.query.filter_by(paziente_id=paziente.id).delete()
            db.session.delete(paziente)
            db.session.commit()
        return redirect("/pazienti")
    html=f"""
    <!doctype html><html lang="it"><head><meta charset="utf-8"><title>Conferma Eliminazione</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/css/bootstrap.min.css" rel="stylesheet">
    {get_bg('celestino')}</head><body>
    <div class="container mt-4" style='position:relative; z-index:1;'>
    <h3>Sei sicuro di voler eliminare il paziente <strong>{paziente.nome} {paziente.cognome}</strong>?</h3>
    <form method="post" class="mt-3">
    <button name="conferma" value="si" class="btn btn-danger me-2">Sì</button>
    <button name="conferma" value="no" class="btn btn-secondary">No</button>
    </form></div></body></html>"""
    return render_template_string(html)

# ---------------- CONSEGNE ----------------
@app.route("/consegne", methods=["GET","POST"])
@login_required
def consegne():
    pazienti=Paziente.query.all()
    if request.method=="POST":
        try:
            data_input = request.form["data"]
            data_obj = datetime.strptime(data_input, "%Y-%m-%d").date()
        except ValueError:
            data_obj = date.today()
        c=Consegna(
            data=data_obj,
            tipo_lavoro=request.form["tipo"],
            stato=request.form["stato"],
            note=request.form.get("note"),
            paziente_id=int(request.form["paziente"])
        )
        db.session.add(c)
        db.session.commit()
    consegne=Consegna.query.order_by(Consegna.data).all()
    html=f"<div class='container mt-4' style='position:relative; z-index:1;'><h2>Consegne</h2>{get_bg('celestino')}"
    html+="<form method='post' class='row g-3 mb-3 bg-light p-3 rounded'>"
    html+="<div class='col-md-2'><input type='date' name='data' class='form-control' required></div>"
    html+="<div class='col-md-2'><input name='tipo' placeholder='Lavoro' class='form-control' required></div>"
    html+="<div class='col-md-2'><input name='stato' placeholder='Stato' class='form-control' required></div>"
    html+="<div class='col-md-3'><select name='paziente' class='form-select'>"
    for p in pazienti:
        html+=f"<option value='{p.id}'>{p.nome} {p.cognome}</option>"
    html+="</select></div>"
    html+="<div class='col-md-2'><input name='note' placeholder='Note' class='form-control'></div>"
    html+="<div class='col-md-1'><button class='btn btn-primary w-100'>Aggiungi</button></div></form>"
    html+="<table class='table table-striped table-bordered'><thead class='table-primary'><tr><th>Data</th><th>Paziente</th><th>Studio</th><th>Lavoro</th><th>Stato</th><th>Azioni</th></tr></thead><tbody>"
    for c in consegne:
        html+=f"<tr><td>{c.data}</td><td>{c.paziente.nome} {c.paziente.cognome}</td><td>{c.paziente.studio}</td><td>{c.tipo_lavoro}</td><td>{c.stato}</td>"
        html+=f"<td><a href='/modifica_consegna/{c.id}' class='btn btn-warning btn-sm me-1'>✏️</a>"
        html+=f"<a href='/elimina_consegna/{c.id}' class='btn btn-danger btn-sm'>❌</a></td></tr>"
    html+="</tbody></table><a class='btn btn-secondary' href='/dashboard'>⬅ Torna</a></div>"
    return render_template_string(html)

# ---------------- MODIFICA CONSEGNA ----------------
@app.route("/modifica_consegna/<int:consegna_id>", methods=["GET","POST"])
@login_required
def modifica_consegna(consegna_id):
    consegna = Consegna.query.get_or_404(consegna_id)
    pazienti = Paziente.query.all()
    if request.method=="POST":
        try:
            data_input = request.form["data"]
            consegna.data = datetime.strptime(data_input, "%Y-%m-%d").date()
        except ValueError:
            consegna.data = date.today()
        consegna.tipo_lavoro = request.form["tipo"]
        consegna.stato = request.form["stato"]
        consegna.note = request.form.get("note")
        consegna.paziente_id = int(request.form["paziente"])
        db.session.commit()
        return redirect("/consegne")
    html=f"""
    <!doctype html><html lang="it"><head><meta charset="utf-8"><title>Modifica Consegna</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/css/bootstrap.min.css" rel="stylesheet">
    {get_bg('celestino')}</head><body>
    <div class="container mt-4" style='position:relative; z-index:1;'>
    <h2>Modifica Consegna</h2>
    <form method="post" class="bg-light p-3 rounded">
        <div class="mb-3"><input type="date" name="data" value="{consegna.data}" class="form-control" required></div>
        <div class="mb-3"><input name="tipo" value="{consegna.tipo_lavoro}" class="form-control" required></div>
        <div class="mb-3"><input name="stato" value="{consegna.stato}" class="form-control" required></div>
        <div class="mb-3">
            <select name="paziente" class="form-select">
    """
    for p in pazienti:
        selected="selected" if p.id==consegna.paziente_id else ""
        html+=f"<option value='{p.id}' {selected}>{p.nome} {p.cognome}</option>"
    html+=f"""
            </select>
        </div>
        <div class="mb-3"><textarea name="note" class="form-control" placeholder="Note">{consegna.note or ''}</textarea></div>
        <button class="btn btn-primary">Salva</button>
    </form>
    <a class="btn btn-secondary mt-2" href='/consegne'>⬅ Torna</a>
    </div></body></html>
    """
    return render_template_string(html)

# ---------------- ELIMINA CONSEGNA ----------------
@app.route("/elimina_consegna/<int:consegna_id>", methods=["GET","POST"])
@login_required
def elimina_consegna(consegna_id):
    consegna=Consegna.query.get_or_404(consegna_id)
    if request.method=="POST":
        if request.form.get("conferma")=="si":
            db.session.delete(consegna)
            db.session.commit()
        return redirect("/consegne")
    html=f"""
    <!doctype html><html lang="it"><head><meta charset="utf-8"><title>Conferma Eliminazione</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/css/bootstrap.min.css" rel="stylesheet">
    {get_bg('celestino')}</head><body>
    <div class="container mt-4" style='position:relative; z-index:1;'>
    <h3>Sei sicuro di voler eliminare questa consegna?</h3>
    <form method="post" class="mt-3">
    <button name="conferma" value="si" class="btn btn-danger me-2">Sì</button>
    <button name="conferma" value="no" class="btn btn-secondary">No</button>
    </form></div></body></html>
    """
    return render_template_string(html)

# ---------------- AGENDA ----------------
# ---------------- AGENDA ----------------
@app.route("/agenda")
@login_required
def agenda():
    oggi = date.today()
    consegne = Consegna.query.order_by(Consegna.data.asc()).all()

    html = f"""
    <div class='container mt-4' style='position:relative; z-index:1;'>
        <h2>Agenda</h2>
        {get_bg('celestino')}
        <style>
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #333; padding: 8px; text-align: left; }}
            th {{ background-color: #007bff; color: white; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
        </style>
        <table>
            <thead>
                <tr>
                    <th>Data</th>
                    <th>Paziente</th>
                    <th>Studio</th>
                    <th>Lavoro</th>
                    <th>Stato</th>
                    <th>Note</th>
                    <th>Azioni</th>
                </tr>
            </thead>
            <tbody>
    """

    for c in consegne:
        # Colore evidenziazione
        if c.data < oggi:
            style = "background:#f8d7da"  # rosso chiaro
        elif c.data == oggi:
            style = "background:#fff3cd"  # giallo chiaro
        else:
            style = "background:#d4edda"  # verde chiaro

        html += f"""
            <tr style='{style}'>
                <td>{c.data}</td>
                <td>{c.paziente.nome} {c.paziente.cognome}</td>
                <td>{c.paziente.studio}</td>
                <td>{c.tipo_lavoro}</td>
                <td>{c.stato}</td>
                <td>{c.note or ''}</td>
                <td>
                    <a href='/modifica_consegna/{c.id}' class='btn btn-warning btn-sm me-1'>✏️</a>
                    <a href='/elimina_consegna/{c.id}' class='btn btn-danger btn-sm'>❌</a>
                </td>
            </tr>
        """

    html += """
            </tbody>
        </table>
        <a class='btn btn-secondary mt-3' href='/dashboard'>⬅ Torna</a>
    </div>
    """
    return render_template_string(html)


# ---------------- UTENTI ----------------
@app.route("/utenti", methods=["GET","POST"])
@login_required
def utenti():
    if current_user.ruolo!="admin": abort(403)
    if request.method=="POST":
        username=request.form["username"]
        password=generate_password_hash(request.form["password"])
        ruolo=request.form["ruolo"]
        db.session.add(User(username=username,password=password,ruolo=ruolo))
        db.session.commit()
    users=User.query.all()
    html=f"<div class='container mt-4' style='position:relative; z-index:1;'><h2>Utenti</h2>{get_bg('celestino')}"
    html+="<form method='post' class='row g-3 mb-3 bg-light p-3 rounded'>"
    html+="<div class='col-md-4'><input name='username' placeholder='Username' class='form-control' required></div>"
    html+="<div class='col-md-4'><input type='password' name='password' placeholder='Password' class='form-control' required></div>"
    html+="<div class='col-md-3'><select name='ruolo' class='form-select'><option value='admin'>Admin</option><option value='user'>User</option></select></div>"
    html+="<div class='col-md-1'><button class='btn btn-primary w-100'>Aggiungi</button></div></form>"
    html+="<table class='table table-striped table-bordered'><thead class='table-primary'><tr><th>Username</th><th>Ruolo</th><th>Azioni</th></tr></thead><tbody>"
    for u in users:
        html+=f"<tr><td>{u.username}</td><td>{u.ruolo}</td>"
        html+=f"<td><a href='/modifica_utente/{u.id}' class='btn btn-warning btn-sm me-1'>✏️</a>"
        html+=f"<a href='/elimina_utente/{u.id}' class='btn btn-danger btn-sm'>❌</a></td></tr>"
    html+="</tbody></table><a class='btn btn-secondary' href='/dashboard'>⬅ Torna</a></div>"
    return render_template_string(html)

# ---------------- MODIFICA UTENTE ----------------
@app.route("/modifica_utente/<int:user_id>", methods=["GET","POST"])
@login_required
def modifica_utente(user_id):
    if current_user.ruolo!="admin": abort(403)
    user=User.query.get_or_404(user_id)
    if request.method=="POST":
        user.username=request.form["username"]
        if request.form.get("password"): user.password=generate_password_hash(request.form["password"])
        user.ruolo=request.form["ruolo"]
        db.session.commit()
        return redirect("/utenti")
    html=f"""
    <!doctype html><html lang="it"><head><meta charset="utf-8"><title>Modifica Utente</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/css/bootstrap.min.css" rel="stylesheet">
    {get_bg('celestino')}</head><body>
    <div class="container mt-4" style='position:relative; z-index:1;'>
    <h2>Modifica Utente</h2>
    <form method="post" class="bg-light p-3 rounded">
    <div class="mb-3"><input name="username" value="{user.username}" class="form-control" required></div>
    <div class="mb-3"><input type="password" name="password" placeholder="Nuova Password (lascia vuoto se non vuoi cambiare)" class="form-control"></div>
    <div class="mb-3"><select name="ruolo" class="form-select">
    <option value="admin" {"selected" if user.ruolo=="admin" else ""}>Admin</option>
    <option value="user" {"selected" if user.ruolo=="user" else ""}>User</option></select></div>
    <button class="btn btn-primary">Salva</button></form>
    <a class="btn btn-secondary mt-2" href='/utenti'>⬅ Torna</a>
    </div></body></html>
    """
    return render_template_string(html)

# ---------------- ELIMINA UTENTE ----------------
@app.route("/elimina_utente/<int:user_id>", methods=["GET","POST"])
@login_required
def elimina_utente(user_id):
    if current_user.ruolo!="admin": abort(403)
    user=User.query.get_or_404(user_id)
    if request.method=="POST":
        if request.form.get("conferma")=="si":
            db.session.delete(user)
            db.session.commit()
        return redirect("/utenti")
    html=f"""
    <!doctype html><html lang="it"><head><meta charset="utf-8"><title>Conferma Eliminazione Utente</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/css/bootstrap.min.css" rel="stylesheet">
    {get_bg('celestino')}</head><body>
    <div class="container mt-4" style='position:relative; z-index:1;'>
    <h3>Sei sicuro di voler eliminare l'utente <strong>{user.username}</strong>?</h3>
    <form method="post" class="mt-3">
    <button name="conferma" value="si" class="btn btn-danger me-2">Sì</button>
    <button name="conferma" value="no" class="btn btn-secondary">No</button>
    </form></div></body></html>
    """
    return render_template_string(html)

# ---------------- AVVIO ----------------
if __name__=="__main__":
    with app.app_context():
        db.create_all()
        if not User.query.first():
            admin=User(username="admin", password=generate_password_hash("admin"), ruolo="admin")
            db.session.add(admin)
            db.session.commit()
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0", port=port, debug=True)
