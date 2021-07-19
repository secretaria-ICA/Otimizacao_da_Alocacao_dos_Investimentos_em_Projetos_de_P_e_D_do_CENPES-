"""
Conjunto de funcoes para realizar o processo de mutacao na implementacao
do algoritmo genetico.

Utilizadas no programa para otimizar O RCA (distribuição dos desembolsos dos
projetos de P&D do CENPES para o cumprimento da obrigação legal) de
forma eficiente, buscando minimizar o valor excedente desembolsado.

 Autor: MFB
 Atualizacao: 07/07/2021

"""

import random
import pandas as pd
from deap import tools
import funcao_objetivo as f_obj
import funcao_restricao as negocio


# Definicao de constantes e parametros
PROB_MUTACAO_DEAP = (0.1, 0.9)


# taxa que define a parcela de contratos que sera alocada ou desalocada
# na mutacao. (0.01, 0.20) significa de 1% a 20% do numero de
# projetos alocados atualmente ao contrato serão alocados ou desalocados.
# TAXA_IMPACTO_MUTACAO = (MIN, MAX)
TAXA_IMPACTO_MUTACAO = (0.01, 0.30)

"""
funcao: tipo(toolbox)

  Objetivo: seleciona randomicamente uma das opcoces disponiveis de mutacao
            - do DEAP: tools.mutShuffleIndexes,tools.mutFlipBit,
                       tools.mutUniformInt, mutacao_metodo_1
            - mutacao_metodo_1 : algoritmo customizado definido neste 
                                 modulo.           
                    
  Parametros:
             toolbox: objeto toolbox do DEAP


  Retorna:
          toolbox: objeto toolbox do DEAP
"""


def tipo(toolbox, numero_contratos, indice_contratos, contratos, projetos):
    # seleciona randomicamente uma das opcoes abaixo:
    opcoes = 7  # ### ATENCAO ### probabilidades diferentes nas opcoes
    i = random.randint(1, opcoes)
    if i == 1:
        toolbox.register("mutate", tools.mutShuffleIndexes,
                         indpb=random.uniform(PROB_MUTACAO_DEAP[0],
                                              PROB_MUTACAO_DEAP[1]))
    elif i == 2:
        toolbox.register("mutate", tools.mutFlipBit,
                         indpb=random.uniform(PROB_MUTACAO_DEAP[0],
                                              PROB_MUTACAO_DEAP[1]))
    elif i == 3:
        toolbox.register("mutate", tools.mutUniformInt,
                         low=0,
                         up=numero_contratos,
                         indpb=random.uniform(PROB_MUTACAO_DEAP[0],
                                              PROB_MUTACAO_DEAP[1]))
    elif 4 <= i < 6:
        toolbox.register("mutate", mutacao_metodo_1,
                         numero_contratos=numero_contratos,
                         indice_contratos=indice_contratos,
                         contratos=contratos,
                         projetos=projetos,
                         toolbox=toolbox)
    elif i >= 6:
        toolbox.register("mutate", mutacao_metodo_2,
                         numero_contratos=numero_contratos,
                         indice_contratos=indice_contratos,
                         contratos=contratos,
                         projetos=projetos,
                         toolbox=toolbox)

    return toolbox


def mutacao_metodo_1(individuo, numero_contratos, indice_contratos,
                     contratos, projetos, toolbox):
    # so executa se o individuo ja tiver sua performance calculada:
    if individuo.fitness.valid:

        # seleciona randomicamente qual das 3 regras de negocio sera
        # utilizada como criterio na mutacao
        regras_de_negocio = ("Critério (TOTAL - Obrigação)",
                             "Criterio Mínimo Externo",
                             "Criterio Máximo Interno")

        # recupera a tabela de performance do individuo
        tab_desvios_ind = f_obj.tabela_desvios(individuo)

        df = pd.DataFrame(columns=["ID_contrato",
                                   "Critério (TOTAL - Obrigação)",
                                   "Criterio Mínimo Externo",
                                   "Criterio Máximo Interno"])
        df["ID_contrato"] = range(len(tab_desvios_ind))
        df["Critério (TOTAL - Obrigação)"] = tab_desvios_ind[0]
        df["Criterio Mínimo Externo"] = tab_desvios_ind[1]
        df["Criterio Máximo Interno"] = tab_desvios_ind[2]

        # novo_individuo:
        # altera algumas alocacoes de projetos em contratos considerando
        # apenas a regra de negócio selecionada randomicamente
        criterio_selecionado = random.choice(regras_de_negocio)

        # para o caso de regra de negocio com limite maximo, inverte o
        # sinal do desvio, de modo que o desvio seja positivo para casos que
        # necessita desalocar projetos, e negativo caso necessite
        # alocar projetos
        if criterio_selecionado == "Criterio Máximo Interno":
            df[criterio_selecionado] = - df[criterio_selecionado]

        # ordena os desvios pelo seu valor
        df = df.sort_values(criterio_selecionado,
                            ascending=False, ignore_index=True)

        # um projeto desalocado e representato pela alocacao em um contrato
        # "vazio", incluido como ultima linha na tabela de indices de contrato
        id_contrato_projeto_nao_alocado = len(df)

        # desalocar projetos dos contratos que estao com valor excedente
        i = 0
        # define a taxa da probabilidade de mutacao, randomicamente entre
        # os valores (MIN, MAX) definidos na constante TAXA_IMPACTO_MUTACAO
        taxa = random.uniform(TAXA_IMPACTO_MUTACAO[0],
                              TAXA_IMPACTO_MUTACAO[1])
        while i < len(df) and df[criterio_selecionado][i] > 0:
            # identifica os indices dos projetos que foram alocados
            # neste contrato
            contrato = df["ID_contrato"][i]
            inds = [index for index, element in enumerate(individuo[:])
                    if element == contrato]

            # desaloca projetos deste contrato no novo_individuo.
            # no minimo 1 projeto
            num_projetos = len(inds)
            num_desalocar = max(1, int(taxa * num_projetos))
            # limita nao desalocar mais contratos do que existem alocados
            # e nao desalocar todos os contratos, e no minimo desalocar 1
            # ### ATENCAO ### pode dar erro na funcao objetivo um contrato
            #                 completamente desalocado
            if len(inds) > 0:
                if num_desalocar < len(inds)-1:
                    inds_desalocar = random.sample(inds, num_desalocar)
                else:
                    inds_desalocar = random.sample(inds, len(inds)-1)

                for j in inds_desalocar:
                    individuo[j] = id_contrato_projeto_nao_alocado
                else:
                    negocio.todos_contratos_alocados(individuo, indice_contratos)

            i = i + 1  # muda para o proximo contrato

        # alocar projetos nos contratos que estao com deficit no valor
        while i < len(df) and df[criterio_selecionado][i] < 0:
            # identifica os indices dos projetos que foram alocados
            # neste contrato
            contrato = df["ID_contrato"][i]
            inds = [index for index, element in enumerate(individuo[:])
                    if element == contrato]
            num_projetos = len(inds)
            num_alocar = max(1, int(taxa * num_projetos))

            negocio.alocar_contrato(individuo, contrato, num_alocar,
                                    indice_contratos)
            i = i + 1  # muda para o proximo contrato

    return



def mutacao_metodo_2(individuo, numero_contratos, indice_contratos,
                     contratos, projetos, toolbox):
    # so executa se o individuo ja tiver sua performance calculada:
    if individuo.fitness.valid:

        # seleciona randomicamente qual das 3 regras de negocio sera
        # utilizada como criterio na mutacao
        # regras_de_negocio = ("Critério (TOTAL - Obrigação)",
        #                      "Criterio Mínimo Externo",
        #                      "Criterio Máximo Interno")

        # recupera a tabela de desvios do individuo
        tab_desvios_ind = f_obj.tabela_desvios(individuo)

        df = pd.DataFrame(columns=["ID_contrato",
                                   "Critério (TOTAL - Obrigação)",
                                   "Criterio Mínimo Externo",
                                   "Criterio Máximo Interno"])
        df["ID_contrato"] = range(len(tab_desvios_ind))
        df["Critério (TOTAL - Obrigação)"] = tab_desvios_ind[0]
        df["Criterio Mínimo Externo"] = tab_desvios_ind[1]
        df["Criterio Máximo Interno"] = tab_desvios_ind[2]

        # novo_individuo:
        # altera algumas alocacoes de projetos em contratos considerando
        # a soma total dos desvios por contrato
        criterio_selecionado = "Desvio Contrato"
        df["Desvio Contrato"] = df["Critério (TOTAL - Obrigação)"]\
                                + df["Criterio Mínimo Externo"]\
                                - df["Criterio Máximo Interno"]

        # ordena os desvios pelo seu valor
        df = df.sort_values(criterio_selecionado,
                            ascending=False, ignore_index=True)

        # um projeto desalocado e representato pela alocacao em um contrato
        # "vazio", incluido como ultima linha na tabela de indices de contrato
        id_contrato_projeto_nao_alocado = len(df)

        # desalocar projetos dos contratos que estao com valor excedente
        i = 0
        # define a taxa da probabilidade de mutacao, randomicamente entre
        # os valores (MIN, MAX) definidos na constante TAXA_IMPACTO_MUTACAO
        taxa = random.uniform(TAXA_IMPACTO_MUTACAO[0],
                              TAXA_IMPACTO_MUTACAO[1])
        while i < len(df) and df[criterio_selecionado][i] > 0:
            # identifica os indices dos projetos que foram alocados
            # neste contrato
            contrato = df["ID_contrato"][i]
            inds = [index for index, element in enumerate(individuo[:])
                    if element == contrato]
            # corrige o individuo caso nao tenha o contrato alocado.
            # pois todos os individuos precisam alocar em todos os contratos
            if len(inds) > 0:
                # desaloca projetos deste contrato no novo_individuo
                num_projetos = len(inds)
                num_desalocar = max(1, int(taxa * num_projetos))
                # limita nao desalocar mais contratos do que existem alocados
                if num_desalocar < len(inds):
                    inds_desalocar = random.sample(inds, num_desalocar)
                else:
                    inds_desalocar = random.sample(inds, len(inds)-1)

                for j in inds_desalocar:
                    individuo[j] = id_contrato_projeto_nao_alocado
                else:
                    # recuperar o individuo que nao tem algum contrato alocado
                    negocio.todos_contratos_alocados(individuo, indice_contratos)
            i = i + 1  # muda para o proximo contrato

        # alocar projetos nos contratos que estao com deficit no valor
        while i < len(df) and df[criterio_selecionado][i] < 0:
            # identifica os indices dos projetos que foram alocados
            # neste contrato
            contrato = df["ID_contrato"][i]
            inds = [index for index, element in enumerate(individuo[:])
                    if element == contrato]
            num_projetos = len(inds)
            num_alocar = max(1, int(taxa * num_projetos))

            negocio.alocar_contrato(individuo, contrato, num_alocar,
                                    indice_contratos)
            i = i + 1  # muda para o proximo contrato

    return



def main():
    # definir rotinas de testes para as funcoes do modulo
    return


if __name__ == "__main__":
    main()
