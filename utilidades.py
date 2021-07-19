"""
Rotinas de utilidade geral utilizadas no programa para otimizar o
RCA(distribuição dos desembolsos dos projetos de P&D do CENPES para o
cumprimento da obrigação legal) de forma eficiente, buscando minimizar o
valor excedente desenbolsado.

 Autor: MFB
 Atualizacao: 12/07/2021

"""

# Definicao de constantes e parametros:
TAMANHO_HISTORICO_MELHORES_INDIVIDUOS = 500
NOME_ABA_CONTRATOS_PLANILHA_SAIDA = "Contratos"
NOME_ABA_PROJETOS_PLANILHA_SAIDA = "Projetos Distribuídos"
NOME_ARQUIVO_MELHOR_INDIVIDUO = "melhor_individuo.rca"

import os
import pickle
import pandas as pd
import numpy as np
from deap import tools
# from deap import creator
import funcao_restricao as negocio


"""
funcao: carrega_consolida_individuo(individuo):

Objetivo: carrega o indivíduo no dataframe de projetos e realiza as
          consolidacoes necessarias para calcular a funcao objetivo e
          verificar as restricoes que representam as regras de negócio

Parametros:
            individuo: representacao de uma alocacao para
                       todos os projetos.
                       lista de numeros inteiros que sao os indices
                       dos contratos.

Retorna:
        df: dataframe com os contratos, as restricoes de negocio e
            os valores relevantes consolidados.

"""
def carrega_consolida_individuo(individuo, df_id_contratos,
                                df_contratos, df_projetos):
    # cria uma lista com as informacoes do individuo passado
    individuo_lista = individuo[:]

    # busca os nomes dos Contratos/Campos para carregar na alocacao
    # dos contratos
    df_individuo = pd.DataFrame(individuo_lista)
    df_individuo = df_individuo.rename(columns={0: "ID_Contrato"})
    df_individuo = pd.merge(df_individuo, df_id_contratos,
                            left_on="ID_Contrato",
                            right_on="ID_Contrato", how='left')

    # carrregar o individuo na coluna "Contratos" no dataframe dos projetos
    df_projetos["CONTRATO PRINC"] = df_individuo["Campo"]

    # consolidar os valores dos projetos alocados por contrato
    df_consolidado = pd.pivot_table(df_projetos, index="CONTRATO PRINC",
                                    values="Valor Pago(R$)",
                                    columns=["Classif"],
                                    aggfunc=np.sum)

    # substitui os valores inválidos por 0
    df_consolidado = df_consolidado.fillna(0)

    # inclui uma coluna "Total" com o total das colunas consolidadas
    # por contrato
    df_consolidado["TOTAL"] = df_consolidado["EXTERNO"] + \
                              df_consolidado["EMPRESA"] + \
                              df_consolidado["INTERNO"]

    # buscar os valores das restricoes de negocio de cada contrato
    df = pd.merge(df_contratos, df_consolidado, left_on="Campo",
                  right_index=True, how='left')

    # retira a linha referente ao contrato em branco, que representa
    # os projetos não alocados
    df = df[df["Campo"] != ""]

    df["Critério (TOTAL - Obrigação)"] = \
       df["TOTAL"] - df["Obrigação - PETROBRAS"]
    df["Criterio Mínimo Externo"] = \
       df["EXTERNO"] - df["Mínimo Externo"]
    df["Critério Máximo Interno"] = \
       df["Máximo Interno"] - df["INTERNO"]

    # inclui uma linha com os totais de cada coluna
    # "Total Geral"
    total_geral = df.sum()
    df = df.append(pd.DataFrame({"ID_Contrato": len(df),
                                 "Campo": "Total Geral",
                                 "Obrigação - PETROBRAS":
                                     total_geral["Obrigação - PETROBRAS"],
                                 "Mínimo Externo":
                                     total_geral["Mínimo Externo"],
                                 "Mínimo Empresa":
                                     total_geral["Mínimo Empresa"],
                                 "Máximo Interno":
                                     total_geral["Máximo Interno"],
                                 "EMPRESA": total_geral["EMPRESA"],
                                 "EXTERNO": total_geral["EXTERNO"],
                                 "INTERNO": total_geral["INTERNO"],
                                 "TOTAL": total_geral["TOTAL"],
                                 "Critério (TOTAL - Obrigação)":
                                     total_geral["Critério (TOTAL - Obrigação)"],
                                 "Criterio Mínimo Externo":
                                     total_geral["Criterio Mínimo Externo"],
                                 "Critério Máximo Interno":
                                     total_geral["Critério Máximo Interno"]},
                                index=[len(df)]))

    # exclui os valores positivos do "Critério Máximo Interno" por nao se
    # tratarem de uma penalidade, e nao faz sentido minimizar
    # df["Critério Máximo Interno"][df["Critério Máximo Interno"] > 0] = 0
    df.loc[df["Critério Máximo Interno"] > 0, "Critério Máximo Interno"] = 0

    return df


"""
funcao: le_planilha_entrada(planilha, aba_projetos, aba_contratos)

  Objetivo: Le a planilha com os dados de entrada, referente aos projetos e
            contratos, e organiza as informacoes em 4 dataframes.

  Parametros:
             planilha: Nome da planilha com os dados de entrada;
             aba_projetos: Nome da aba com os dados dos projetos;
             aba_contratos: Nome da aba com os dados dos contratos.

Retorna:
         df_projetos: dataframe apenas com as informacoes necessarias dos
                      projetos para realizar a otimizacao;
         df_contratos: dataframe com os contratos e as restricoes das 
                       regras de negocio;
         df_detalhes_projetos: dataframe com todas as informacoes dos
                               projetos contidas na planilha de entrada,
                               que serao replicadas na planilha de saida.
         df_id_contratos: dataframe com um indice para os contratos

"""
def le_planilha_entrada(planilha, aba_projetos, aba_contratos):
    df = pd.read_excel(planilha, sheet_name=[aba_projetos, aba_contratos],
                       header=0)
    df_detalhes_projetos = df[aba_projetos]
    df_projetos = df_detalhes_projetos[["Número ANP", "Valor Pago(R$)",
                                        "Irá fazer parte do RCA?", "Classif",
                                        "CONTRATO PRINC"]]

    # ### ATENCAO ### *** DESABILITADO TEMPORARIAMENTE ***
    # retira os projetos que foram marcados para nao entrar na distribuicao
    # pelo campo "Irá fazer parte do RCA?"
    projetos_excluidos = []
    # projetos_excluidos = df_projetos["Irá fazer parte do RCA?"] == False

    # monta dataframe apenas com os campos necessários relacionados aos
    # projetos:  "Campo", "Obrigação - PETROBRAS", "Mínimo Externo",
    # "Mínimo Empresa", "Máximo Interno".
    # inclui uma coluna com um indice numerico inteiro para cada contrato "ID_Contrato"

    df_contratos = df[aba_contratos]
    df_contratos = df_contratos[["Campo", "Obrigação - PETROBRAS",
                                 "Mínimo Externo", "Mínimo Empresa",
                                 "Máximo Interno"]]
    df_contratos.insert(0, "ID_Contrato", range(len(df_contratos)))

    # inclui um contrato em branco, para ser utilizado quando
    # o projeto NAO for alocado
    df_contratos = df_contratos.append(pd.DataFrame({"ID_Contrato": len(df_contratos),
                                                     "Campo": "", "Obrigação - PETROBRAS": 0,
                                                     "Mínimo Externo": 0, "Mínimo Empresa": 0,
                                                     "Máximo Interno": 0},
                                                    index=[len(df_contratos)]))

    # monta um dataframe com os indices dos contratos
    df_id_contratos = df_contratos[["ID_Contrato", "Campo"]]

    return df_projetos.copy(), df_detalhes_projetos.copy(), projetos_excluidos,\
           df_contratos.copy(), df_id_contratos.copy()


"""
funcao: grava_planilha_saida(individuo, nome_planilha):

Objetivo: Grava em arquivo uma planilha com a alocacao de todos os projetos
          nos contratos representada pelo individuo passado como parametro,
          e as consolidacoes necessarias para avaliar o atendimento as 
          regras de negocio

Parametros:
           individuo: representacao de uma alocacao para todos os projetos
                      nos contratos.
           planilha: nome da planilha a ser criada.

Retorna:

"""
def grava_planilha_saida(individuo, nome_planilha, df_id_contratos,
                         df_contratos, df_projetos):
    # carrega o individuo e consolida os valores relevantes
    df = carrega_consolida_individuo(individuo, df_id_contratos,
                                     df_contratos, df_projetos)

    # inclui a conformidade ao atendimento das regras de negocio,
    # e as consolidacoes necessarias para verificar cada uma
    df, valido, regra_ativa = negocio.funcao_restricao(df)

    # renomeia as colunas e retira o indice, para gravar na planilha
    df = df.rename(columns={"EXTERNO": "Total Externo",
                            "EMPRESA": "Total Empresa",
                            "INTERNO": "Total Interno"})
    df = df.drop(columns="ID_Contrato")

    # grava consolidacao em uma tabela excel.
    with pd.ExcelWriter(nome_planilha) as writer:
        df.to_excel(writer, sheet_name=NOME_ABA_CONTRATOS_PLANILHA_SAIDA,
                    index=False)
        df_projetos.to_excel(writer,
                             sheet_name=NOME_ABA_PROJETOS_PLANILHA_SAIDA,
                             index=False)

    # grava em arquivo o individuo
    arq = open(NOME_ARQUIVO_MELHOR_INDIVIDUO, 'wb')
    pickle.dump(individuo, arq)
    arq.close()
    return


"""
funcao: grava_individuo(nome_arquivo, individuo):

Objetivo: Grava em disco os individuos validos, no formato do objeto
          "Hall of Fame" do DEAP.
          Inclui no objeto "Hall of Fame" gravado em arquivo o 
          individuo passado como parametro.  
          Cria o arquivo caso não exista.

Parametros:
           nome_arquivo: Nome do arquivo a ser gravado em disco.
           individuo: individuo a ser gravado

Retorna:

"""
def grava_individuo(nome_arquivo, individuo):
    # le arquivo caso já exista, e inclui o individuo no final da populacao
    # de individuos validos gravados em disco.
    if os.path.isfile(nome_arquivo):
        arq = open(nome_arquivo, 'rb')
        hof_populacao = pickle.load(arq)
        arq.close()
        hof_populacao.insert(individuo)
        hof_populacao.update(hof_populacao)  ### ATENCAO ### Nao esta limitando o tamanho
        #                                    maximo do hall of fame
    else:
        hof_populacao = \
            tools.HallOfFame(TAMANHO_HISTORICO_MELHORES_INDIVIDUOS)
        hof_populacao.insert(individuo)

    # grava novamente a populacao dos individuos validos em disco
    arq = open(nome_arquivo, 'wb')
    pickle.dump(hof_populacao, arq)
    arq.close()
    return


def le_individuo_arquivo(nome_arquivo):
    # verifica se arquivo existe
    individuo = 0
    if os.path.isfile(nome_arquivo):
        arq = open(nome_arquivo, 'rb')
        hof = pickle.load(arq)
        # ### ATENCAO ### so esta lendo o primeiro individuo.
        # precisa alterar para retornar uma lista com todos os individuos
        individuo = hof[0]
        arq.close()
    return individuo


"""
funcao: grava_populacao(nome_arquivo, hof_populacao):

Objetivo: Grava em arquivo a populacao passada como parametro
          como um objeto "Hall of Fame" do DEAP.
          

Parametros:
           nome_arquivo: Nome do arquivo a ser gravado.
           hof_populacao: objeto "Hall of Fame" do DEAP contendo
                          a populacao a ser gravada em arquivo.
           
Retorna:

"""
def grava_historico(nome_arquivo, logbook):
    # grava o logbook do DEAP com o historico da evolucao em arquivo
    arq = open(nome_arquivo, 'wb')
    pickle.dump(logbook, arq)
    arq.close()
    return


"""
funcao: le_populacao(nome_arquivo):

Objetivo: Le de um arquivo um objeto "Hall of Fame" do DEAP, contendo
          uma populacao.


Parametros:
           nome_arquivo: Nome do arquivo a ser lido.

Retorna:

"""
def le_historico(nome_arquivo):
    # verifica se o arquivo existe
    if os.path.isfile(nome_arquivo):
        arq = open(nome_arquivo, 'rb')
        logbook = pickle.load(arq)
        arq.close()
    else:
        return  # arquivo nao encontrado

    return logbook


"""
funcao: grava_populacao(nome_arquivo, hof_populacao):

Objetivo: Grava em arquivo a populacao passada como parametro
          como um objeto "Hall of Fame" do DEAP.


Parametros:
           nome_arquivo: Nome do arquivo a ser gravado.
           hof_populacao: objeto "Hall of Fame" do DEAP contendo
                          a populacao a ser gravada em arquivo.

Retorna:

"""
def grava_populacao(nome_arquivo, hof_populacao):
    hof_populacao.update(hof_populacao)  ### ATENCAO ###
    # verificar se esta funcionando, e limitando o numero de individuaos.

    # grava o Hall of Fame com a populacao em arquivo
    arq = open(nome_arquivo, 'wb')
    pickle.dump(hof_populacao, arq)
    arq.close()
    return


"""
funcao: le_populacao(nome_arquivo):

Objetivo: Le de um arquivo um objeto "Hall of Fame" do DEAP, contendo
          uma populacao.
          

Parametros:
           nome_arquivo: Nome do arquivo a ser lido.
          
Retorna:

"""
def le_populacao(nome_arquivo):
    # verifica se o arquivo existe
    if os.path.isfile(nome_arquivo):
        arq = open(nome_arquivo, 'rb')
        hof_populacao = pickle.load(arq)
        arq.close()
    else:
        return  # arquivo nao encontrado

    return hof_populacao


def main():
    # definir rotinas de testes para as funcoes do modulo


    # ### TESTE ### leitura e gravacao de individuos m disco
    #
    # individuo = le_individuo_arquivo(NOME_ARQUIVO_MELHOR_INDIVIDUO)
    #
    # util.grava_planilha_saida(individuo,
    #                           "Teste le arquivo grava planilha.xlsx",
    #                           df_id_contratos, df_contratos,
    #                           df_detalhes_projetos)
    # ### TESTE ###


    return


if __name__ == "__main__":
    main()
