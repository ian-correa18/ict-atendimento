# ICT Sistema de Atendimento - versão 3.6 (Corrigida)

from flask import Flask, request, redirect, url_for, session, render_template_string, flash
import sqlite3
from datetime import datetime
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "ALTERAR-ESTA-CHAVE-EM-PRODUCAO"
DB = Path(__file__).with_name("senhas.db")

CATS = {"telefonia": ("T", "Telefonia"), "informatica": ("I", "Informática")}
DEFAULT_ANALYSTS = ["Ian", "Rafael", "Matheus", "Nicolas", "Gabriel", "José Otávio", "Lisiane", "Pedro"]
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
.wrap{max-width:1220px;margin:auto;padding:26px 18px}.hero{max-width:780px;margin:35px auto;background:#fff;border:1px solid var(--border);border-radius:20px;padding:32px;box-shadow:0 8px 25px #0000000d}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:18px}.g4{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}
.card{background:#fff;border:1px solid var(--border);border-radius:15px;padding:20px;box-shadow:0 6px 20px #0000000a}
.btn{border:0;border-radius:10px;padding:12px 16px;color:#fff;background:var(--navy);font-weight:800;cursor:pointer;text-decoration:none;display:inline-block;text-align:center}
.full{width:100%}.tel{background:var(--teal)}.inf{background:var(--blue)}.danger{background:var(--red)}.good{background:var(--green)}.light{background:#e9eef4;color:#26364a}
h1,h2,h3{margin-top:0}.muted{color:var(--muted)}.small{font-size:13px;color:var(--muted)}.center{text-align:center}
.big{font-size:80px;font-weight:950;letter-spacing:5px;color:var(--navy);margin:22px 0 5px}.kpi{font-size:32px;font-weight:900}
.badge{display:inline-block;padding:8px 10px;background:#eef2f6;border-radius:8px;margin:4px;font-weight:800}
label{display:block;font-weight:800;font-size:14px;margin:10px 0 6px}select,input,textarea{width:100%;padding:10px;border:1px solid #cdd5df;border-radius:8px;font-size:14px;background:#fff}textarea{min-height:75px}
table{width:100%;border-collapse:collapse;background:#fff}th,td{padding:10px;border-bottom:1px solid var(--border);text-align:left;font-size:13px;white-space:nowrap}th{background:#f8fafc}.tbl{overflow:auto}
.row{display:flex;justify-content:space-between;gap:16px;align-items:center}.section{margin-top:26px}.flash{padding:11px 14px;background:#fff4cc;color:#7a4a00;border-radius:10px;margin-bottom:14px}
.userbox{background:#f8fafc;border:1px solid var(--border);border-radius:12px;padding:12px;margin-top:12px}.userbox b{color:var(--navy)}
@media(max-width:800px){.grid,.g4{grid-template-columns:1fr}.topin{align-items:flex-start;flex-direction:column}.big{font-size:58px}}
</style>
"""

BASE = """<!doctype html><html lang='pt-br'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>{{title}}</title>""" + STYLE + """</head><body>
<div class='top'><div class='topin'>
<div class='brand'><img src='{{logo_url}}' alt='Stellantis' onerror="this.style.display='none';this.nextElementSibling.style.display='block'"><div class='fallback' style='display:none'>STELLANTIS</div><div class='brandtext'><b>ICT • Atendimento</b><span>Porto Real</span></div></div>
{% if role in ['analista','admin'] %}<div class='nav'><span>{{display_name}}</span><a href='/painel'>Filas</a><a href='/dashboard'>Dashboard</a><a href='/historico'>Histórico</a>{% if role=='admin' %}<a href='/admin'>Administração</a>{% endif %}<a href='/sair'>Sair</a></div>{% endif %}
</div></div><div class='wrap'>{% with msgs=get_flashed_messages() %}{% for m in msgs %}<div class='flash'>{{m}}</div>{% endfor %}{% endwith %}{{content|safe}}</div></body></html>"""

def db():
    c = sqlite3.connect(DB, timeout=30, isolation_level=None)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    return c

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def today():
    return datetime.now().strftime("%Y-%m-%d")

def init():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios(id INTEGER PRIMARY KEY AUTOINCREMENT,nome TEXT UNIQUE NOT NULL,senha_hash TEXT NOT NULL,role TEXT NOT NULL DEFAULT 'analista',ativo INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS motivos(id INTEGER PRIMARY KEY AUTOINCREMENT,categoria TEXT NOT NULL,nome TEXT NOT NULL,ativo INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS senhas(id INTEGER PRIMARY KEY AUTOINCREMENT,numero TEXT NOT NULL,categoria TEXT NOT NULL,status TEXT NOT NULL,solicitante_nome TEXT NOT NULL,identifiant TEXT NOT NULL,analista TEXT,motivo TEXT,observacao TEXT,criada_em TEXT NOT NULL,chamada_em TEXT,finalizada_em TEXT,cancelada_em TEXT);
        CREATE TABLE IF NOT EXISTS contadores(data TEXT,categoria TEXT,ultimo INTEGER,PRIMARY KEY(data,categoria));
        """)
        if c.execute("SELECT COUNT(*) n FROM usuarios").fetchone()["n"] == 0:
            for nome in DEFAULT_ANALYSTS:
                c.execute("INSERT INTO usuarios(nome,senha_hash,role) VALUES(?,?,?)", (nome, generate_password_hash("ict123"), "analista"))
            c.execute("INSERT INTO usuarios(nome,senha_hash,role) VALUES(?,?,?)", ("Administrador", generate_password_hash("admin123"), "admin"))
            
        colunas_senhas = [r["name"] for r in c.execute("PRAGMA table_info(senhas)").fetchall()]
        if "numero_chamado" not in colunas_senhas:
            c.execute("ALTER TABLE senhas ADD COLUMN numero_chamado TEXT")

        if c.execute("SELECT COUNT(*) n FROM motivos").fetchone()["n"] == 0:
            for cat, itens in DEFAULT_REASONS.items():
                for item in itens:
                    c.execute("INSERT INTO motivos(categoria,nome) VALUES(?,?)", (cat, item))

def role():
    return session.get("role")

def auth():
    return role() in ("analista", "admin")

def page(title, content, **kw):
    return render_template_string(BASE, title=title, content=render_template_string(content, **kw), role=role(), display_name=session.get("nome"), logo_url=LOGO_URL)

@app.route("/")
def home():
    return page("ICT - Atendimento", """<div class='hero center'><h1>Atendimento ICT</h1><p class='muted'>Selecione o tipo de atendimento.</p><div class='grid'>
    <div class='card'><div style='font-size:36px'>📱</div><h2>Telefonia</h2><p class='muted'>Celular corporativo, chip e configuração.</p><a class='btn tel full' href='/solicitar/telefonia'>Continuar</a></div>
    <div class='card'><div style='font-size:36px'>💻</div><h2>Informática</h2><p class='muted'>Computador, software, acesso e periféricos.</p><a class='btn inf full' href='/solicitar/informatica'>Continuar</a></div></div></div>""")

@app.route("/solicitar/<cat>", methods=["GET", "POST"])
def solicitar(cat):
    if cat not in CATS:
        return "Categoria inválida", 400
    if request.method == "GET":
        return page("Identificação", """<div class='hero' style='max-width:620px'><h1>{{nome_cat}}</h1><p class='muted'>Preencha seus dados antes de confirmar o atendimento.</p><p class='small'>Cada Identifiant pode ter no máximo 1 senha aguardando por categoria. Assim, é possível ter 1 senha de Telefonia e 1 de Informática ao mesmo tempo.</p><form method='post'>
        <label>Nome completo</label><input name='solicitante_nome' required maxlength='100' placeholder='Digite seu nome'>
        <label>Identifiant</label><input name='identifiant' required maxlength='50' placeholder='Digite seu identifiant'>
        <label>Número do chamado</label><input name='numero_chamado' maxlength='60' placeholder='Digite o número do chamado'>
        <button class='btn full' style='margin-top:16px'>Confirmar e gerar senha</button></form><a class='btn light full' style='margin-top:8px' href='/'>Voltar</a></div>""", nome_cat=CATS[cat][1])
    
    nome = request.form.get("solicitante_nome", "").strip()
    ident = request.form.get("identifiant", "").strip().upper()
    numero_chamado = request.form.get("numero_chamado", "").strip().upper()

    if not nome or not ident:
        flash("Preencha nome e identifiant.")
        return redirect(url_for("solicitar", cat=cat))

    with db() as c:
        senha_existente = c.execute(
            """SELECT numero, categoria, criada_em
               FROM senhas
               WHERE UPPER(TRIM(identifiant))=?
                 AND categoria=?
                 AND status='aguardando'
                 AND substr(criada_em,1,10)=?
               ORDER BY id DESC
               LIMIT 1""",
            (ident, cat, today())
        ).fetchone()

        if senha_existente:
            flash(
                f"Você já possui a senha {senha_existente['numero']} de {CATS[cat][1]} aguardando atendimento. "
                f"É permitido retirar no máximo 1 senha aguardando para {CATS[cat][1]}."
            )
            return redirect(url_for("solicitar", cat=cat))

        c.execute("BEGIN IMMEDIATE")
        try:
            d = today()
            r = c.execute("SELECT ultimo FROM contadores WHERE data=? AND categoria=?", (d, cat)).fetchone()
            n = r["ultimo"] + 1 if r else 1
            if r:
                c.execute("UPDATE contadores SET ultimo=? WHERE data=? AND categoria=?", (n, d, cat))
            else:
                c.execute("INSERT INTO contadores VALUES(?,?,?)", (d, cat, n))
            
            senha = f"{CATS[cat][0]}{n:03d}"
            c.execute(
                "INSERT INTO senhas(numero,categoria,status,solicitante_nome,identifiant,numero_chamado,criada_em) VALUES(?,?,?,?,?,?,?)",
                (senha, cat, "aguardando", nome, ident, numero_chamado, now())
            )
            c.execute("COMMIT")
        except Exception:
            c.execute("ROLLBACK")
            raise

    return redirect(url_for("senha", numero=senha))

@app.route("/senha/<numero>")
def senha(numero):
    with db() as c:
        s = c.execute("SELECT * FROM senhas WHERE numero=? AND substr(criada_em,1,10)=? ORDER BY id DESC LIMIT 1", (numero, today())).fetchone()
    if not s:
        return "Senha não encontrada", 404
    return page("Sua senha", """<div class='hero center'><p class='muted'>Sua senha</p><div class='big'>{{s.numero}}</div><h2>{{cat}}</h2><div class='userbox'><b>{{s.solicitante_nome}}</b><br><span class='small'>Identifiant: {{s.identifiant}}</span><br><span class='small'>Chamado: {{s.numero_chamado or '-'}}</span></div><p class='muted'>Aguarde ser chamado por um analista.</p><a class='btn light' href='/'>Voltar ao início</a></div>""", s=s, cat=CATS[s["categoria"]][1])

@app.route("/analista", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return page("Login ICT", """<div class='hero' style='max-width:500px'><h1>Acesso interno</h1><p class='muted'>Entre com seu usuário e senha.</p><form method='post'><label>Usuário</label><input name='nome' required><label>Senha</label><input name='senha' type='password' required><button class='btn full' style='margin-top:14px'>Entrar</button></form></div>""")
    
    nome = request.form.get("nome", "").strip()
    senha = request.form.get("senha", "")
    with db() as c:
        u = c.execute("SELECT * FROM usuarios WHERE nome=? AND ativo=1", (nome,)).fetchone()
    if u and check_password_hash(u["senha_hash"], senha):
        session["nome"] = u["nome"]
        session["role"] = u["role"]
        return redirect("/painel")
    flash("Usuário ou senha inválidos.")
    return redirect("/analista")

@app.route("/sair")
def sair():
    session.clear()
    return redirect("/analista")

@app.route("/painel")
def painel():
    if not auth():
        return redirect("/analista")
    with db() as c:
        ag = c.execute("SELECT * FROM senhas WHERE status='aguardando' AND substr(criada_em,1,10)=? ORDER BY id", (today(),)).fetchall()
        em = c.execute("SELECT * FROM senhas WHERE status='em_atendimento' AND substr(criada_em,1,10)=? ORDER BY chamada_em", (today(),)).fetchall()
        fin = c.execute("SELECT COUNT(*) n FROM senhas WHERE status='finalizado' AND substr(criada_em,1,10)=?", (today(),)).fetchone()["n"]
        motivos = {cat: [r["nome"] for r in c.execute("SELECT nome FROM motivos WHERE categoria=? AND ativo=1 ORDER BY nome", (cat,)).fetchall()] for cat in CATS}
    
    f = {"telefonia": [], "informatica": []}
    for x in ag:
        f[x["categoria"]].append(x)
        
    return page("Filas", """<h1>Filas de atendimento</h1><p class='muted'>Todos os analistas visualizam as duas filas.</p><div class='grid'>
    {% for cat in ['telefonia','informatica'] %}<div class='card'><div class='row'><div><h2>{{'📱 Telefonia' if cat=='telefonia' else '💻 Informática'}}</h2><span class='small'>Aguardando</span></div><div class='kpi'>{{f[cat]|length}}</div></div>
    <div style='margin:14px 0'>{% for s in f[cat] %}<div class='userbox'><span class='badge'>{{s.numero}}</span> <b>{{s.solicitante_nome}}</b><br><span class='small'>Identifiant: {{s.identifiant}}</span><br><span class='small'>Chamado: {{s.numero_chamado or '-'}}</span></div>{% else %}<span class='small'>Nenhuma senha aguardando.</span>{% endfor %}</div>
    <form method='post' action='/chamar/{{cat}}'><button class='btn {{'tel' if cat=='telefonia' else 'inf'}} full' {% if not f[cat] %}disabled{% endif %}>Chamar próximo</button></form></div>{% endfor %}</div>
    <div class='g4 section'><div class='card'><span class='small'>Telefonia aguardando</span><div class='kpi'>{{f.telefonia|length}}</div></div><div class='card'><span class='small'>Informática aguardando</span><div class='kpi'>{{f.informatica|length}}</div></div><div class='card'><span class='small'>Em atendimento</span><div class='kpi'>{{em|length}}</div></div><div class='card'><span class='small'>Finalizados hoje</span><div class='kpi'>{{fin}}</div></div></div>
    <h2 class='section'>Atendimentos em andamento</h2>{% for s in em %}<div class='card' style='margin-bottom:12px'><div class='grid'><div><h2>{{s.numero}} • {{cats[s.categoria][1]}}</h2><div class='userbox'><b>{{s.solicitante_nome}}</b><br><span class='small'>Identifiant: {{s.identifiant}}</span><br><span class='small'>Chamado: {{s.numero_chamado or '-'}}</span></div><p>Analista: <b>{{s.analista}}</b></p></div>
    <div>{% if s.analista==analyst %}<form method='post' action='/finalizar/{{s.id}}'><label>Motivo</label><select name='motivo' required><option value=''>Selecione...</option>{% for m in motivos[s.categoria] %}<option>{{m}}</option>{% endfor %}</select><label>Observação</label><textarea name='observacao'></textarea><button class='btn good' style='margin-top:10px'>Finalizar atendimento</button></form><form method='post' action='/cancelar/{{s.id}}'><button class='btn danger' style='margin-top:8px'>Cancelar</button></form>{% else %}<p class='muted'>Atendimento assumido por {{s.analista}}.</p>{% endif %}</div></div></div>{% else %}<div class='card'><span class='muted'>Nenhum atendimento em andamento.</span></div>{% endfor %}""", f=f, em=em, fin=fin, cats=CATS, analyst=session["nome"], motivos=motivos)

@app.post("/chamar/<cat>")
def chamar(cat):
    if not auth():
        return redirect("/analista")
    with db() as c:
        c.execute("BEGIN IMMEDIATE")
        try:
            s = c.execute("SELECT * FROM senhas WHERE categoria=? AND status='aguardando' AND substr(criada_em,1,10)=? ORDER BY id LIMIT 1", (cat, today())).fetchone()
            if s:
                c.execute("UPDATE senhas SET status='em_atendimento',analista=?,chamada_em=? WHERE id=? AND status='aguardando'", (session["nome"], now(), s["id"]))
            c.execute("COMMIT")
        except Exception:
            c.execute("ROLLBACK")
            raise
    return redirect("/painel")

@app.post("/finalizar/<int:i>")
def finalizar(i):
    if not auth():
        return redirect("/analista")
    with db() as c:
        s = c.execute("SELECT * FROM senhas WHERE id=?", (i,)).fetchone()
        if s and s["analista"] == session["nome"] and s["status"] == "em_atendimento":
            c.execute("UPDATE senhas SET status='finalizado',motivo=?,observacao=?,finalizada_em=? WHERE id=?", (request.form.get("motivo"), request.form.get("observacao"), now(), i))
    return redirect("/painel")

@app.post("/cancelar/<int:i>")
def cancelar(i):
    if not auth():
        return redirect("/analista")
    with db() as c:
        s = c.execute("SELECT * FROM senhas WHERE id=?", (i,)).fetchone()
        if s and (s["status"] == "aguardando" or s["analista"] == session["nome"]):
            c.execute("UPDATE senhas SET status='cancelado',cancelada_em=? WHERE id=?", (now(), i))
    return redirect("/painel")

def secs(a, b):
    if not a or not b:
        return None
    f = "%Y-%m-%d %H:%M:%S"
    return max(0, (datetime.strptime(b, f) - datetime.strptime(a, f)).total_seconds())

def dur(v):
    if v is None:
        return "-"
    m = round(v / 60)
    return f"{m} min" if m < 60 else f"{m//60}h {m%60:02d}min"

@app.route("/dashboard")
def dashboard():
    if not auth():
        return redirect("/analista")
    di = request.args.get("data_inicio", today())
    df = request.args.get("data_fim", today())
    with db() as c:
        r = c.execute("SELECT * FROM senhas WHERE substr(criada_em,1,10) BETWEEN ? AND ?", (di, df)).fetchall()
    
    final = [x for x in r if x["status"] == "finalizado"]
    es = [secs(x["criada_em"], x["chamada_em"]) for x in r if x["chamada_em"]]
    ds = [secs(x["chamada_em"], x["finalizada_em"]) for x in final if x["finalizada_em"]]
    tel = sum(x["categoria"] == "telefonia" for x in r)
    inf = sum(x["categoria"] == "informatica" for x in r)
    by = {}
    for x in final:
        by[x["analista"]] = by.get(x["analista"], 0) + 1
    rank = sorted(by.items(), key=lambda z: (-z[1], z[0] or ""))
    
    return page("Dashboard", """<h1>Dashboard</h1><form class='card grid' method='get'><div><label>Data inicial</label><input type='date' name='data_inicio' value='{{di}}'></div><div><label>Data final</label><input type='date' name='data_fim' value='{{df}}'></div><button class='btn'>Atualizar</button></form><div class='g4 section'><div class='card'><span class='small'>Total</span><div class='kpi'>{{total}}</div></div><div class='card'><span class='small'>Finalizados</span><div class='kpi'>{{fin}}</div></div><div class='card'><span class='small'>Média de espera</span><div class='kpi' style='font-size:24px'>{{me}}</div></div><div class='card'><span class='small'>Média de atendimento</span><div class='kpi' style='font-size:24px'>{{md}}</div></div></div><div class='grid section'><div class='card'><h2>Por tipo</h2><p>Telefonia <b style='float:right'>{{tel}}</b></p><p>Informática <b style='float:right'>{{inf}}</b></p></div><div class='card'><h2>Finalizados por analista</h2>{% for a,n in rank %}<p>{{a}} <b style='float:right'>{{n}}</b></p>{% else %}<p class='muted'>Sem atendimentos finalizados.</p>{% endfor %}</div></div>""", di=di, df=df, total=len(r), fin=len(final), me=dur(sum(es)/len(es) if es else None), md=dur(sum(ds)/len(ds) if ds else None), tel=tel, inf=inf, rank=rank)

@app.route("/historico")
def historico():
    if not auth():
        return redirect("/analista")
    di = request.args.get("data_inicio", today())
    df = request.args.get("data_fim", today())
    cat = request.args.get("categoria", "")
    ana = request.args.get("analista", "")
    
    q = "SELECT * FROM senhas WHERE substr(criada_em,1,10) BETWEEN ? AND ?"
    p = [di, df]
    if cat in CATS:
        q += " AND categoria=?"
        p.append(cat)
    if ana:
        q += " AND analista=?"
        p.append(ana)
    q += " ORDER BY id DESC LIMIT 1000"
    
    with db() as c:
        r = c.execute(q, p).fetchall()
        users = [x["nome"] for x in c.execute("SELECT nome FROM usuarios WHERE role='analista' AND ativo=1 ORDER BY nome").fetchall()]
    
    rows = []
    for x in r:
        d = dict(x)
        d["espera"] = dur(secs(x["criada_em"], x["chamada_em"]))
        d["duracao"] = dur(secs(x["chamada_em"], x["finalizada_em"]))
        rows.append(d)
        
    return page("Histórico", """<h1>Histórico</h1><form class='card g4' method='get'><div><label>Data inicial</label><input type='date' name='data_inicio' value='{{di}}'></div><div><label>Data final</label><input type='date' name='data_fim' value='{{df}}'></div><div><label>Tipo</label><select name='categoria'><option value=''>Todos</option><option value='telefonia'>Telefonia</option><option value='informatica'>Informática</option></select></div><div><label>Analista</label><select name='analista'><option value=''>Todos</option>{% for a in users %}<option>{{a}}</option>{% endfor %}</select></div><button class='btn'>Filtrar</button></form><div class='card tbl section'><table><tr><th>Senha</th><th>Solicitante</th><th>Identifiant</th><th>Nº chamado</th><th>Tipo</th><th>Status</th><th>Analista</th><th>Retirada</th><th>Espera</th><th>Duração</th><th>Motivo</th><th>Observação</th></tr>{% for s in rows %}<tr><td><b>{{s.numero}}</b></td><td>{{s.solicitante_nome}}</td><td>{{s.identifiant}}</td><td>{{s.numero_chamado or '-'}}</td><td>{{cats[s.categoria][1]}}</td><td>{{s.status}}</td><td>{{s.analista or '-'}}</td><td>{{s.criada_em}}</td><td>{{s.espera}}</td><td>{{s.duracao}}</td><td>{{s.motivo or '-'}}</td><td>{{s.observacao or '-'}}</td></tr>{% else %}<tr><td colspan='12'>Nenhum registro.</td></tr>{% endfor %}</table></div>""", di=di, df=df, users=users, rows=rows, cats=CATS)

@app.route("/admin")
def admin():
    if role() != "admin":
        return redirect("/painel")
    with db() as c:
        users = c.execute("SELECT * FROM usuarios ORDER BY role DESC,nome").fetchall()
        motivos = c.execute("SELECT * FROM motivos ORDER BY categoria,nome").fetchall()
    return page("Administração", """<h1>Administração</h1><div class='grid'><div class='card'><h2>Analistas</h2><form method='post' action='/admin/usuario'><label>Nome</label><input name='nome' required><label>Senha inicial</label><input name='senha' type='password' required><button class='btn full' style='margin-top:10px'>Adicionar analista</button></form><div class='section'>{% for u in users %}<div class='userbox'><b>{{u.nome}}</b> • {{u.role}} • {{'ativo' if u.ativo else 'inativo'}}<form method='post' action='/admin/senha/{{u.id}}'><input name='senha' type='password' placeholder='Nova senha' required><button class='btn light' style='margin-top:6px'>Salvar nova senha</button></form>{% if u.role!='admin' %}<form method='post' action='/admin/toggle_usuario/{{u.id}}'><button class='btn danger' style='margin-top:6px'>{{'Desativar' if u.ativo else 'Ativar'}}</button></form>{% endif %}</div>{% endfor %}</div></div><div class='card'><h2>Motivos</h2><form method='post' action='/admin/motivo'><label>Categoria</label><select name='categoria'><option value='telefonia'>Telefonia</option><option value='informatica'>Informática</option></select><label>Motivo</label><input name='nome' required><button class='btn full' style='margin-top:10px'>Adicionar motivo</button></form><div class='section'>{% for m in motivos %}<div class='userbox'><b>{{cats[m.categoria][1]}}</b> • {{m.nome}} • {{'ativo' if m.ativo else 'inativo'}}<form method='post' action='/admin/toggle_motivo/{{m.id}}'><button class='btn light' style='margin-top:6px'>{{'Desativar' if m.ativo else 'Ativar'}}</button></form></div>{% endfor %}</div></div></div>""", users=users, motivos=motivos, cats=CATS)

@app.post("/admin/usuario")
def add_user():
    if role() != "admin":
        return redirect("/painel")
    try:
        with db() as c:
            c.execute("INSERT INTO usuarios(nome,senha_hash,role) VALUES(?,?,?)", (request.form["nome"].strip(), generate_password_hash(request.form["senha"]), "analista"))
    except sqlite3.IntegrityError:
        flash("Já existe um usuário com esse nome.")
    return redirect("/admin")

@app.post("/admin/senha/<int:i>")
def senha_admin(i):
    if role() != "admin":
        return redirect("/painel")

    nova_senha = request.form.get("senha", "").strip()
    if not nova_senha:
        flash("Informe uma nova senha.")
        return redirect("/admin")

    with db() as c:
        usuario = c.execute("SELECT id, nome FROM usuarios WHERE id=?", (i,)).fetchone()
        if not usuario:
            flash("Analista não encontrado. A senha não foi alterada.")
            return redirect("/admin")

        resultado = c.execute("UPDATE usuarios SET senha_hash=? WHERE id=?", (generate_password_hash(nova_senha), i))
        if resultado.rowcount == 1:
            flash(f"Senha de {usuario['nome']} alterada com sucesso!")
        else:
            flash("Não foi possível alterar a senha. Tente novamente.")

    return redirect("/admin")

@app.post("/admin/toggle_usuario/<int:i>")
def toggle_user(i):
    if role() != "admin":
        return redirect("/painel")
    with db() as c:
        u = c.execute("SELECT * FROM usuarios WHERE id=?", (i,)).fetchone()
        if u and u["role"] != "admin":
            c.execute("UPDATE usuarios SET ativo=? WHERE id=?", (0 if u["ativo"] else 1, i))
    return redirect("/admin")

@app.post("/admin/motivo")
def add_reason():
    if role() != "admin":
        return redirect("/painel")
    cat = request.form.get("categoria")
    nome = request.form.get("nome", "").strip()
    if cat in CATS and nome:
        with db() as c:
            c.execute("INSERT INTO motivos(categoria,nome) VALUES(?,?)", (cat, nome))
    return redirect("/admin")

@app.post("/admin/toggle_motivo/<int:i>")
def toggle_reason(i):
    if role() != "admin":
        return redirect("/painel")
    with db() as c:
        m = c.execute("SELECT * FROM motivos WHERE id=?", (i,)).fetchone()
        if m:
            c.execute("UPDATE motivos SET ativo=? WHERE id=?", (0 if m["ativo"] else 1, i))
    return redirect("/admin")

if __name__ == "__main__":
    init()
    app.run(host="0.0.0.0", port=5000, debug=False)