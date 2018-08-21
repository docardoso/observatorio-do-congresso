#Versão 2.2.0
import sqlite3
import aiohttp as aio
from bs4 import BeautifulSoup
import asyncio as asy
import logging
import time
import requests
import scipy.stats as sct
import sts_lib as sts

conn = sqlite3.connect("py_politica.db") # Conexão com o BD;
cursor = conn.cursor() # Criação de um cursor para realizar operações no BD;
logging.getLogger('aiohttp.client').setLevel(logging.ERROR) # Mudança no nivel dos avisos do aiohttp;
tempo_atual = time.localtime() # Data corrente

def main():
	loop = asy.get_event_loop()
	loop.run_until_complete(async_materia())
	loop.run_until_complete(async_votacao())
	get_partidos()
	parlamentares = cursor.execute('''SELECT id_parlamentar FROM parlamentar''').fetchall()
	loop.run_until_complete(async_info(parlamentares, 'filiacoes'))
	loop.run_until_complete(async_info(parlamentares, 'mandatos'))
	loop.close()
	delete_suplente()
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
			for parlamentar in materia.find_all('codigoparlamentar'):
				try:
					cursor.execute('''INSERT INTO autoria (id_parlamentar, id_materia) VALUES (?,?);''', (parlamentar.text, id_materia))
				except sqlite3.IntegrityError:
					pass

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

def insert_filiacao(lista_filiacoes):
	for filiacoes in lista_filiacoes:
		parlamentar = filiacoes.find('codigoparlamentar').text

		for filiacao in filiacoes.find_all('filiacao'):
			id_partido = filiacao.find('codigopartido').text
			data_filia = filiacao.find('datafiliacao').text
			data_desfilia = get_text_alt(filiacao, 'datadesfiliacao')
			info = (parlamentar, id_partido, data_filia, data_desfilia)
		
			try:
				cursor.execute('''INSERT INTO filiacao (id_parlamentar, id_partido, data_filiacao, data_desfiliacao) VALUES (?,?,?,?);''', info)
			
			except sqlite3.IntegrityError:
				pass

		
	conn.commit()


def insert_mandatos(lista_mandatos):
	for mandatos in lista_mandatos:
		parlamentar = mandatos.find('codigoparlamentar').text
		for mandato in mandatos.find_all('mandato'):
			id_mandato = get_text_alt(mandato, 'codigomandato')
			participacao = get_text_alt(mandato, 'descricaoparticipacao')
			data_in = mandato.find('datainicio').text
			data_fim = mandato.find('datafim').text
			uf = mandato.find('ufparlamentar').text
			info = (parlamentar, id_mandato, participacao, data_in, data_fim, uf)
		
			try:
				cursor.execute('''INSERT INTO mandato (id_parlamentar, id_mandato, descricao, data_inicio, data_fim, uf) VALUES (?,?,?,?,?,?);''', info)
			
			except sqlite3.IntegrityError:
				pass

	conn.commit()

def delete_suplente():
	sql_command = '''
		DELETE FROM parlamentar
		WHERE id_parlamentar NOT IN (
			SELECT DISTINCT id_parlamentar
			FROM mandato
			WHERE descricao = 'Titular')
	'''

	cursor.execute(sql_command)

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
		ORDER BY id_votacao, count(*) desc
	'''	
	infos = cursor.execute(sql_command).fetchall()
	for info in infos:
		if info[0] in votacao_info.keys():
			votacao_info[info[0]].append((info[1],info[2]))
		
		else:
			votacao_info[info[0]] = [(info[1],info[2])]
	
	for info in votacao_info.keys():
		total_sim = 0 
		total_nao = 0 
		total_abs = 0 
		
		for total in votacao_info[info]:	
			if total[0] == 'Sim': total_sim = total[1]
			elif total[0] == 'Não': total_nao = total[1]
			elif total[0] == 'Abstenção' or total[0] == 'P-NRV': total_abs += total[1]

		eq = [x[1] for x in votacao_info[info]]
		entropia = [int(i[1]) for i in votacao_info[info]]
		comp_r = sts.competitividade([total_sim, total_nao], 'r')
		comp_s = sts.competitividade([total_sim, total_nao], 's')
		indice_equilibrio = sts.equilibrio(eq)
		entropia = sct.entropy(entropia)

		sql_command = '''
			UPDATE estatisticas_votacao
			SET total_sim = {}, total_nao = {}, total_abs = {}, indice_equilibrio = {:.2f}, competitividade_r = {:.2f}, competitividade_s = {}, entropia = {:.3f}
			WHERE id_votacao = {}
		'''
		
		cursor.execute(sql_command.format(total_sim,total_nao,total_abs, indice_equilibrio, comp_r, comp_s, entropia, info))
	
	conn.commit()
	
	votacao_info = {}
	sql_command = '''
		SELECT id_votacao, placarSim, placarNao, placarAbs, count (descricao)
		FROM votacao_secreta NATURAL JOIN voto 
		WHERE descricao = 'P-NRV'
		GROUP BY id_votacao, descricao
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
		
		total_abs += votacao_info[info][3]
		
		totais = [total_sim, total_nao, total_abs] 
		comp_r = sts.competitividade(totais[:2], 'r')
		comp_s = sts.competitividade(totais[:2], 's')
		entropia = sct.entropy(totais)
		indice_equilibrio = sts.equilibrio(totais)

		sql_command = '''
			UPDATE estatisticas_votacao
			SET total_sim = {}, total_nao = {}, total_abs = {}, indice_equilibrio = {:.2f}, competitividade_r = {:.2f}, competitividade_s = {}, entropia = {:.3f}
			WHERE id_votacao = {}
		'''
		cursor.execute(sql_command.format(total_sim, total_nao, total_abs, indice_equilibrio, comp_r, comp_s, entropia, info))

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
		
		try:
			cursor.execute('''INSERT INTO partido (id_partido, sigla, nome, data_criacao) VALUES (?,?,?,?);''', info)
		except sqlite3.IntegrityError:
			pass
			
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

async def get_info_parlamentar(parlamentar, info, session):
	URL = 'http://legis.senado.leg.br/dadosabertos/senador/{}/{}'
	async with session.get(URL.format(parlamentar, info)) as info:
		info = BeautifulSoup(await info.text(), 'lxml')
		return info

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


async def async_info(parlamentares, info):
	connector = aio.TCPConnector(limit=10)
	timeout = aio.ClientTimeout(total=60*60)
	async with aio.ClientSession(trust_env=True, timeout=timeout, connector=connector) as session:
		res = [get_info_parlamentar(parlamentar[0], info, session) for parlamentar in parlamentares]
		res = await asy.gather(*res)
		if info == 'filiacoes':
			insert_filiacao(res)
		
		elif info == 'mandatos':
			insert_mandatos(res)

main()