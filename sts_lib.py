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
	try:
		id_votacao = '{} {}/{}'.format(votacao[0], votacao[1], votacao[2])
		return id_votacao

	except TypeError:
		return id_votacao


# Funções Relacionadas às votações
def equilibrio(lista):
	maximo = max(lista)
	res = maximo * 100/81
	return 100 - res

def competitividade(lista, tipo):
	lista = sorted(lista, reverse = True)
	if tipo == 'r':
		try:
			return lista[1]*100/lista[0]
		except ZeroDivisionError:
			return 0

	if tipo == 's': return lista[0]-lista[1]

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
	""" Retorna o número de Matérias apresentadas numa faixa de tempo, podendo alternar o passo da contagem """

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
			ORDER BY date(data_apresentacao);
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
	""" Calcula a assertividade dos parlamentares.\n
	Assertividade é dada pela quantidade de votos Sim e Não dividido pelo somatório de votos Sim, Não, Abstenções e P-NRV
	do parlamentar. O calculo só é realizado com totais de votos superiores a 40 votos e só leva em conta votações ostensivas"""

	conn = sql.connect("py_politica.db")
	cursor = conn.cursor()
	parlamentares = dict()
	sql_command = '''
		SELECT nome, sum(qtd), total
		FROM (SELECT nome, descricao, count(*) as qtd 
			FROM parlamentar NATURAL JOIN voto
			WHERE descricao = 'Sim' or descricao = 'Não'
			GROUP BY id_parlamentar, descricao)r 
		NATURAL JOIN 
			(SELECT nome, count(*) as total
			FROM parlamentar NATURAL JOIN voto
			WHERE id_votacao not in 
				(SELECT id_votacao
				FROM votacao_secreta)
			and descricao = 'Sim' or descricao = 'Não' 
			or descricao = 'Abstenção' or descricao = 'P-NRV'
			GROUP BY id_parlamentar)l
		GROUP BY nome;

	'''
 
	res = cursor.execute(sql_command).fetchall()
	parlamentares = {key[0]:'{:.2f}'.format(key[1]*100/key[2]) if key[2]>=40 else '-' for key in res}
	sql_command = '''
		SELECT nome 
		FROM parlamentar'''

	res = cursor.execute(sql_command).fetchall()
	for parlamentar in res:
		if parlamentar[0] not in parlamentares.keys():
			parlamentares[parlamentar[0]] = '-'

	conn.close()
	return parlamentares

def totais_parlamentares():
	""" Calcula os totais de votos, efetívos e ausências (justificadas e não justificadas) """

	conn = sql.connect("py_politica.db")
	cursor = conn.cursor()
	parlamentares = dict()
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
	total = cursor.execute(sql_command_total).fetchall()
	valido = cursor.execute(sql_command_valido).fetchall()
	ausencia = cursor.execute(sql_command_ausencia).fetchall()
	justificada = cursor.execute(sql_command_justificada).fetchall()
	parlamentares = {parlamentar[0]:[parlamentar[1],0,0,0] for parlamentar in total}
	for parlamentar in valido:
		parlamentares[parlamentar[0]].pop(1)
		parlamentares[parlamentar[0]].insert(1,parlamentar[1])
	
	for parlamentar in ausencia:
		parlamentares[parlamentar[0]].pop(2)
		parlamentares[parlamentar[0]].insert(2,parlamentar[1])	

	for parlamentar in justificada:
		parlamentares[parlamentar[0]].pop(3)
		parlamentares[parlamentar[0]].insert(3,parlamentar[1])	

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
	""" Calcula uma porcentagem relacionada ao número de vezes que o voto de um parlamentar 
	concordou com o resultado de uma votação. Só leva em consideração votações ostensivas e parlamentares
	que tenham mais de 40 votos. Caso contrário registra-se '-'.\n
	Retorna uma lista de tuplas (parlamentar, porcentagem). """

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
			parlamentares[parlamentar[0]] = '-'

	conn.close()
	return parlamentares

def count_info(info):
	conn = sql.connect("py_politica.db")
	cursor = conn.cursor()
	parlamentares = dict()

	sql_command = '''
		SELECT nome, count(*) 
		FROM {} NATURAL JOIN parlamentar
		GROUP BY id_parlamentar
	'''

	res = cursor.execute(sql_command.format(info)).fetchall()
	for parlamentar in res:
		parlamentares[parlamentar[0]] = parlamentar[1]
		
	return parlamentares

def tipo_voto():
	
	conn = sql.connect("py_politica.db")
	cursor = conn.cursor()
	count = 0 
	sql_command = ''' 
		SELECT descricao, qtd
		FROM (SELECT descricao, count(*) as qtd
				FROM voto 
				WHERE descricao != 'Votou' and descricao not like 'L%'
				GROUP BY descricao)o
		WHERE qtd > 200
		
		UNION
		
		SELECT descricao, sum(qtd)
		FROM (SELECT descricao, count(*) as qtd
				FROM voto 
				WHERE descricao != 'Votou' and descricao not like 'L%'
				GROUP BY descricao)o
		WHERE qtd <= 200
		
		UNION 
		
		SELECT descricao, sum(qtd)
			FROM (SELECT descricao, count(*) as qtd
				FROM voto
				WHERE descricao like 'L%'
				GROUP BY descricao)l
		
		ORDER BY qtd DESC
	'''

	res = cursor.execute(sql_command).fetchall()
	res = list(map(list, res))
	for tipo in res:
		if 'Presidente' in tipo[0]:
			count += tipo[1]
			outros = ['Outros', count]
			res.remove(tipo)
			continue
		
		if 'L' == tipo[0][0]:
			tipo[0] = 'Licenças'
	
	res.append(outros)
	res = sorted(res, key=lambda res:res[1], reverse=True)
	return res 

def votacao_materia():
	conn = sql.connect("py_politica.db")
	cursor = conn.cursor()

	sql_command = '''
		SELECT qtd as num_v, count(*)
		FROM   (SELECT id_materia, count(id_votacao) as qtd
				FROM votacao NATURAL JOIN materia
				GROUP BY id_materia)r
		
		GROUP BY qtd
		ORDER BY qtd
	'''

	res = cursor.execute(sql_command).fetchall()
	return res

	# sql_command = '''
	# 	select *
	# 	from materia
	# 	where id_materia not in 
	# 	(select id_materia from votacao)'''

	# res = cursor.execute(sql_command).fetchall()
	# print(res)

