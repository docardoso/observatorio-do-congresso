import sqlite3 as sql
import time
import utility as ut

# CONST GLOBAIS DE TEMPO
data_atual = time.localtime()[0:3]
DATA_INICIO = '2010-02-24'
DATA_FIM = '{}-{}-{}'.format(data_atual[0], data_atual[1], data_atual[2])

def indice_equilibrio(lista):
	""" Calcula o índice de equilíbrio da votação. 
	Recebe uma lista de valores associados aos números de votos em cada legenda. """

	return 100 - (max(lista) * 100/81)


def indice_competitividade(lista, tipo):
	""" Calcula o índice de competitividade da votação
	Recebe uma lista de valores associados aos números de votos em cada legenda 
	e qual tipo de índice se quer gerar."""
	
	lista = sorted(lista, reverse = True)
	if tipo == 'r':
		try:
			return lista[1]*100/lista[0]
		except ZeroDivisionError:
			return 0

	if tipo == 's': return lista[0]-lista[1]


def info_periodo(info, data_in = DATA_INICIO, data_fim = DATA_FIM):
	""" Recebe um iteravel (info) com o nome da tabela (materia ou votacao)
	e nome da coluna referente ao atributo de tempo da tabela, além de uma data inicial
	e uma data final.
	Retorna uma lista com a data e o número de info (matérias ou votações) que ocorreram naquela data"""

	conn = sql.connect("py_politica.db")
	cursor = conn.cursor()

	sql_command = '''
		SELECT date({}) as tmp, count(*)
		FROM {}
		WHERE tmp >= '{}' AND
			tmp <= '{}'
		GROUP BY tmp
		ORDER BY tmp;
	'''
	res = cursor.execute(sql_command.format(info[1], info[0], data_in,data_fim)).fetchall()
	res = [list(info) for info in res]
	conn.close()
	return res


def tipo_voto():
	""" Retorna um dicionário cuja a chave é o tipo de legenda do voto e o valor é quantas vezes
	ele apareceu nas votações.

	Só retorna legendas que apareceram mais de 200 vezes;
	Ouve um agrupamento das licenças e das legendas referentes aos votos do presidente do SF;
	"""

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
		
	'''

	res = ut.sql_dict(sql_command)
	exe = [key for key in res if 'Presidente' in key]
	for k in exe:
		res['Presidente'] = res.pop(k)
	
	exe = [key for key in res if 'L' in key[0]]
	for k in exe:
		res['Licença'] = res.pop(k)
			
	res = sorted(res.items(), key=lambda kv: kv[1], reverse=True)
	
	return res 