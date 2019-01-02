import time
import sqlite3 as sql
from bs4 import BeautifulSoup

# CONST GLOBAIS DE TEMPO
data_atual = time.localtime()[0:3]
DATA_INICIO = '2010-02-24'
DATA_FIM = '{}-{}-{}'.format(data_atual[0], data_atual[1], data_atual[2])

# Constantes SQL
sql_command_total = '''
		SELECT nome, count(*) as qtd 
		FROM parlamentar NATURAL JOIN voto
		GROUP BY id_parlamentar
		ORDER BY id_parlamentar;
		'''
sql_command_valido = '''
	SELECT nome, count(*) as validos 
	FROM parlamentar NATURAL JOIN voto
	WHERE descricao = 'Sim' or descricao = 'Não' or descricao = 'Abstenção'
	GROUP BY id_parlamentar
	ORDER BY id_parlamentar;
	'''	

sql_command_ausencia = '''
	SELECT nome, count(*) as ausencias
	FROM parlamentar NATURAL JOIN voto
	WHERE descricao != 'Sim' and descricao != 'Não' and 
	descricao != 'Abstenção'and descricao != 'P-NRV' and 
	descricao != 'P-OD' and descricao != 'Votou'
	GROUP BY id_parlamentar
	ORDER BY id_parlamentar;
'''
sql_command_justificada = ''' 
	SELECT nome, count(*) as a_justificada
	FROM parlamentar NATURAL JOIN voto
	WHERE descricao != 'Sim' and descricao != 'Não' and 
	descricao != 'Abstenção' and descricao != 'NCom' and 
	descricao != 'NA' and descricao != 'P-NRV' and 
	descricao != 'P-OD' and descricao != 'Votou'
	GROUP BY id_parlamentar
	ORDER BY id_parlamentar;
'''

def get_text_alt(elem, tag, alt=None):
	try:
		return elem.find(tag).text
	except AttributeError:
		return alt

def insert(tabela, info, esquema=None):
	conn = sql.connect("py_politica.db")
	cursor = conn.cursor()
	col = ','.join('?'*len(info))
	if esquema == None:
		sql_command = '''INSERT INTO {} VALUES ({});'''.format(tabela, col)
	else:
		sql_command = '''INSERT INTO {} ({}) VALUES ({});'''.format(tabela, esquema, col)

	try:
		cursor.execute(sql_command, info)
		conn.commit()
		conn.close()
	except sql.IntegrityError:
		pass
	

def converte_data(data_string):
	""" Converte as data_strings em milisegundos a partir da epoch"""
	
	return time.mktime(time.strptime(data_string , '%Y-%m-%d'))

def converte_id_votacao(id_votacao):
	""" Converte o id das votações, encontrados na API, em composições de tipo, número e ano
	da matéria que está sendo votada. Caso a votação não seja associada a uma matéria, retorna-se 
	o id da API. """

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
	#Tratamento para quando a votação não possui matéria associada
	try:
		id_votacao = '{} {}/{}'.format(votacao[0], votacao[1], votacao[2])
		return id_votacao

	except TypeError:
		return id_votacao

def sql_dict(sql_command):
	""" Recebe uma string com o código sql da consulta (que deve retornar 2 atributos) e retorna
	um dict, onde o primeiro atributo retornado pela consulta é a chave do dict e o segundo e o valor."""

	conn = sql.connect("py_politica.db")
	cursor = conn.cursor()
	total = cursor.execute(sql_command).fetchall()
	total = {k:v for k,v in total}
	conn.close()
	return total
