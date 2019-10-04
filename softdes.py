# -*- coding: utf-8 -*-
"""
Created on Wed Jun 28 09:00:39 2017

@AUTHor: rauli
"""
import hashlib
import sqlite3
from datetime import datetime
from flask import Flask, request, render_template
from flask_httpauth import HTTPBasicAuth

DBNAME = './quiz.db'

def lambda_handler(event, context):
    try:
        import numbers
        def not_equals(first, second):
            if isinstance(first, numbers.Number) and isinstance(second, numbers.Number):
                return abs(first - second) > 1e-3
            return first != second
        ndes = int(event['ndes'])
        code = event['code']
        args = event['args']
        resp = event['resp']
        diag = event['diag']
        exec(code, locals())
        test = []
        for index in enumerate(args):
            if not 'desafio{0}'.format(ndes) in locals():
                return "Nome da função inválido. Usar 'def desafio{0}(...)'".format(ndes)
            if not_equals(eval('desafio{0}(*arg)'.format(ndes)), resp[index]):
                test.append(diag[index])
        return " ".join(test)
    except:
        return "Função inválida."

def converte_data(orig):
    return orig[8:10]+'/'+orig[5:7]+'/'+orig[0:4]+' '+orig[11:13]+':'+orig[14:16]+':'+orig[17:]

def get_quizes(user):
    conn = sqlite3.connect(DBNAME)
    cursor = conn.cursor()
    if user == 'admin' or user == 'fabioja':
        (cursor.execute("SELECT id, numb from QUIZ" \
            .format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))))
    else:
        cursor.execute("SELECT id, numb from QUIZ where release < '{0}'" \
            .format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    info = [reg for reg in cursor.fetchall()]
    conn.close()
    return info

def get_user_quiz(userid, quizid):
    conn = sqlite3.connect(DBNAME)
    cursor = conn.cursor()
    cursor.execute("SELECT sent,answer,result from USERQUIZ where userid = '{0}' and quizid = {1} order by sent desc" \
        .format(userid, quizid))
    info = [reg for reg in cursor.fetchall()]
    conn.close()
    return info

def set_user_quiz(userid, quizid, sent, answer, result):
    conn = sqlite3.connect(DBNAME)
    cursor = conn.cursor()
    #print("insert into USERQUIZ(userid,quizid,sent,answer,result) values ('{0}',{1},'{2}','{3}','{4}');"
        #.format(userid, quizid, sent, answer, result))
    #cursor.execute("insert into USERQUIZ(userid,quizid,sent,answer,result) values ('{0}',{1},'{2}','{3}','{4}');"
        #.format(userid, quizid, sent, answer, result))
    cursor.execute("insert into USERQUIZ(userid,quizid,sent,answer,result) values (?,?,?,?,?);", (userid, quizid, sent, answer, result))
    #
    conn.commit()
    conn.close()

def get_quiz(id_func, user):
    conn = sqlite3.connect(DBNAME)
    cursor = conn.cursor()
    if user == 'admin' or user == 'fabioja':
        cursor.execute("SELECT id, release, expire, problem, tests, results, diagnosis, numb from QUIZ where id = {0}".format(id_func))
    else:
        cursor.execute("SELECT id, release, expire, problem, tests, results, diagnosis, numb from QUIZ where id = {0} and release < '{1}'".format(id_func, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    info = [reg for reg in cursor.fetchall()]
    conn.close()
    return info

def set_info(pwd, user):
    conn = sqlite3.connect(DBNAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE USER set pass = ? where user = ?", (pwd, user))
    conn.commit()
    conn.close()

def get_info(user):
    conn = sqlite3.connect(DBNAME)
    cursor = conn.cursor()
    cursor.execute("SELECT pass, type from USER where user = '{0}'".format(user))
    print("SELECT pass, type from USER where user = '{0}'".format(user))
    info = [reg[0] for reg in cursor.fetchall()]
    conn.close()
    if not info:
        return None
    return info[0]

AUTH = HTTPBasicAuth()

APP = Flask(__name__, static_url_path='')
APP.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?TX'

@APP.route('/', methods=['GET', 'POST'])
@AUTH.login_required
def main():
    msg = ''
    p_o = 1
    challenges = get_quizes(AUTH.username())
    sent = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if request.method == 'POST' and 'ID' in request.args:
        id_o = request.args.get('ID')
        quiz = get_quiz(id_o, AUTH.username())
        if not quiz:
            msg = "Boa tentativa, mas não vai dar certo!"
            p_o = 2
            return render_template('index.html', username=AUTH.username(), challenges=challenges, p=p_o, msg=msg)
        quiz = quiz[0]
        if sent > quiz[2]:
            msg = "Sorry... Prazo expirado!"
        f_o = request.files['code']
        filename = './upload/{0}-{1}.py'.format(AUTH.username(), sent)
        f_o.save(filename)
        with open(filename, 'r') as fp_o:
            answer = fp_o.read()
        #lamb = boto3.client('lambda')
        args = {"ndes": id_o, "code": answer, "args": eval(quiz[4]), "resp": eval(quiz[5]), "diag": eval(quiz[6])}

        #response = lamb.invoke(FunctionName="Teste", InvocationType='RequestResponse', Payload=json.dumps(args))
        #feedback = response['Payload'].read()
        #feedback = json.loads(feedback).replace('"','')
        feedback = lambda_handler(args, '')


        result = 'Erro'
        if not feedback:
            feedback = 'Sem erros.'
            result = 'OK!'

        set_user_quiz(AUTH.username(), id_o, sent, feedback, result)


    if request.method == 'GET':
        if 'ID' in request.args:
            id_o = request.args.get('ID')
        else:
            id_o = 1

    if not challenges:
        msg = "Ainda não há desafios! Volte mais tarde."
        p_o = 2
        return render_template('index.html', username=AUTH.username(), challenges=challenges, p=p_o, msg=msg)
    else:
        quiz = get_quiz(id_o, AUTH.username())

        if not quiz:
            msg = "Oops... Desafio invalido!"
            p_o = 2
            return render_template('index.html', username=AUTH.username(), challenges=challenges, p=p_o, msg=msg)

        answers = get_user_quiz(AUTH.username(), id_o)
    return render_template('index.html', username=AUTH.username(), challenges=challenges, quiz=quiz[0], e=(sent > quiz[0][2]), answers=answers, p=p_o, msg=msg, expi=converte_data(quiz[0][2]))
@APP.route('/pass', methods=['GET', 'POST'])
@AUTH.login_required
def change():
    if request.method == 'POST':
        velha = request.form['old']
        nova = request.form['new']
        repet = request.form['again']

        p_o = 1
        msg = ''
        if nova != repet:
            msg = 'As novas senhas nao batem'
            p_o = 3
        elif get_info(AUTH.username()) != hashlib.md5(velha.encode()).hexdigest():
            msg = 'A senha antiga nao confere'
            p_o = 3
        else:
            set_info(hashlib.md5(nova.encode()).hexdigest(), AUTH.username())
            msg = 'Senha alterada com sucesso'
            p_o = 3
    else:
        msg = ''
        p_o = 3

    return render_template('index.html', username=AUTH.username(), challenges=get_quizes(AUTH.username()), p=p_o, msg=msg)


@APP.route('/logout')
def logout():
    return render_template('index.html', p=2, msg="Logout com sucesso"), 401

@AUTH.get_password
def get_password(username):
    return get_info(username)

@AUTH.hash_password
def hash_pw(password):
    return hashlib.md5(password.encode()).hexdigest()

if __name__ == '__main__':
    APP.run(debug=True, host='0.0.0.0', port=80)
