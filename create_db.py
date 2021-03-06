import asyncio as asy
import async_lib as asl
import get_dados as gd
import sqlite3 as sql

conn = sql.connect("py_politica.db") # Conexão com o BD;
cursor = conn.cursor() # Criação de um cursor para realizar 

cursor.executescript('''
	CREATE TABLE partido( 
		id_partido varchar primary key,
		sigla varchar not null,
		nome varchar not null,
		data_criacao date not null);

	CREATE TABLE parlamentar( 
		id_parlamentar varchar primary key,
		nome varchar null,
		casa char null);

	CREATE TABLE filiacao( 
		id_parlamentar varchar not null,
		id_partido varchar not null,
		data_filiacao date not null,
		data_desfiliacao date null,
		primary key(id_parlamentar, id_partido, data_filiacao),
		foreign key(id_parlamentar) references parlamentar(id_parlamentar) ON DELETE CASCADE,
		foreign key(id_partido) references partido(id_partido));

	CREATE TABLE mandato(
		id_parlamentar varchar not null,
		id_mandato varchar not null,
		descricao varchar null,
		data_inicio date not null,
		data_fim date not null,
		uf varchar null,
		primary key (id_parlamentar, id_mandato),
		foreign key (id_parlamentar) references parlamentar(id_parlamentar) ON DELETE CASCADE);
	
	CREATE TABLE materia( 
		id_materia varchar primary key,
		tipo varchar null,
		numero integer null,
		data_apresentacao date null,
		natureza varchar null,
		assunto_geral varchar null,
		assunto_especifico varchar null);

	CREATE TABLE index_materia(
		id_materia varchar not null,
		indice varchar not null,
		primary key (id_materia, indice),
		foreign key (id_materia) references materia (id_materia	));

	CREATE TABLE autoria(
		tipo_autor varchar not null,
		id_materia varchar not null,
		autor varchar null,
		id_parlamentar varchar null,
		primary key(tipo_autor, id_materia),
		foreign key(id_parlamentar) references parlamentar (id_parlametar) ON DELETE CASCADE,
		foreign key(id_materia) references parlamentar (id_materia));
	
	CREATE TABLE votacao( 
		id_votacao varchar primary key,
		id_materia varchar null,
		dataHoraInicio datetime not null,
		resultado varchar null,
		foreign key(id_materia) references materia(id_materia));

	CREATE TABLE votacao_secreta( 
		id_votacao varchar not null,
		placarSim integer null,
		placarNao integer null,
		placarAbs integer null,
		primary key(id_votacao),
		foreign key(id_votacao) references votacao(id_votacao));
		
	CREATE TABLE voto( 
		id_parlamentar varchar not null,
		id_votacao varchar not null,
		descricao integer not null,
		primary key(id_parlamentar, id_votacao),
		foreign key (id_parlamentar) references parlamentar(id_parlamentar) ON DELETE CASCADE,
		foreign key (id_votacao) references votacao(id_votacao));
		
	CREATE TABLE estatisticas_votacao(
		id_votacao varchar primary key,
		total_sim integer null,
		total_nao integer null,
		total_abs integer null,
		indice_equilibrio real null,
		competitividade_r real null,
		competitividade_s integer null,
		entropia real null,
		foreign key (id_votacao) references votacao (id_votacao));''')

conn.commit()



loop = asy.get_event_loop()
loop.run_until_complete(asl.async_materia())
loop.run_until_complete(asl.async_votacao())
parlamentares = cursor.execute('''SELECT id_parlamentar FROM parlamentar''').fetchall()
loop.run_until_complete(asl.async_info(parlamentares, 'filiacoes'))
loop.run_until_complete(asl.async_info(parlamentares, 'mandatos'))
materias = cursor.execute('SELECT id_materia FROM materia').fetchall()
loop.run_until_complete(asl.async_assunto(materias))
loop.close()

gd.insert_partidos()
gd.delete_suplente()
gd.insert_est_votacao()
gd.insert_est_votacao_secreta()

conn.close()