import sts_lib as sts
import flask
import numpy as np
import sqlite3 as sql

site = flask.Flask(__name__)
site.config['DEBUG'] = True

@site.route('/', methods=["GET", "POST"])
def main():
    return flask.render_template("main.html")

@site.route('/votacoes/votacoes-dia')
def votacoes():
    return flask.render_template('index.html')

@site.route('/votacoes/ranking')
def vranking():
	conn = sql.connect("py_politica.db")
	cursor = conn.cursor()
	sql_command = '''
		SELECT * 
		FROM estatisticas_votacao
		WHERE total_sim != 'NULL'
	'''
	res = cursor.execute(sql_command).fetchall()
	for i,r in enumerate(res):
		r = list(r)
		r[0] = sts.converte_id_votacao(r[0])
		res[i] = r

	return flask.render_template('VRanking.html', ast=res)

@site.route('/materias-dia')
def materias():
    return flask.render_template('materia.html')
    
@site.route('/json')
def json():
    data = sts.votacoes_periodo()
    data = [[sts.converte_data(x[0])*10**3,x[1]] for x in data]        
    return flask.jsonify(data)

@site.route('/json-materia')
def json_materia():
    data = sts.materias_periodo()
    data = [[sts.converte_data(x[0])*10**3,x[1]] for x in data]        
    return flask.jsonify(data)


if __name__ == '__main__':
    site.run()