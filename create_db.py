'''Versão 1.1.1'''
import sqlite3 as sql

con = sql.connect('py_politica.db')

con.cursor().executescript('''
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
		assunto_especifico varchar null,
		ementa varchar null,
		apelido varchar null,
		status varchar null);

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

con.commit()
con.close()