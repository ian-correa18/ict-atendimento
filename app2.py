# ICT Sistema de Atendimento - Firebase Edition (app2.py)

from flask import Flask, request, redirect, url_for, session, render_template_string, flash, Response
from datetime import datetime
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash
import csv
import io
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)
app.secret_key = "ALTERAR-ESTA-CHAVE-EM-PRODUCAO"

# ================= CONEXÃO FIREBASE =================
KEY_PATH = Path(__file__).with_name("firebase-key.json")

if not firebase_admin._apps:
    cred = credentials.Certificate(str(KEY_PATH))
    firebase_admin.initialize_app(cred)

db = firestore.client()
# ====================================================

CATS = {"telefonia": ("T", "Telefonia"), "informatica": ("I", "Informática")}
DEFAULT_REASONS = {
    "telefonia": ["Celular corporativo", "Chip", "WhatsApp / 2FA", "Configuração de aparelho", "Aplicativos", "Outro"],
    "informatica": ["Notebook / Desktop", "Software", "Acesso / Conta", "Impressora", "Rede / VPN", "Periféricos", "Outro"]
}
LOGO_URL = "https://www.stellantis.com/content/dam/stellantis-corporate/news/press-releases/2020/november/09112020/Stellantis_logo_white_background.jpg"

STYLE = """
<style>
:root{--bg:#f3f5f7;--card:#fff;--txt:#1f2937;--muted:#667085;--border:#d9e0e7;--navy:#182a46;--blue:#2b5ec7;--teal:#0f766e;--red:#b42318;--green:#18794e}
*{box-sizing:border-box}body{margin:0;font-family:Segoe UI,Arial,sans-serif;background:var(--bg);color:var(--txt)}
.top{background:#fff;border-bottom:1px solid var(--border);box-shadow:0 2px 10px #0000000a}
.topin{max-width:1220px;margin:auto;padding:12px 20px;display:flex;justify-content:space-between;gap:18px;align-items:center}
.brand{display:flex;align-items:center;gap:14px}.brand img{height:42px;max-width:180px;object-fit:contain}.brandtext b{display:block;color:var(--navy)}.brandtext span{font-size:12px;color:var(--muted)}
.fallback{font-weight:900;letter-spacing:5px;color:#233b8b}
.nav{display:flex;gap:14px;flex-wrap:wrap;align-items:center}.nav a{color:var(--navy);text-decoration:none;font-size:14px;font-weight:700}
.wrap{max-width:1220px;margin:auto;padding:26px 18px}.hero{max-width:680px;margin:35px auto;background:#fff;border:1px solid var(--border);border-radius:20px;padding:32px;box-shadow:0 8px 25px #0000000d}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:18px}.g4{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}
.card{background:#fff;border:1px solid var(--border);border-radius:15px;padding:20px;box-shadow:0 6px 20px #0000000a}
.btn{border:0;border-radius:10px;padding:12px 16px;color:#fff;background:var(--navy);font-weight:800;cursor:pointer;text-decoration:none;display:inline-block;text-align:center}
.full{width:100%}.tel{background:var(--teal)}.inf{background:var(--blue)}.danger{background:var(--red)}.good{background:var(--green)}.light{background:#e9eef4;color:#26364a}
h1,h2,h3{margin-top:0}.muted{color:var(--muted)}.small{font-size:13px;color:var(--muted)}.center{text-align:center}
.kpi{font-size:32px;font-weight:900}
.badge{display:inline-block;padding:6px 10px;background:#eef2f6;border-radius:8px;margin-bottom:6px;font-weight:800}
label{display:block;font-weight:800;font-size:14px;margin:10px 0 6px}select,input,textarea{width:100%;padding:10px;border:1px solid #cdd5df;border-radius:8px;font-size:14px;background:#fff}textarea{min-height:75px}
table{width:100%;border-collapse:collapse;background:#fff}th,td{padding:10px;border-bottom:1px solid var(--border);text-align:left;font-size:13px;white-space:nowrap}th{background:#f8fafc}.tbl{overflow:auto}
.row{display:flex;justify-content:space-between;gap:16px;align-items:center}.section{margin-top:26px}.flash{padding:11px 14px;background:#fff4cc;color:#7a4a00;border-radius:10px;margin-bottom:14px}
.userbox{background:#f8fafc;border:1px solid var(--border);border-radius:12px;padding:12px;margin-top:10px}.userbox b{color:var(--navy)}
@media(max-width:800px){.grid,.g4{grid-template-columns:1fr}.topin{align-items:flex-start;flex-direction:column}}
</style>
"""

BASE = """<!doctype html><html lang='pt-br'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>{{title}}</title>""" + STYLE + """</head><body>
<div class='top'><div class='topin'>
<div class='brand'><img src='{{logo_url}}' alt='Stellantis' onerror="this.style.display='none';this.nextElementSibling.style.display='block'"><div class='fallback' style='display:none'>STELLANTIS</div><div class='brandtext'><b>ICT • Atendimento</b><span>Porto Real (Firebase)</span></div></div>
{% if role in ['analista','admin'] %}<div class='nav'><span>👤 {{display_name}}</span><a href='/painel'>Filas</a><a href='/novo_atendimento'>+ Novo Atendimento</a><a href='/dashboard'>Dashboard</a><a href='/historico'>Histórico</a>{% if role=='admin' %}<a href='/admin'>Administração</a>{% endif %}<a href='/sair'>Sair</a></div>{% endif %}
</div></div><div class='wrap'>{% with msgs=get_flashed_messages() %}{% for m in msgs %}<div class='flash'>{{m}}</div>{% endfor %}{% endwith %}{{content|safe}}</div></body></html>"""

def now(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
def today(): return datetime.now().strftime("%Y-%m-%d")

def init_firebase_defaults():
    users_ref = db.collection("usuarios")
    admin_docs = list(users_ref.where("identifiant_corporativo", "==", "ADMIN01").limit(1).stream())
    if not admin_docs:
        users_ref.add({
            "nome": "Administrador Mestre",
            "identifiant_corporativo": "ADMIN01",
            "email_corporativo": "admin.ict@stellantis.com",
            "senha_hash": generate_password_hash("admin123"),
            "role": "admin",
            "ativo": True
        })
    motivos_ref = db.collection("motivos")
    if not list(motivos_ref.limit(1).stream()):
        for cat, itens in DEFAULT_REASONS.items():
            for item in itens:
                motivos_ref.add({"categoria": cat, "nome": item, "ativo": True})

def role(): return session.get("role")
def auth(): return role() in ("analista", "admin")
def page(title, content, **kw):
    return render_template_string(BASE, title=title, content=render_template_string(content, **kw), role=role(), display_name=session.get("nome"), logo_url=LOGO_URL)

def secs(a, b):
    if not a or not b: return None
    try:
        f = "%Y-%m-%d %H:%M:%S"
        return max(0, (datetime.strptime(str(b), f) - datetime.strptime(str(a), f)).total_seconds())
    except Exception: return None

def dur(v):
    if v is None: return "-"
    m = round(v / 60)
    return f"{m} min" if m < 60 else f"{m//60}h {m%60:02d}min"

@app.route("/")
def home():
    return redirect("/painel" if auth() else "/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return page("Login Técnico", """<div class='hero' style='max-width:440px'>
        <h2>Portal Interno ICT</h2><p class='muted'>Acesso via Firebase Cloud.</p>
        <form method='post'>
            <label>E-mail ou Identifiant Corporativo</label>
            <input name='login_ident' required autofocus placeholder='Ex: ADMIN01 ou admin.ict@stellantis.com'>
            <label>Senha</label>
            <input name='senha' type='password' required placeholder='••••••••'>
            <button class='btn full' style='margin-top:16px'>Entrar no Sistema</button>
        </form></div>""")
    
    login_val = request.form.get("login_ident", "").strip()
    senha = request.form.get("senha", "")
    
    users = list(db.collection("usuarios").where("identifiant_corporativo", "==", login_val.upper()).where("ativo", "==", True).limit(1).stream())
    if not users:
        users = list(db.collection("usuarios").where("email_corporativo", "==", login_val.lower()).where("ativo", "==", True).limit(1).stream())

    if users:
        u = users[0].to_dict()
        if check_password_hash(u["senha_hash"], senha):
            session["nome"] = u["nome"]
            session["role"] = u["role"]
            session["identifiant_corporativo"] = u["identifiant_corporativo"]
            return redirect("/painel")

    flash("Credenciais inválidas ou conta inativa.")
    return redirect("/login")

@app.route("/sair")
def sair():
    session.clear()
    return redirect("/login")

@app.route("/novo_atendimento", methods=["GET", "POST"])
def novo_atendimento():
    if not auth(): return redirect("/login")

    if request.method == "GET":
        return page("Registrar Atendimento", """<div class='hero' style='max-width:620px'>
        <h1>Registrar Atendimento</h1>
        <form method='post'>
            <label>Tipo de Atendimento</label>
            <select name='categoria' required>
                <option value='informatica'>💻 Informática</option>
                <option value='telefonia'>📱 Telefonia</option>
            </select>
            <label>E-mail Corporativo do Solicitante</label>
            <input name='email_solicitante' type='email' required placeholder='colaborador@stellantis.com'>
            <label>Identifiant do Solicitante</label>
            <input name='identifiant' required maxlength='30' placeholder='Ex: CD98765' style='text-transform:uppercase'>
            <label>Nome Completo</label>
            <input name='solicitante_nome' required maxlength='100' placeholder='Nome do colaborador'>
            <label>Número do Chamado</label>
            <input name='numero_chamado' maxlength='60' placeholder='Ex: INC0012345 (Opcional)'>
            <button class='btn full good' style='margin-top:20px'>Gerar Senha no Firebase</button>
        </form></div>""")

    cat = request.form.get("categoria")
    nome = request.form.get("solicitante_nome", "").strip()
    ident = request.form.get("identifiant", "").strip().upper()
    email_user = request.form.get("email_solicitante", "").strip().lower()
    chamado = request.form.get("numero_chamado", "").strip().upper()

    d = today()
    contador_ref = db.collection("contadores").document(f"{d}_{cat}")
    contador_doc = contador_ref.get()
    novo_num = 1
    if contador_doc.exists:
        novo_num = contador_doc.to_dict().get("ultimo", 0) + 1
        contador_ref.update({"ultimo": novo_num})
    else:
        contador_ref.set({"ultimo": novo_num, "data": d, "categoria": cat})

    senha = f"{CATS[cat][0]}{novo_num:03d}"
    db.collection("senhas").add({
        "numero": senha,
        "categoria": cat,
        "status": "aguardando",
        "solicitante_nome": nome,
        "identifiant": ident,
        "email_solicitante": email_user,
        "numero_chamado": chamado,
        "aberto_por": session.get("nome"),
        "analista": "",
        "motivo": "",
        "observacao": "",
        "criada_em": now(),
        "chamada_em": "",
        "finalizada_em": "",
        "cancelada_em": ""
    })

    flash(f"Senha {senha} criada com sucesso para {nome}!")
    return redirect("/painel")

@app.route("/painel")
def painel():
    if not auth(): return redirect("/login")
    
    hoje = today()
    senhas_stream = db.collection("senhas").stream()
    
    ag, em, fin = [], [], 0
    for doc in senhas_stream:
        item = doc.to_dict()
        item["id"] = doc.id
        if item.get("criada_em", "").startswith(hoje):
            if item["status"] == "aguardando": ag.append(item)
            elif item["status"] == "em_atendimento": em.append(item)
            elif item["status"] == "finalizado": fin += 1

    ag.sort(key=lambda x: x.get("criada_em", ""))
    em.sort(key=lambda x: x.get("chamada_em", ""))

    motivos = {cat: [] for cat in CATS}
    for m in db.collection("motivos").where("ativo", "==", True).stream():
        m_data = m.to_dict()
        if m_data.get("categoria") in motivos:
            motivos[m_data["categoria"]].append(m_data["nome"])

    f = {"telefonia": [x for x in ag if x["categoria"] == "telefonia"],
         "informatica": [x for x in ag if x["categoria"] == "informatica"]}

    return page("Filas de Atendimento", """<meta http-equiv="refresh" content="4">
    <div style='display:flex;justify-content:space-between;align-items:center'>
        <h1>Painel de Chamadas (Firebase)</h1>
        <div><a class='btn good' href='/novo_atendimento'>+ Abrir Atendimento</a></div>
    </div>
    <div class='grid section'>
    {% for cat in ['telefonia','informatica'] %}<div class='card'><div class='row'><div><h2>{{'📱 Telefonia' if cat=='telefonia' else '💻 Informática'}}</h2><span class='small'>Aguardando</span></div><div class='kpi'>{{f[cat]|length}}</div></div>
    <div style='margin:14px 0'>{% for s in f[cat] %}<div class='userbox'><span class='badge'>{{s.numero}}</span> <b>{{s.solicitante_nome}}</b><br><span class='small'>Identifiant: {{s.identifiant}} | Chamado: {{s.numero_chamado or '-'}}</span></div>{% else %}<span class='small muted'>Nenhuma senha aguardando.</span>{% endfor %}</div>
    <form method='post' action='/chamar/{{cat}}'><button class='btn {{'tel' if cat=='telefonia' else 'inf'}} full' {% if not f[cat] %}disabled{% endif %}>Chamar Próximo</button></form></div>{% endfor %}</div>
    <div class='g4 section'><div class='card'><span class='small'>Telefonia</span><div class='kpi'>{{f.telefonia|length}}</div></div><div class='card'><span class='small'>Informática</span><div class='kpi'>{{f.informatica|length}}</div></div><div class='card'><span class='small'>Em atendimento</span><div class='kpi'>{{em|length}}</div></div><div class='card'><span class='small'>Finalizados hoje</span><div class='kpi'>{{fin}}</div></div></div>
    <h2 class='section'>Atendimentos em Andamento</h2>{% for s in em %}<div class='card' style='margin-bottom:12px'><div class='grid'><div><h2>{{s.numero}} • {{cats[s.categoria][1]}}</h2><div class='userbox'><b>{{s.solicitante_nome}}</b> ({{s.identifiant}})<br><span class='small'>Chamado: {{s.numero_chamado or '-'}}</span></div><p>Atendido por: <b>{{s.analista}}</b></p></div>
    <div>{% if s.analista==analyst %}<form method='post' action='/finalizar/{{s.id}}'><label>Motivo</label><select name='motivo' required><option value=''>Selecione...</option>{% for m in motivos[s.categoria] %}<option>{{m}}</option>{% endfor %}</select><label>Observações Técnicas</label><textarea name='observacao' placeholder='Resolução aplicada...' required></textarea><button class='btn good full' style='margin-top:10px'>Finalizar Atendimento</button></form><form method='post' action='/cancelar/{{s.id}}'><button class='btn danger full' style='margin-top:8px'>Cancelar</button></form>{% else %}<p class='muted'>Em atendimento por {{s.analista}}.</p>{% endif %}</div></div></div>{% else %}<div class='card'><span class='muted'>Nenhum técnico atendendo no momento.</span></div>{% endfor %}""", f=f, em=em, fin=fin, cats=CATS, analyst=session["nome"], motivos=motivos)

@app.post("/chamar/<cat>")
def chamar(cat):
    if not auth(): return redirect("/login")
    hoje = today()
    candidatos = db.collection("senhas").where("categoria", "==", cat).where("status", "==", "aguardando").stream()
    proximos = [doc for doc in candidatos if doc.to_dict().get("criada_em", "").startswith(hoje)]
    proximos.sort(key=lambda d: d.to_dict().get("criada_em", ""))
    
    if proximos:
        db.collection("senhas").document(proximos[0].id).update({
            "status": "em_atendimento",
            "analista": session["nome"],
            "chamada_em": now()
        })
    return redirect("/painel")

@app.post("/finalizar/<doc_id>")
def finalizar(doc_id):
    if not auth(): return redirect("/login")
    db.collection("senhas").document(doc_id).update({
        "status": "finalizado",
        "motivo": request.form.get("motivo"),
        "observacao": request.form.get("observacao"),
        "finalizada_em": now()
    })
    return redirect("/painel")

@app.post("/cancelar/<doc_id>")
def cancelar(doc_id):
    if not auth(): return redirect("/login")
    db.collection("senhas").document(doc_id).update({
        "status": "cancelado",
        "cancelada_em": now()
    })
    return redirect("/painel")

@app.route("/dashboard")
def dashboard():
    if not auth(): return redirect("/login")
    di = request.args.get("data_inicio", today())
    df = request.args.get("data_fim", today())
    
    r = []
    for doc in db.collection("senhas").stream():
        item = doc.to_dict()
        c_dia = item.get("criada_em", "")[:10]
        if di <= c_dia <= df:
            r.append(item)
            
    final = [x for x in r if x.get("status") == "finalizado"]
    es = [secs(x["criada_em"], x["chamada_em"]) for x in r if x.get("chamada_em")]
    es_val = [x for x in es if x is not None]
    ds = [secs(x["chamada_em"], x["finalizada_em"]) for x in final if x.get("finalizada_em")]
    ds_val = [x for x in ds if x is not None]
    
    tel = sum(1 for x in r if x.get("categoria") == "telefonia")
    inf = sum(1 for x in r if x.get("categoria") == "informatica")
    by = {}
    for x in final:
        a = x.get("analista") or "Outro"
        by[a] = by.get(a, 0) + 1
    rank = sorted(by.items(), key=lambda z: (-z[1], z[0]))

    return page("Dashboard", """<h1>Dashboard (Firestore)</h1><form class='card grid' method='get'><div><label>Data inicial</label><input type='date' name='data_inicio' value='{{di}}'></div><div><label>Data final</label><input type='date' name='data_fim' value='{{df}}'></div><button class='btn'>Filtrar</button></form><div class='g4 section'><div class='card'><span class='small'>Total</span><div class='kpi'>{{total}}</div></div><div class='card'><span class='small'>Finalizados</span><div class='kpi'>{{fin}}</div></div><div class='card'><span class='small'>Média de espera</span><div class='kpi' style='font-size:24px'>{{me}}</div></div><div class='card'><span class='small'>Média de atendimento</span><div class='kpi' style='font-size:24px'>{{md}}</div></div></div><div class='grid section'><div class='card'><h2>Por Categoria</h2><p>Telefonia <b style='float:right'>{{tel}}</b></p><p>Informática <b style='float:right'>{{inf}}</b></p></div><div class='card'><h2>Finalizados por Técnico</h2>{% for a,n in rank %}<p>{{a}} <b style='float:right'>{{n}}</b></p>{% else %}<p class='muted'>Nenhum atendimento no período.</p>{% endfor %}</div></div>""", di=di, df=df, total=len(r), fin=len(final), me=dur(sum(es_val)/len(es_val) if es_val else None), md=dur(sum(ds_val)/len(ds_val) if ds_val else None), tel=tel, inf=inf, rank=rank)

@app.route("/historico")
def historico():
    if not auth(): return redirect("/login")
    di = request.args.get("data_inicio", today())
    df = request.args.get("data_fim", today())
    cat = request.args.get("categoria", "")
    termo = request.args.get("termo", "").strip().upper()
    
    rows = []
    for doc in db.collection("senhas").stream():
        x = doc.to_dict()
        c_dia = x.get("criada_em", "")[:10]
        if di <= c_dia <= df:
            if cat and x.get("categoria") != cat: continue
            if termo:
                txt = f"{x.get('solicitante_nome','')} {x.get('identifiant','')} {x.get('numero','')} {x.get('numero_chamado','')}".upper()
                if termo not in txt: continue
            x["espera"] = dur(secs(x.get("criada_em"), x.get("chamada_em")))
            x["duracao"] = dur(secs(x.get("chamada_em"), x.get("finalizada_em")))
            rows.append(x)
            
    rows.sort(key=lambda z: z.get("criada_em", ""), reverse=True)

    return page("Histórico", """<div class='row'><h1>Histórico</h1><a class='btn good' href='/historico/exportar?data_inicio={{di}}&data_fim={{df}}&categoria={{cat}}&termo={{termo}}'>📥 Baixar CSV</a></div>
    <form class='card grid' method='get' style='margin-top:14px'><div><label>Data inicial</label><input type='date' name='data_inicio' value='{{di}}'></div><div><label>Data final</label><input type='date' name='data_fim' value='{{df}}'></div><div><label>Tipo</label><select name='categoria'><option value=''>Todos</option><option value='telefonia' {% if cat=='telefonia' %}selected{% endif %}>Telefonia</option><option value='informatica' {% if cat=='informatica' %}selected{% endif %}>Informática</option></select></div><div><label>Buscar</label><input name='termo' value='{{termo}}' placeholder='Identifiant, nome ou chamado'></div><button class='btn full' style='grid-column:span 2'>Filtrar</button></form>
    <div class='card tbl section'><table><tr><th>Senha</th><th>Solicitante</th><th>Identifiant</th><th>Chamado</th><th>Tipo</th><th>Status</th><th>Técnico</th><th>Retirada</th><th>Duração</th><th>Motivo</th><th>Observação</th></tr>{% for s in rows %}<tr><td><b>{{s.numero}}</b></td><td>{{s.solicitante_nome}}</td><td>{{s.identifiant}}</td><td>{{s.numero_chamado or '-'}}</td><td>{{cats[s.categoria][1]}}</td><td>{{s.status}}</td><td>{{s.analista or '-'}}</td><td>{{s.criada_em}}</td><td>{{s.duracao}}</td><td>{{s.motivo or '-'}}</td><td>{{s.observacao or '-'}}</td></tr>{% else %}<tr><td colspan='11'>Nenhum registro encontrado.</td></tr>{% endfor %}</table></div>""", di=di, df=df, cat=cat, termo=termo, rows=rows, cats=CATS)

@app.route("/historico/exportar")
def exportar_historico():
    if not auth(): return redirect("/login")
    di = request.args.get("data_inicio", today())
    df = request.args.get("data_fim", today())
    cat = request.args.get("categoria", "")
    termo = request.args.get("termo", "").strip().upper()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(["Senha", "Solicitante", "Identifiant", "Chamado", "Categoria", "Status", "Tecnico", "Criado Em", "Finalizado Em", "Motivo", "Observacao"])

    for doc in db.collection("senhas").stream():
        r = doc.to_dict()
        c_dia = r.get("criada_em", "")[:10]
        if di <= c_dia <= df:
            if cat and r.get("categoria") != cat: continue
            if termo:
                txt = f"{r.get('solicitante_nome','')} {r.get('identifiant','')} {r.get('numero','')} {r.get('numero_chamado','')}".upper()
                if termo not in txt: continue
            writer.writerow([r.get("numero"), r.get("solicitante_nome"), r.get("identifiant"), r.get("numero_chamado") or "", CATS.get(r.get("categoria"), ("", r.get("categoria")))[1], r.get("status"), r.get("analista") or "", r.get("criada_em"), r.get("finalizada_em") or "", r.get("motivo") or "", r.get("observacao") or ""])

    output.seek(0)
    return Response("\ufeff" + output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": f"attachment;filename=ict_firebase_{di}_{df}.csv"})

init_firebase_defaults()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)