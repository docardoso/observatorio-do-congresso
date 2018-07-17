import sts_lib as sts
import flask
import numpy as np
import sqlite3 as sql

website = flask.Flask(__name__)
website.config['DEBUG'] = True

@website.route('/', methods=["GET", "POST"])
def main():
    return flask.render_template("main.html")

@website.route('/votacoes/votacoes-dia')
def votacoes():
    return flask.render_template('index.html')

@website.route('/votacoes/ranking')
def v_ranking():
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

@website.route('/materias-dia')
def materias():
    return flask.render_template('materia.html')

@website.route('/parlamentares/ranking')
def p_ranking():
	res = list()
	assertividade = sts.assertividade_parlamentar()
	total = sts.numero_votos()
	for parlamentar in total.keys():
		res.append((parlamentar, assertividade[parlamentar], total[parlamentar]))

	return flask.render_template('Pranking.html', ast=res)

@website.route('/json')
def json():
    data = sts.votacoes_periodo()
    data = [[sts.converte_data(x[0])*10**3,x[1]] for x in data]        
    return flask.jsonify(data)

@website.route('/json-materia')
def json_materia():
    data = sts.materias_periodo()
    data = [[sts.converte_data(x[0])*10**3,x[1]] for x in data]        
    return flask.jsonify(data)


if __name__ == '__main__':
    website.run()