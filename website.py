import utility as ut
import votacao as vt
import parlamentar as pl
import flask
import numpy as np
import sqlite3 as sql

website = flask.Flask(__name__)
website.config['DEBUG'] = True

@website.route('/', methods=["GET", "POST"])
def main_page():
    return flask.render_template("main.html")

@website.route('/votacoes/grafvotacaodia')
def graf_votacao_dia():
    return flask.render_template('graf_votacao_dia.html')

@website.route('/votacoes/ranking')
def ranking_votacao():
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
		r[0] = ut.converte_id_votacao(r[0])
		res[i] = r

	return flask.render_template('tab_votacao.html', ast=res)

@website.route('/materias/grafmateriadia')
def graf_materias_dia():
    return flask.render_template('graf_materia_dia.html')


@website.route('/parlamentares/ranking')
def ranking_parlamentar():

	assertividade = pl.assertividade_parlamentar()
	i_concordancia = pl.indice_concordancia()
	total_votos = ut.sql_dict(ut.sql_command_total)
	total_validos = ut.sql_dict(ut.sql_command_valido)
	mat_prop = pl.n_mat_propostas(False)
	mat_prop_vt = pl.n_mat_propostas()
	i_trocas = pl.indice_trocas()
	mandato = pl.count_info('mandato')
	total_ausencias = ut.sql_dict(ut.sql_command_ausencia)
	total_ausencias_jus = ut.sql_dict(ut.sql_command_justificada)

	dicts = [assertividade, i_concordancia, total_votos, total_validos, mat_prop, 
			mat_prop_vt, i_trocas, mandato, total_ausencias, total_ausencias_jus]

	res = {k:[ dic.get(k, '-') for dic in dicts] for k in pl.get_nome()}

	return flask.render_template('tab_parlamentar.html', res=res)

@website.route('/votacoes/graftipofreq')
def graf_tipo_freq():
    return flask.render_template('graf_voto_freq.html')

# @website.route('/materia/bubble')
# def bubble():
#     return flask.render_template('bubble.html')

@website.route('/json-votacaodia')
def json_votacao_dia():
    data = vt.info_periodo(('votacao', 'dataHoraInicio'))
    data = [[ut.converte_data(x[0]),x[1]] for x in data]        
    return flask.jsonify(data)

@website.route('/json-materiadia')
def json_materia_dia():
    data = vt.info_periodo(('materia', 'data_apresentacao'))
    data = [[ut.converte_data(x[0]) ,x[1]] for x in data]        
    return flask.jsonify(data)

@website.route('/json-tipofreq')
def json_tipo_freq():
    info = vt.tipo_voto()
    return flask.jsonify(info)

# @website.route('/json-materia-bubble')
# def json_materia_bubble():
#     info = sts.bubble_chart()
#     return flask.jsonify(info)

if __name__ == '__main__':
    website.run()