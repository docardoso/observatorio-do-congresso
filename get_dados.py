#Versão 2.2.0
import sqlite3
from bs4 import BeautifulSoup
import requests
import scipy.stats as sct
import re
import async_lib as asl
from utility import get_text_alt, insert
import votacao as vt

# Função de recolhimento de dados da API e inserção de informações no BD
def insert_partidos():
	URL = 'http://legis.senado.leg.br/dadosabertos/senador/partidos'
	req = requests.get(URL).text
	partidos = BeautifulSoup(req, 'lxml')
	for partido in partidos.find_all('partido'):
		id_partido = partido.find('codigo').text
		sigla = partido.find('sigla').text
		nome = partido.find('nome').text
		data_criacao = partido.find('datacriacao').text
		info = (id_partido, sigla, nome, data_criacao)
		
		insert('partido', info)
	
# Funções de Seleção de informações e inserção no BD
def insert_materias(lista_materias):
	for materias in lista_materias:
		for materia in materias.find_all('materia'):
			id_materia = materia.find('codigomateria').text
			tipo = materia.find('siglasubtipomateria').text
			numero = materia.find('numeromateria').text
			data_apresentacao = materia.find('dataapresentacao').text
			natureza = get_text_alt(materia, 'nomenatureza')
			info = (id_materia, tipo, numero, data_apresentacao, natureza)
			
			insert('materia', info, 'id_materia, tipo, numero, data_apresentacao, natureza')

			insert_autor(id_materia, materia)

			try:
				index = get_text_alt(materia, 'indexacaomateria')
				insert_index(id_materia, index)
				
			except TypeError:
				pass

		
def insert_index(id_materia, index):
	p = re.compile(r'[^\w, ]')
	index = p.sub('', index).split(', ')
	for i in index:
		insert('index_materia', (id_materia, i.strip()))

def insert_autor(id_materia, materia):
	for autor in materia.find_all('autorprincipal'):
		nome_autor = get_text_alt(autor, 'nomeautor')
		tipo_autor = autor.find('siglatipoautor').text
		parlamentar = get_text_alt(autor, 'codigoparlamentar')
		autor = (tipo_autor, id_materia, nome_autor, parlamentar)
		insert('autoria', autor)

def insert_voto(id_votacao, voto):
		id_parlamentar = voto.find('codigoparlamentar').text
		descricao = voto.find('voto').text
		voto = (id_parlamentar, id_votacao, descricao)
		insert('voto',voto)

def insert_parlamentar(info):
	id_parlamentar = info.find('codigoparlamentar').text
	nome = info.find('nomeparlamentar').text
	info = (id_parlamentar, nome, 'SF')
	insert('parlamentar', info)

def insert_votacao_secreta(id_votacao, votacao):
	placar_sim = get_text_alt(votacao, 'totalvotossim')
	placar_nao = get_text_alt(votacao, 'totalvotosnao')
	placar_abs = get_text_alt(votacao, 'totalvotosabstencao')
	info = (id_votacao, placar_sim, placar_nao, placar_abs)
	insert('votacao_secreta', info)

def insert_votacao(listas_votacoes):
	for votacoes in listas_votacoes:
		for votacao in votacoes.find_all('votacao'):
			id_votacao = votacao.find('codigosessaovotacao').text
			id_materia = get_text_alt(votacao,'codigomateria')
			resultado = get_text_alt(votacao,'resultado')
			dataHorainicio = '{} {}:00'.format(votacao.find('datasessao').text, votacao.find("horainicio").text)
			info = (id_votacao, id_materia, dataHorainicio, resultado)
			insert('votacao', info)
			insert('estatisticas_votacao', (id_votacao,), 'id_votacao')
			if votacao.find('secreta').text == 'S':
				insert_votacao_secreta(id_votacao, votacao)

			for voto in votacao.find_all('votoparlamentar'):
				insert_voto(id_votacao, voto)
				insert_parlamentar(voto)
			
def insert_filiacao(lista_filiacoes):
	for filiacoes in lista_filiacoes:
		# print(filiacoes)
		parlamentar = filiacoes.find('codigoparlamentar').text

		for filiacao in filiacoes.find_all('filiacao'):
			id_partido = filiacao.find('codigopartido').text
			data_filia = filiacao.find('datafiliacao').text
			data_desfilia = get_text_alt(filiacao, 'datadesfiliacao')
			info = (parlamentar, id_partido, data_filia, data_desfilia)
			insert('filiacao', info)
		

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
		
			insert('mandato', info)

def insert_assunto(list_assuntos):
	conn = sqlite3.connect("py_politica.db") # Conexão com o BD;
	cursor = conn.cursor() # Criação de um cursor para realizar operações no BD;

	for assunto in list_assuntos:
		try:
			cursor.execute('''
				UPDATE materia 
				SET assunto_geral = '{}', assunto_especifico = '{}'
				WHERE id_materia = '{}' '''.format(assunto[1], assunto[2], assunto[0]))

			conn.commit()

		except sqlite3.IntegrityError:
			pass

	conn.close()

#Outras Funções de manipulação do BD
def delete_suplente():
	conn = sqlite3.connect("py_politica.db") # Conexão com o BD;
	cursor = conn.cursor() # Criação de um cursor para realizar operações no BD;
	sql_command = '''
		DELETE FROM parlamentar
		WHERE id_parlamentar NOT IN (
			SELECT DISTINCT id_parlamentar
			FROM mandato
			WHERE descricao = 'Titular')
	'''
	cursor.execute(sql_command)
	conn.commit()
	conn.close()

def insert_est_votacao():
	conn = sqlite3.connect("py_politica.db") # Conexão com o BD;
	cursor = conn.cursor() # Criação de um cursor para realizar operações no BD;
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
		try:
			votacao_info.get(info[0]).append(info[1:])

		except AttributeError:
			votacao_info[info[0]] = [info[1:]]
	
	for info in votacao_info:
		total_sim = 0 
		total_nao = 0 
		total_abs = 0 
		
		for total in votacao_info[info]:	
			if total[0] == 'Sim': total_sim = total[1]
			elif total[0] == 'Não': total_nao = total[1]
			elif total[0] == 'Abstenção' or total[0] == 'P-NRV': total_abs += total[1]

		totais = [int(x[1]) for x in votacao_info[info]]
		comp_r = vt.indice_competitividade([total_sim, total_nao], 'r')
		comp_s = vt.indice_competitividade([total_sim, total_nao], 's')
		indice_equilibrio = vt.indice_equilibrio(totais)
		entropia = sct.entropy(totais)

		sql_command = '''
			UPDATE estatisticas_votacao
			SET total_sim = {}, total_nao = {}, total_abs = {}, indice_equilibrio = {:.2f}, competitividade_r = {:.2f}, competitividade_s = {}, entropia = {:.3f}
			WHERE id_votacao = {}
		'''
		
		cursor.execute(sql_command.format(total_sim,total_nao,total_abs, indice_equilibrio, comp_r, comp_s, entropia, info))
	
	conn.commit()
	conn.close()
	
def insert_est_votacao_secreta():
	conn = sqlite3.connect("py_politica.db") # Conexão com o BD;
	cursor = conn.cursor() # Criação de um cursor para realizar operações no BD;
	sql_command = '''
		SELECT id_votacao, placarSim, placarNao, placarAbs, count (descricao)
		FROM votacao_secreta NATURAL JOIN voto 
		WHERE descricao = 'P-NRV'
		GROUP BY id_votacao, descricao
	'''

	infos = cursor.execute(sql_command).fetchall()
	votacao_info = {k[0]:k[1:] for k in infos}
		
	for info in votacao_info:
		total_sim = votacao_info[info][0]
		total_nao = votacao_info[info][1]
		total_abs = votacao_info[info][2] 
		if total_sim == None: total_sim = 0
		if total_nao == None: total_nao = 0
		if total_abs == None: total_abs = 0
		
		total_abs += votacao_info[info][3]
		
		totais = [total_sim, total_nao, total_abs] 
		comp_r = vt.indice_competitividade(totais, 'r')
		comp_s = vt.indice_competitividade(totais, 's')
		indice_equilibrio = vt.indice_equilibrio(totais)
		entropia = sct.entropy(totais)

		sql_command = '''
			UPDATE estatisticas_votacao
			SET total_sim = {}, total_nao = {}, total_abs = {}, indice_equilibrio = {:.2f}, competitividade_r = {:.2f}, competitividade_s = {}, entropia = {:.3f}
			WHERE id_votacao = {}
		'''
		cursor.execute(sql_command.format(total_sim, total_nao, total_abs, indice_equilibrio, comp_r, comp_s, entropia, info))

	conn.commit()
	conn.close()