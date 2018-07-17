#Versão 2.2.0
import sqlite3
import aiohttp as aio
from bs4 import BeautifulSoup
import asyncio as asy
import logging
import time
import requests
import scipy.stats as st

conn = sqlite3.connect("py_politica.db") # Conexão com o BD;
cursor = conn.cursor() # Criação de um cursor para realizar operações no BD;
logging.getLogger('aiohttp.client').setLevel(logging.ERROR) # Mudança no nivel dos avisos do aiohttp;
tempo_atual = time.localtime() # Data corrente

def main():
	loop = asy.get_event_loop()
	loop.run_until_complete(async_materia())
	loop.run_until_complete(async_votacao())
	loop.close()
	create_ranking_votacao()

def get_text_alt(elem, tag, alt=None):
	try:
		return elem.find(tag).text
	except AttributeError:
		return alt

def insert_materias(lista_materias):
	for materias in lista_materias:
		for materia in materias.find_all('materia'):
			id_materia = materia.find('codigomateria').text
			tipo = materia.find('siglasubtipomateria').text
			numero = materia.find('numeromateria').text
			data_apresentacao = materia.find('dataapresentacao').text
			info = (id_materia, tipo, numero, data_apresentacao)

			try:
				cursor.execute('''INSERT INTO materia (id_materia, tipo, numero, data_apresentacao) VALUES (?,?,?,?);''', info)
			except sqlite3.IntegrityError:
				pass

		conn.commit()

def insert_votacao(listas_votacoes):
	
	for votacoes in listas_votacoes:
		for votacao in votacoes.find_all('votacao'):
			id_votacao = votacao.find('codigosessaovotacao').text
			id_materia = get_text_alt(votacao,'codigomateria')
			resultado = get_text_alt(votacao,'resultado')
			dataHorainicio = votacao.find('datasessao').text + ' ' + votacao.find("horainicio").text + ":00"
			info = (id_votacao, id_materia, dataHorainicio, resultado)
			try:
				cursor.execute('''INSERT INTO votacao (id_votacao, id_materia, dataHorainicio, resultado) VALUES (?,?,?,?);''', info)
			except sqlite3.IntegrityError:
				pass

			try:
				cursor.execute('''INSERT INTO estatisticas_votacao (id_votacao) VALUES (?);''', (id_votacao,))
			except sqlite3.IntegrityError:
				pass

			for voto in votacao.find_all('votoparlamentar'):
				id_parlamentar = voto.find('codigoparlamentar').text
				nome = voto.find('nomeparlamentar').text
				descricao = voto.find('voto').text
				info = (id_parlamentar, id_votacao, descricao)
				try:
					cursor.execute('''INSERT INTO voto (id_parlamentar, id_votacao, descricao) VALUES (?,?,?);''', info)
				except sqlite3.IntegrityError:
					pass
				
				try:
					cursor.execute('''INSERT INTO parlamentar (id_parlamentar, nome, casa) VALUES (?,?,?);''', (id_parlamentar, nome,'SF'))
				except sqlite3.IntegrityError:
					pass

			if votacao.find('secreta').text == 'S':
				placar_sim = get_text_alt(votacao, 'totalvotossim')
				placar_nao = get_text_alt(votacao, 'totalvotosnao')
				placar_abs = get_text_alt(votacao, 'totalvotosabstencao')
				info = (id_votacao, placar_sim, placar_nao, placar_abs)
				try:
					cursor.execute('''INSERT INTO votacao_secreta (id_votacao, placarSim, placarNao, placarAbs) VALUES (?,?,?,?);''', info)
				except sqlite3.IntegrityError:
					pass

			conn.commit()
		
	print(bug, bug2, bug-bug2)
		
def create_ranking_votacao():
	votacao_info = dict()

	sql_command = '''
		SELECT id_votacao, descricao, count(*) 
		FROM voto 
		WHERE id_votacao IN
			(SELECT id_votacao 
			FROM votacao 
			WHERE id_votacao NOT IN
				(SELECT id_votacao 
				FROM votacao_secreta)) 
		GROUP BY id_votacao, descricao
		ORDER BY count(*) desc
	'''	
	infos = cursor.execute(sql_command).fetchall()
	for info in infos:
		if info[0] in votacao_info.keys():
			votacao_info[info[0]].append((info[1],info[2]))
		
		else:
			votacao_info[info[0]] = [(info[1],info[2])]
	
	for info in votacao_info.keys():
		maximo = max([i[1] for i in votacao_info[info]])
		total = sum([i[1] for i in votacao_info[info]])
		total_sim = [i[1] for i in votacao_info[info] if i[0] == 'Sim']
		total_nao = [i[1] for i in votacao_info[info] if i[0] == 'Não']
		total_abs = [i[1] for i in votacao_info[info] if i[0] == 'Abstenção']
		competitividade_r = "%.2f" %(votacao_info[info][1][1]*100/votacao_info[info][0][1])
		competitividade_s = votacao_info[info][0][1]-votacao_info[info][1][1]
		entropia = [int(i[1]) for i in votacao_info[info]]
		entropia = "%.2f" %(st.entropy(entropia))
		if total_sim == []: total_sim = [0]
		if total_nao == []: total_nao = [0]
		if total_abs == []: total_abs = [0]
		indice_equilibrio = "%.2f" %(100 - maximo*100/total)
		sql_command = '''
			UPDATE estatisticas_votacao
			SET total_sim = {}, total_nao = {}, total_abs = {}, indice_equilibrio = {}, competitividade_r = {}, competitividade_s = {}, entropia = {}
			WHERE id_votacao = {}
		'''
		
		cursor.execute(sql_command.format(total_sim[0],total_nao[0],total_abs[0], indice_equilibrio, competitividade_r, competitividade_s, entropia, info))
	
	conn.commit()
	
	votacao_info = {}
	sql_command = '''
		SELECT id_votacao, placarSim, placarNao, placarAbs, count (descricao)
		FROM votacao_secreta NATURAL JOIN voto 
		GROUP BY id_votacao
	'''
	infos = cursor.execute(sql_command).fetchall()
	for info in infos:
		votacao_info[info[0]] = info[1:]
		

	for info in votacao_info.keys():
		total_sim = votacao_info[info][0]
		total_nao = votacao_info[info][1]
		total_abs = votacao_info[info][2]
		if total_sim == None: total_sim = 0
		if total_nao == None: total_nao = 0
		if total_abs == None: total_abs = 0
		
		indice_equilibrio = "%.2f" %(100 - max([total_sim, total_nao, total_abs])*100/votacao_info[info][3])
		competitividade = sorted([total_sim, total_nao, total_abs], reverse= True)
		competitividade_r = "%.2f" %(competitividade[1] * 100/competitividade[0])
		competitividade_s = competitividade[0] - competitividade[1]
		entropia = "%.3f" %(st.entropy(competitividade))

		sql_command = '''
			UPDATE estatisticas_votacao
			SET total_sim = {}, total_nao = {}, total_abs = {}, indice_equilibrio = {}, competitividade_r = {}, competitividade_s = {}, entropia = {}
			WHERE id_votacao = {}
		'''
		cursor.execute(sql_command.format(total_sim, total_nao, total_abs, indice_equilibrio, competitividade_r, competitividade_s, entropia, info))

	conn.commit()
				
def get_partidos():
	URL = 'http://legis.senado.leg.br/dadosabertos/senador/partidos'
	req = requests.get(URL).text
	partidos = BeautifulSoup(req, 'lxml')
	for partido in partidos.find_all('partido'):
		id_partido = partido.find('codigo').text
		sigla = partido.find('sigla').text
		nome = partido.find('nome').text
		data_criacao = partido.find('datacriacao').text
		info = (id_partido, sigla, nome, data_criacao)
		cursor.execute('''INSERT INTO partido (id_partido, sigla, nome, data_criacao) VALUES (?,?,?,?);''', info)
	
	conn.commit()

async def get_materia(ano, session):
	URL = 'http://legis.senado.leg.br/dadosabertos/materia/pesquisa/lista?ano={}'
	async with session.get(URL.format(ano)) as materias:
		materias = BeautifulSoup(await materias.text(), 'lxml')
		return materias

async def get_votacao(data_in, data_fim, session):
	URL = 'http://legis.senado.leg.br/dadosabertos/plenario/lista/votacao/{}/{}'
	async with session.get(URL.format(data_in, data_fim)) as listas_votacoes:
		listas_votacoes = BeautifulSoup(await listas_votacoes.text(), 'lxml')
		return listas_votacoes

async def async_materia():
	async with aio.ClientSession(trust_env = True) as session:
		materias = [get_materia(ano, session) for ano in range(2010, tempo_atual[0]+1)]
		materias = await asy.gather(*materias)
		insert_materias(materias)

async def async_votacao():
	votacoes = list()
	connector = aio.TCPConnector(limit=10)
	timeout = aio.ClientTimeout(total=60*60)
	async with aio.ClientSession(trust_env=True, timeout=timeout, connector=connector) as session:
		for ano in range(2010,tempo_atual[0]+1):
			for mes in range(1,12):
				data_in ='{}{:02d}02'.format(ano,mes)
				data_fim = '{}{:02d}01'.format(ano,mes+1)
				votacoes.append(get_votacao(data_in, data_fim, session))
		
		votacoes = await asy.gather(*votacoes)
		insert_votacao(votacoes)

main()