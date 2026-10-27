import os
import sqlite3
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from database import conectar, criar_banco

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": os.environ.get("CORS_ORIGINS", "*")}})
criar_banco()

def erro(mensagem, status=400):
    return jsonify({"erro": mensagem}), status

def payload():
    return request.get_json(silent=True) or {}

def linhas_para_json(linhas):
    return [dict(linha) for linha in linhas]

def executar(sql, valores=()):
    con = conectar()
    try:
        cur = con.execute(sql, valores)
        con.commit()
        return cur.lastrowid, cur.rowcount
    finally:
        con.close()

@app.get("/")
def inicio():
    return jsonify({"mensagem":"API AcademiaFit funcionando!", "status":"ok"})

@app.get("/api/teste")
def teste():
    return jsonify({"status":"ok","mensagem":"API e banco acessíveis."})

@app.get("/api/dashboard")
def dashboard():
    con = conectar()
    try:
        return jsonify({
            "alunos": con.execute("SELECT COUNT(*) FROM alunos").fetchone()[0],
            "professores": con.execute("SELECT COUNT(*) FROM professores").fetchone()[0],
            "planos": con.execute("SELECT COUNT(*) FROM planos").fetchone()[0],
            "pagamentos_pendentes": con.execute("SELECT COUNT(*) FROM pagamentos WHERE lower(status)='pendente'").fetchone()[0]
        })
    finally: con.close()

# Cadastro/login. Senhas novas são armazenadas com hash; login mantém compatibilidade com senhas antigas.
@app.post("/api/cadastro")
def cadastro():
    d=payload(); nome=str(d.get("nome","")).strip(); email=str(d.get("email","")).strip().lower(); senha=str(d.get("senha",""))
    if not nome or not email or len(senha)<6: return erro("Informe nome, e-mail e senha com pelo menos 6 caracteres.")
    try:
        executar("INSERT INTO usuarios(nome,email,senha) VALUES(?,?,?)",(nome,email,generate_password_hash(senha)))
        return jsonify({"mensagem":"Cadastro realizado com sucesso!"}),201
    except sqlite3.IntegrityError: return erro("Este e-mail já está cadastrado.",409)

@app.post("/api/login")
def login():
    d=payload(); email=str(d.get("email","")).strip().lower(); senha=str(d.get("senha",""))
    if not email or not senha: return erro("E-mail e senha são obrigatórios.")
    con=conectar()
    try: usuario=con.execute("SELECT id,nome,email,senha FROM usuarios WHERE email=?",(email,)).fetchone()
    finally: con.close()
    if not usuario: return erro("E-mail ou senha incorretos.",401)
    senha_db=usuario["senha"]
    try: valido=check_password_hash(senha_db,senha)
    except (ValueError, TypeError): valido=False
    # Compatibilidade com registros criados na versão anterior (texto puro); migra para hash após login.
    if not valido and senha_db == senha:
        valido=True
        executar("UPDATE usuarios SET senha=? WHERE id=?",(generate_password_hash(senha),usuario["id"]))
    if not valido: return erro("E-mail ou senha incorretos.",401)
    return jsonify({"mensagem":"Login realizado com sucesso!","usuario":{"id":usuario["id"],"nome":usuario["nome"],"email":usuario["email"]}})

# Alunos
@app.get("/api/alunos")
def listar_alunos():
    con=conectar()
    try: return jsonify(linhas_para_json(con.execute("SELECT * FROM alunos ORDER BY id DESC").fetchall()))
    finally: con.close()

@app.post("/api/alunos")
def cadastrar_aluno():
    d=payload(); nome=str(d.get("nome","")).strip()
    if not nome: return erro("O nome do aluno é obrigatório.")
    email=str(d.get("email","")).strip() or None
    campos=(nome,email,d.get("telefone"),d.get("idade"),d.get("dataNascimento") or d.get("data_nascimento"),d.get("plano"),d.get("status","Ativo"))
    try:
        ident,_=executar("INSERT INTO alunos(nome,email,telefone,idade,data_nascimento,plano,status) VALUES(?,?,?,?,?,?,?)",campos)
        return jsonify({"mensagem":"Aluno cadastrado com sucesso!","id":ident}),201
    except sqlite3.IntegrityError as e: return erro("Não foi possível cadastrar o aluno: verifique os dados.",409)

@app.route("/api/alunos/<int:ident>",methods=["PUT","DELETE"])
def aluno_item(ident):
    if request.method=="DELETE":
        _,n=executar("DELETE FROM alunos WHERE id=?",(ident,))
        return (jsonify({"mensagem":"Aluno excluído com sucesso!"}) if n else erro("Aluno não encontrado.",404))
    d=payload()
    nome=str(d.get("nome","")).strip()
    if not nome: return erro("O nome do aluno é obrigatório.")
    _,n=executar("UPDATE alunos SET nome=?,email=?,telefone=?,idade=?,data_nascimento=?,plano=?,status=? WHERE id=?",
       (nome,d.get("email"),d.get("telefone"),d.get("idade"),d.get("dataNascimento") or d.get("data_nascimento"),d.get("plano"),d.get("status","Ativo"),ident))
    return (jsonify({"mensagem":"Aluno atualizado com sucesso!"}) if n else erro("Aluno não encontrado.",404))

# Professores
@app.get("/api/professores")
def listar_professores():
    con=conectar()
    try: return jsonify(linhas_para_json(con.execute("SELECT * FROM professores ORDER BY id DESC").fetchall()))
    finally: con.close()

@app.post("/api/professores")
def cadastrar_professor():
    d=payload(); nome=str(d.get("nome","")).strip()
    if not nome: return erro("O nome do professor é obrigatório.")
    ident,_=executar("INSERT INTO professores(nome,email,telefone,especialidade) VALUES(?,?,?,?)",(nome,d.get("email"),d.get("telefone"),d.get("especialidade")))
    return jsonify({"mensagem":"Professor cadastrado com sucesso!","id":ident}),201

@app.route("/api/professores/<int:ident>",methods=["PUT","DELETE"])
def professor_item(ident):
    if request.method=="DELETE":
        _,n=executar("DELETE FROM professores WHERE id=?",(ident,))
        return jsonify({"mensagem":"Professor excluído com sucesso!"}) if n else erro("Professor não encontrado.",404)
    d=payload(); nome=str(d.get("nome","")).strip()
    if not nome:return erro("O nome do professor é obrigatório.")
    _,n=executar("UPDATE professores SET nome=?,email=?,telefone=?,especialidade=? WHERE id=?",(nome,d.get("email"),d.get("telefone"),d.get("especialidade"),ident))
    return jsonify({"mensagem":"Professor atualizado com sucesso!"}) if n else erro("Professor não encontrado.",404)

# Planos
@app.get("/api/planos")
def listar_planos():
    con=conectar()
    try:return jsonify(linhas_para_json(con.execute("SELECT * FROM planos ORDER BY id DESC").fetchall()))
    finally:con.close()

@app.post("/api/planos")
def cadastrar_plano():
    d=payload(); nome=str(d.get("nome","")).strip(); preco=d.get("preco",d.get("valor"))
    if not nome or preco is None:return erro("Nome e preço são obrigatórios.")
    try:preco=float(str(preco).replace(",",".")); duracao=int(d.get("duracao",1) or 1)
    except (TypeError,ValueError):return erro("Preço e duração devem ser numéricos.")
    if preco<0 or duracao<1:return erro("Preço não pode ser negativo e duração deve ser maior que zero.")
    ident,_=executar("INSERT INTO planos(nome,preco,descricao,duracao) VALUES(?,?,?,?)",(nome,preco,d.get("descricao"),duracao))
    return jsonify({"mensagem":"Plano cadastrado com sucesso!","id":ident}),201

@app.delete("/api/planos/<int:ident>")
def excluir_plano(ident):
    _,n=executar("DELETE FROM planos WHERE id=?",(ident,))
    return jsonify({"mensagem":"Plano excluído com sucesso!"}) if n else erro("Plano não encontrado.",404)

# Pagamentos
@app.get("/api/pagamentos")
def listar_pagamentos():
    con=conectar()
    try:
        rows=con.execute("""SELECT p.id,p.aluno_id,a.nome AS aluno,p.valor,p.data,p.status,p.forma_pagamento
          FROM pagamentos p JOIN alunos a ON a.id=p.aluno_id ORDER BY p.id DESC""").fetchall()
        return jsonify(linhas_para_json(rows))
    finally:con.close()

@app.post("/api/pagamentos")
def cadastrar_pagamento():
    d=payload(); aluno_id=d.get("aluno_id"); valor=d.get("valor"); data=d.get("data")
    if aluno_id is None or valor is None or not data:return erro("Aluno, valor e data são obrigatórios.")
    try:aluno_id=int(aluno_id);valor=float(str(valor).replace(",",".")); 
    except (TypeError,ValueError):return erro("Aluno e valor inválidos.")
    if valor<0:return erro("O valor não pode ser negativo.")
    con=conectar()
    try:
        if not con.execute("SELECT id FROM alunos WHERE id=?",(aluno_id,)).fetchone():return erro("Aluno não encontrado.",404)
        cur=con.execute("INSERT INTO pagamentos(aluno_id,valor,data,status,forma_pagamento) VALUES(?,?,?,?,?)",(aluno_id,valor,data,d.get("status","Pendente"),d.get("forma_pagamento") or d.get("forma_pagamento")))
        con.commit()
        return jsonify({"mensagem":"Pagamento registrado com sucesso!","id":cur.lastrowid}),201
    finally:con.close()

@app.route("/api/pagamentos/<int:ident>",methods=["PUT","DELETE"])
def pagamento_item(ident):
    if request.method=="DELETE":
        _,n=executar("DELETE FROM pagamentos WHERE id=?",(ident,))
        return jsonify({"mensagem":"Pagamento excluído!"}) if n else erro("Pagamento não encontrado.",404)
    d=payload()
    try:valor=float(str(d.get("valor")).replace(",","."));aluno_id=int(d.get("aluno_id"))
    except (TypeError,ValueError):return erro("Aluno e valor inválidos.")
    _,n=executar("UPDATE pagamentos SET aluno_id=?,valor=?,data=?,status=?,forma_pagamento=? WHERE id=?",(aluno_id,valor,d.get("data"),d.get("status","Pendente"),d.get("forma_pagamento"),ident))
    return jsonify({"mensagem":"Pagamento atualizado!"}) if n else erro("Pagamento não encontrado.",404)

# Treinos
@app.get("/api/treinos")
def listar_treinos():
    con=conectar()
    try:
        rows=con.execute("""SELECT t.id,t.aluno_id,a.nome AS aluno,t.nome,t.descricao,t.professor_id,p.nome AS professor,t.divisao
        FROM treinos t JOIN alunos a ON a.id=t.aluno_id LEFT JOIN professores p ON p.id=t.professor_id ORDER BY t.id DESC""").fetchall()
        return jsonify(linhas_para_json(rows))
    finally:con.close()

@app.post("/api/treinos")
def cadastrar_treino():
    d=payload(); aluno_id=d.get("aluno_id"); nome=str(d.get("nome","")).strip()
    if aluno_id is None or not nome:return erro("Aluno e nome do treino são obrigatórios.")
    try:aluno_id=int(aluno_id)
    except (ValueError,TypeError):return erro("ID do aluno inválido.")
    con=conectar()
    try:
        if not con.execute("SELECT id FROM alunos WHERE id=?",(aluno_id,)).fetchone():return erro("Aluno não encontrado.",404)
        cur=con.execute("INSERT INTO treinos(aluno_id,nome,descricao,professor_id,divisao) VALUES(?,?,?,?,?)",(aluno_id,nome,d.get("descricao"),d.get("professor_id") or None,d.get("divisao")))
        con.commit()
        return jsonify({"mensagem":"Treino cadastrado com sucesso!","id":cur.lastrowid}),201
    finally:con.close()

@app.route("/api/treinos/<int:ident>",methods=["PUT","DELETE"])
def treino_item(ident):
    if request.method=="DELETE":
        _,n=executar("DELETE FROM treinos WHERE id=?",(ident,))
        return jsonify({"mensagem":"Treino excluído!"}) if n else erro("Treino não encontrado.",404)
    d=payload()
    try:aluno_id=int(d.get("aluno_id"))
    except (ValueError,TypeError):return erro("ID do aluno inválido.")
    nome=str(d.get("nome","")).strip()
    if not nome:return erro("Nome do treino obrigatório.")
    _,n=executar("UPDATE treinos SET aluno_id=?,nome=?,descricao=?,professor_id=?,divisao=? WHERE id=?",(aluno_id,nome,d.get("descricao"),d.get("professor_id") or None,d.get("divisao"),ident))
    return jsonify({"mensagem":"Treino atualizado!"}) if n else erro("Treino não encontrado.",404)

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)),debug=False)
