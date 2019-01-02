import sqlite3 as sql
import time
import utility as ut

def get_nome():
	conn = sql.connect("py_politica.db")
	cursor = conn.cursor()
	sql_command = '''
		SELECT nome 
		FROM parlamentar'''

	res = cursor.execute(sql_command).fetchall()
	return [r[0] for r in res]


def assertividade_parlamentar():
	""" Calcula a assertividade dos parlamentares.\n
	Assertividade é dada pela quantidade de votos Sim e Não dividido pelo somatório de votos Sim, Não, Abstenções e P-NRV
	do parlamentar. O calculo só é realizado com totais de votos superiores a 40 votos e só leva em conta votações ostensivas"""

	conn = sql.connect("py_politica.db")
	cursor = conn.cursor()
	assertividade = dict()
	sql_command = '''
		SELECT nome, sum(qtd), total
		FROM (SELECT nome, count(*) as qtd
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
	assertividade = {key[0]:'{:.2f}'.format(key[1]*100/key[2]) if key[2]>=40 else '-' for key in res}

	conn.close()
	return assertividade

def indice_concordancia():
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
	parlamentares = {k:'{:.2f}'.format(v1*100/v2) for k,v1,v2 in res}
	
	conn.close()
	return parlamentares

def count_info(info):
	""" Recebe uma info que deve ser recuperada (filiação ou mandatos)
	e retorna um dicionário com o nome do parlamentar (key) e o count da info requerida
	(value). """

	sql_command = '''
		SELECT nome, count(*) 
		FROM {} NATURAL JOIN parlamentar
		GROUP BY id_parlamentar
	'''

	parlamentares = ut.sql_dict(sql_command.format(info))
		
	return parlamentares

def indice_trocas():
	filiacao = count_info('filiacao')
	mandato = count_info('mandato')

	return {k:'{:.2f}'.format(filiacao[k]/mandato[k]) for k in get_nome()}


def n_mat_propostas(votadas = True):
	""" Recebe um boleano que define se o retorno.
		Se votadas for verdadeiro retorna um dicionário cuja chave é o nome do parlamentar
		e o conteudo é o número de matérias propostas, pelo parlamentar, que foram votadas.
		Se votadas for falso retorna um dicionário cuja chave é o nome do parlamentar
		e o conteudo é o número total de matérias propostas pelo parlamentar."""

	sql_command_nvotadas = '''
		select nome, count(*) 
		from parlamentar NATURAL JOIN autoria 
		GROUP by id_parlamentar 
	'''

	sql_command_votadas = '''
		select nome, count(*) 
		from parlamentar NATURAL JOIN autoria 
		where id_materia in 
			(SELECT id_materia from votacao)
		GROUP by id_parlamentar 
	'''
	if votadas:
		res = ut.sql_dict(sql_command_votadas)

	else:
		res = ut.sql_dict(sql_command_nvotadas)

	return res