"""	
	Módulo que contem as funções async que são responsaveis por fazer as requisições da web, 
	a fim de obter as informações que serão inseridas no BD.
"""


import sqlite3
import aiohttp as aio
from bs4 import BeautifulSoup
import asyncio as asy
import logging
import time
from utility import get_text_alt
import get_dados as gd

conn = sqlite3.connect("py_politica.db") # Conexão com o BD;
cursor = conn.cursor() # Criação de um cursor para realizar operações no BD;
logging.getLogger('aiohttp.client').setLevel(logging.ERROR) # Mudança no nivel dos avisos do aiohttp;
tempo_atual = time.localtime() # Data corrente

async def async_materia():
	"""
		Função responsável por fazer as requisições na API referente as informações das matérias 
	"""
	connector = aio.TCPConnector(limit=5) # Número de conexões 
	timeout = aio.ClientTimeout(total=60*60) # Tempo máximo de espera por resposta
	async with aio.ClientSession(trust_env = True, timeout=timeout, connector=connector) as session:
		URL = 'http://legis.senado.leg.br/dadosabertos/materia/pesquisa/lista?ano={}'
		materias = [get_info(URL, session, ano) for ano in range(2010, tempo_atual[0]+1)]
		gd.insert_materias(await asy.gather(*materias))

async def async_votacao():
	"""
		Função responsável por fazer as requisições na API referente as informações das matérias
	"""
	connector = aio.TCPConnector(limit=3)
	timeout = aio.ClientTimeout(total=60*60)
	async with aio.ClientSession(trust_env=True, timeout=timeout, connector=connector) as session:
		URL = 'http://legis.senado.leg.br/dadosabertos/plenario/lista/votacao/{}/{}'
		for ano in range(2010,tempo_atual[0]+1):
			votacoes = list()
			for mes in range(1,12):
				data_in ='{}{:02d}02'.format(ano,mes)
				data_fim = '{}{:02d}01'.format(ano,mes+1)
				votacoes.append(get_info(URL, session, data_in, data_fim))
		
			gd.insert_votacao(await asy.gather(*votacoes))

async def async_info(parlamentares, info):
	connector = aio.TCPConnector(limit=5)
	timeout = aio.ClientTimeout(total=60*60)
	async with aio.ClientSession(trust_env=True, timeout=timeout, connector=connector) as session:
		print(parlamentares)
		URL = 'http://legis.senado.leg.br/dadosabertos/senador/{}/{}'
		res = [get_info(URL, session, parlamentar[0], info) for parlamentar in parlamentares]
		res = await asy.gather(*res)
		if info == 'filiacoes': gd.insert_filiacao(res)
		if info == 'mandatos': gd.insert_mandatos(res)	

async def async_assunto(lista_materia):
	connector = aio.TCPConnector(limit=5)
	timeout = aio.ClientTimeout(total=60*60)
	async with aio.ClientSession(trust_env=True, timeout=timeout, connector=connector) as session:
		URL = 'http://legis.senado.leg.br/dadosabertos/materia/{}'
		# assunto = [get_info(URL, session, materia[0]) for materia in lista_materia]
		assunto = [get_assunto(materia[0], URL, session) for materia in lista_materia]
		gd.insert_assunto(await asy.gather(*assunto))
		

async def get_info(url, session, *args):
	async with session.get(url.format(*args)) as info:
		info = BeautifulSoup(await info.text(), 'lxml')
		return info

async def get_assunto(id_materia, url, session):
	async with session.get(url.format(id_materia)) as assunto:
		assunto = BeautifulSoup(await assunto.text(), 'lxml')
		assunto_g = get_text_alt(assunto, 'assuntogeral')
		assunto_e = get_text_alt(assunto, 'assuntoespecifico')

		return (id_materia, assunto_g, assunto_e)