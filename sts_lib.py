# Versão 1.2.3
import imp
import sqlite3 as sql
import pickle
import scipy.stats as st
from scipy.sparse import csr_matrix
from matplotlib import pyplot as pp
import numpy as np
import time
import pprint
from sklearn.naive_bayes import BernoulliNB
import sklearn.metrics as metrics
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
import utility

# CONST GLOBAIS DE TEMPO
data_atual = time.localtime()[0:3]
DATA_INICIO = '2010-02-24'
DATA_FIM = '{}-{}-{}'.format(data_atual[0], data_atual[1], data_atual[2])

# Funções Relacionadas à índices das votações


# Função Temporal



# def bubble_chart():
# 	conn = sql.connect('py_politica.db')
# 	cursor = conn.cursor()
# 	list_return = list()

# 	sql_command = '''
# 		select assunto_geral, count(*)
# 		from materia
# 		group by assunto_geral
# 		order by count(*) desc
# 	'''

# 	res = cursor.execute(sql_command).fetchall()
# 	temas = {tema[0]:[tema[1],0,0] for tema in res}

# 	sql_command = '''
# 		select assunto_geral, count(*)
# 		from materia
# 		where id_materia in (select id_materia from votacao)
# 		group by assunto_geral	
# 		order by count(*) desc
# 	'''

# 	res = cursor.execute(sql_command).fetchall()
# 	for tema in res:
# 		temas[tema[0]][1] = tema[1]

# 	sql_command = '''
# 		select assunto_geral, avg(abs_media)
# 		from materia natural join (
# 		select id_materia, avg(qtd) abs_media
# 		from votacao natural join (
# 			select id_votacao, count(*) as qtd
# 			from voto
# 			where descricao = "P-NRV" or descricao = "Absteção"
# 			group by id_votacao)r
			
# 		group by id_materia
# 		)s
# 		group by assunto_geral
# 		order by avg(abs_media) 
# 	'''

# 	res = cursor.execute(sql_command).fetchall()
# 	for tema in res:
# 		temas[tema[0]][2] = tema[1]

# 	for k in temas.keys():
# 		#if k is None:
# 		#	continue

# 		tema = {'x': temas[k][0], 'y': temas[k][1], 'z': temas[k][2], 'name': k}
# 		list_return.append(tema)
	
# 	return list_return

# def missing():
# 	conn = sql.connect('py_politica.db')
# 	cursor = conn.cursor()
# 	indices = cursor.execute('select distinct indice from index_materia').fetchall()
# 	materias = cursor.execute('select id_materia, assunto_especifico from materia where assunto_especifico != "None"').fetchall()
	
# 	indices = [indice[0] for indice in indices]
# 	ypi = {k:v for v,k in enumerate(indices)}

# 	assuntos = [0 for materia in materias]
# 	ypm = {k[0]:v for v,k in enumerate(materias)}

# 	for materia in materias:
# 		assuntos[ypm[materia[0]]] = materia[1]

# 	matriz = np.zeros((len(materias), len(indices)), bool)
# 	materias = cursor.execute('''
# 		select id_materia, assunto_especifico, indice 
# 		from materia natural join index_materia 
# 		where assunto_especifico != 'None' 
# 		order by id_materia''').fetchall()	

# 	for materia in materias:
# 		matriz[ypm[materia[0]]][ypi[materia[2]]] = 1

# 	matriz = csr_matrix(matriz)
# 	print(matriz.shape)
# 	#clf = BernoulliNB()
# 	#clf = KNeighborsClassifier(1)
# 	clf = DecisionTreeClassifier()
# 	clf.fit(matriz[1000:], assuntos[1000:])
# 	yp = clf.predict(matriz[:1000])
# 	print(metrics.classification_report(assuntos[:1000], yp))
# 	import pdb; pdb.set_trace()


# # def exoterismo_computacional():
# # 	conn = sql.connect('py_politica.db')
# # 	cursor = conn.cursor()
# # 	indices_interesse = cursor.execute('')

# # missing()