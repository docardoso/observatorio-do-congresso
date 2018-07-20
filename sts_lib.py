# Versão 1.2.3
import sqlite3 as sql
import scipy.stats as st
from matplotlib import pyplot as pp
import numpy as np
import time

# CONST GLOBAIS DE TEMPO
data_atual = time.localtime()[0:3]
# Dicionario com as variáveis globais
global_keys = dict()
global_keys['DATA_INICIO'] = '2010-02-24'
global_keys['DATA_FIM'] = '{}-{}-{}'.format(data_atual[0], data_atual[1], data_atual[2])

# Funções auxiliares
def converte_data(data_string):
	""" Converte as data_strings em milisegundos a partir da epoch"""
	data = time.strptime(data_string , '%Y-%m-%d')
	data = time.mktime(data)
	return data

def converte_id_votacao(id_votacao):
	conn = sql.connect("py_politica.db")
	cursor = conn.cursor()
	sql_command = '''
		SELECT tipo, numero, strftime('%Y', data_apresentacao) as ano
		FROM materia 
		WHERE id_materia in (
			SELECT id_materia 
			FROM votacao
			WHERE id_votacao = {})'''

	votacao = cursor.execute(sql_command.format(id_votacao)).fetchone()
	try:
		id_votacao = '{} {}/{}'.format(votacao[0], votacao[1], votacao[2])
		return id_votacao

	except TypeError:
		return id_votacao


# Funções Relacionadas às votações
def votacoes_periodo(passo = 'D', data_in = global_keys['DATA_INICIO'], data_fim = global_keys['DATA_FIM']):
	""" Retorna o número de votações numa faixa de tempo, podendo alternar o passo da contagem """
	conn = sql.connect("py_politica.db")
	cursor = conn.cursor()
	if passo == 'D':
		sql_command = '''
		SELECT date(dataHorainicio),count(id_votacao)
		FROM votacao
		WHERE date(dataHorainicio) >= '{}' AND
			date(dataHorainicio) <= '{}'
		GROUP BY date(dataHorainicio)
		ORDER BY date(dataHoraInicio);
	'''
		res = cursor.execute(sql_command.format(data_in,data_fim)).fetchall()
		res = [list(x) for x in res]
		conn.close()
		return res

	elif passo == 'M':
		sql_command = '''
			SELECT strftime('%Y-%m', dataHoraInicio) as tmp, count(*) as cnt
			FROM votacao 
			WHERE date(dataHorainicio) >= '{}' AND
				date(dataHorainicio) <= '{}'
			GROUP BY tmp
			ORDER BY date(dataHoraInicio);
		'''	
		res = cursor.execute(sql_command.format(data_in,data_fim)).fetchall()
		res = [list(x) for x in res]
		conn.close()
		return res

	elif passo == 'A':	
		sql_command = '''
			SELECT strftime('%Y', dataHoraInicio) as tmp, count(*) as cnt 
			FROM votacao 
			WHERE date(dataHorainicio) >= '{}' AND
				date(dataHorainicio) <= '{}'
			GROUP BY tmp
			ORDER BY date(dataHoraInicio);
		'''	
		res = cursor.execute(sql_command.format(data_in,data_fim)).fetchall()
		res = [list(x) for x in res]
		conn.close()
		return res

# Funções relacionadas às Matérias
def materias_periodo(passo = 'D', data_in = global_keys['DATA_INICIO'], data_fim = global_keys['DATA_FIM']):
	""" Retorna o número de votações numa faixa de tempo, podendo alternar o passo da contagem """
	conn = sql.connect("py_politica.db")
	cursor = conn.cursor()
	if passo == 'D':
		sql_command = '''
		SELECT date(data_apresentacao) as tmp, count(*)
		FROM materia
		WHERE date(data_apresentacao) >= '{}' AND
			date(data_apresentacao) <= '{}'
		GROUP BY tmp
		ORDER BY date(data_apresentacao);
	'''
		res = cursor.execute(sql_command.format(data_in,data_fim)).fetchall()
		res = [list(x) for x in res]
		conn.close()
		return res

	elif passo == 'M':
		sql_command = '''
			SELECT strftime('%Y-%m', data_apresentacao) as tmp, count(*) as cnt
			FROM materia 
			WHERE date(data_apresentacao) >= '{}' AND
				date(data_apresentacao) <= '{}'
			GROUP BY tmp
			ORDER BY date(dataHoraInicio);
		'''	
		res = cursor.execute(sql_command.format(data_in,data_fim)).fetchall()
		res = [list(x) for x in res]
		conn.close()
		return res

	elif passo == 'A':	
		sql_command = '''
			SELECT strftime('%Y', data_apresentacao) as tmp, count(*) as cnt 
			FROM materia 
			WHERE date(data_apresentacao) >= '{}' AND
				date(data_apresentacao) <= '{}'
			GROUP BY tmp
			ORDER BY date(dataHoraInicio);
		'''	
		res = cursor.execute(sql_command.format(data_in,data_fim)).fetchall()
		res = [list(x) for x in res]
		conn.close()
		return res

# Funções relacionadas aos parlamentares
def assertividade_parlamentar():
	""" Calcula a assertividade dos parlamentares em um período de tempo
	Assertividade é da pela quantidade de votos na descrição mais votada pelo parlamentar / total de votos do parlamentar
	O calculo só é realizado com totais de votos superiores a 40 votos, e só leva em conta votações nominais"""
	conn = sql.connect("py_politica.db")
	cursor = conn.cursor()
	parlamentares = dict()
	sql_command = '''
		SELECT nome, sum(qtd), total
		FROM (SELECT nome, descricao, count(*) as qtd 
			FROM parlamentar NATURAL JOIN voto
			WHERE id_votacao in 
				(SELECT id_votacao 
				FROM votacao) 
			and descricao = 'Sim' or descricao = 'Não'
			GROUP BY id_parlamentar, descricao)r 
		NATURAL JOIN 
			(SELECT nome, count(*) as total
			FROM parlamentar NATURAL JOIN voto
			WHERE id_votacao not in 
				(SELECT id_votacao
				FROM votacao_secreta)
			GROUP BY id_parlamentar)l
		GROUP BY nome;

	'''
 
	res = cursor.execute(sql_command).fetchall()
	for parlamentar in res:
		if parlamentar[2]>=40:
			parlamentares[parlamentar[0]] = "%.2f" %(parlamentar[1]*100/parlamentar[2])
		
		else:
			parlamentares[parlamentar[0]] = 'NA'

	sql_command = '''
		SELECT nome 
		FROM parlamentar'''

	res = cursor.execute(sql_command).fetchall()
	for parlamentar in res:
		if parlamentar[0] not in parlamentares.keys():
			parlamentares[parlamentar[0]] = 'NA'

	conn.close()
	return parlamentares

def numero_votos(data_in = global_keys['DATA_INICIO'], data_fim = global_keys['DATA_FIM']):
	""" Calcula o Número de Votos dos parlamentares dado uma faixa de tempo """
	conn = sql.connect("py_politica.db")
	cursor = conn.cursor()
	parlamentares = dict()
	sql_command = '''
		SELECT nome, count(*) as qtd 
		FROM parlamentar NATURAL JOIN voto
		WHERE id_votacao in 
			(SELECT id_votacao 
			FROM votacao 
			WHERE date(dataHoraInicio)>='{}' and date(dataHoraInicio)<='{}')

		GROUP BY id_parlamentar;
		'''
	res = cursor.execute(sql_command.format(data_in, data_fim)).fetchall()
	for parlamentar in res:
		parlamentares[parlamentar[0]] = parlamentar[1]

	conn.close()
	return parlamentares

def chinelinho(id_parlamentar, data_in = global_keys['DATA_INICIO'], data_fim = global_keys['DATA_FIM']):
	""" Calcula uma porcentagem entre as licenças parlamentares e o total de votos """
	conn = sql.connect("py_politica.db")
	cursor = conn.cursor()
	sql_command = ''' 
		SELECT count(*) as qtd 
		FROM parlamentar NATURAL JOIN voto
		WHERE id_votacao in 
			(SELECT id_votacao 
			FROM votacao 
			WHERE date(dataHoraInicio)>='{}' and date(dataHoraInicio)<='{}')
			and id_parlamentar = {}
			and descricao like 'L%'
		'''
	sql_command2 = '''
		SELECT count(*) 
		FROM voto
		WHERE id_votacao in 
			(SELECT id_votacao 
			FROM votacao 
			WHERE date(dataHoraInicio)>='{}' and date(dataHoraInicio)<='{}')
			and id_parlamentar = {}
		'''
	licenca = cursor.execute(sql_command.format(data_in, data_fim, id_parlamentar)).fetchone()
	total = cursor.execute(sql_command2.format(data_in, data_fim, id_parlamentar)).fetchone()
	if total >= 40:
		chinelo = (licenca[0]/total[0])*100
		conn.close()
		return chinelo

def concordancia():
	conn = sql.connect("py_politica.db")
	cursor = conn.cursor()
	parlamentares = dict()
	
	sql_command = '''
		SELECT * FROM (SELECT nome, count(*) 
		FROM parlamentar NATURAL JOIN voto NATURAL JOIN votacao
		WHERE descricao = 'Sim' AND resultado = 'A' OR descricao = 'Não' AND resultado = 'R' 
		GROUP BY id_parlamentar)r NATURAL JOIN
		(SELECT nome, count(*) as total FROM voto NATURAL JOIN parlamentar WHERE id_votacao not in 
		(SELECT id_votacao FROM votacao_secreta) GROUP BY id_parlamentar)l
		WHERE total >= 40 
	'''

	res = cursor.execute(sql_command).fetchall()
	for parlamentar in res:
		parlamentares[parlamentar[0]] = "%.2f" %(parlamentar[1] *100/parlamentar[2])

	sql_command = '''
		SELECT nome 
		FROM parlamentar'''

	res = cursor.execute(sql_command).fetchall()
	for parlamentar in res:
		if parlamentar[0] not in parlamentares.keys():
			parlamentares[parlamentar[0]] = 'NA'

	conn.close()
	return parlamentares