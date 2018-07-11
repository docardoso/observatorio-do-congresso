import sts_lib as sts
import flask
import numpy as np
import sqlite3 as sql

app = flask.Flask(__name__)
app.config['DEBUG'] = True

@app.route('/', methods=["GET", "POST"])
def main():
    return flask.render_template("main.html")

@app.route('/votacoes/votacoes-dia')
def votacoes():
    return flask.render_template('index.html')

@app.route('/votacoes/ranking')
def vranking():
	conn = sql.connect("py_politica.db")
	cursor = conn.cursor()
	sql_command = '''
		SELECT * 
		FROM estatisticas_votacao
		WHERE total_sim != 'NULL'
	'''
	res = cursor.execute(sql_command).fetchall()
	return flask.render_template('VRanking.html', ast=res)

@app.route('/materias-dia')
def materias():
    return flask.render_template('materia.html')
    
@app.route('/json')
def json():
    data = sts.votacoes_periodo()
    data = [[sts.converte_data(x[0])*10**3,x[1]] for x in data]        
    return flask.jsonify(data)

@app.route('/json-materia')
def json_materia():
    data = sts.materias_periodo()
    data = [[sts.converte_data(x[0])*10**3,x[1]] for x in data]        
    return flask.jsonify(data)


if __name__ == '__main__':
    app.run()