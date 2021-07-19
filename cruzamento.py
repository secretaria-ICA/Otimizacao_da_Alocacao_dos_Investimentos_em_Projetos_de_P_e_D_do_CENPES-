"""
Conjunto de funcoes para realizar o processo de cruzamento na implementacao
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

# Definicao de constantes e parametros:
PROB_CRUZAMENTO_DEAP = (0.2, 0.9)

"""
funcao: tipo(toolbox)

  Objetivo: seleciona randomicamente uma das opcoes disponiveis de
            cruzamento:
            - do DEAP: tools.cxTwoPoint,tools.cxUniform,tools.cxPartialyMatched,
                       tools.cxUniformPartialyMatched, cruzamento_metodo_1
            - cruzamento_metodo_1 : algoritmo customizado definido neste
                                    modulo.           
                     
                     Obs.: Naoforam implementados as opcoes:
                           tools.cxOrdered, tools.cxBlend, tools.cxESBlend,
                           tools.cxESTwoPoint, tools.cxSimulatedBinary, 
                           tools.cxSimulatedBinaryBounded, 
                           tools.cxMessyOnePoint
                     
  Parametros:
             toolbox: objeto toolbox do DEAP


 Retorna:
         toolbox: objeto toolbox do DEAP
"""
def tipo(toolbox, numero_contratos, indice_contratos, contratos, projetos):
    # seleciona randomicamente uma das opcoes abaixo:
    opcoes = 12  # ### ATENCAO ### maior probabilidade de usar a opcao 7
    i = random.randint(1, opcoes)
    if i == 1:
        toolbox.register("mate", tools.cxOnePoint)
    elif i == 2:
        toolbox.register("mate", tools.cxTwoPoint)
    elif i == 3:
        toolbox.register("mate", tools.cxPartialyMatched)
    elif i == 4:
        toolbox.register("mate", tools.cxOrdered)
    elif i == 5:
        toolbox.register("mate", tools.cxUniform,
                         indpb=random.uniform(PROB_CRUZAMENTO_DEAP[0],
                                              PROB_CRUZAMENTO_DEAP[1]))
    elif i == 6:
        toolbox.register("mate", tools.cxUniformPartialyMatched,
                         indpb=random.uniform(PROB_CRUZAMENTO_DEAP[0],
                                              PROB_CRUZAMENTO_DEAP[1]))
    elif i >= 7:
        toolbox.register("mate", cruzamento_metodo_1,
                         numero_contratos=numero_contratos,
                         indice_contratos=indice_contratos,
                         contratos=contratos,
                         projetos=projetos,
                         toolbox=toolbox)

    return toolbox


def cruzamento_metodo_1(child_1, child_2, numero_contratos,
                        indice_contratos, contratos, projetos, toolbox):
    # verificar se os 2 individuos estao com a performance calculada
    if child_1.fitness.valid and child_2.fitness.valid:
        # recuperar a performance dos 2 individuos
        desvios_ind_1 = f_obj.tabela_desvios(child_1)
        desvios_ind_2 = f_obj.tabela_desvios(child_2)

        # calcula o desvio total decada contrato como a soma das colunas dos desvios
        # das 3 regras/restricao de negocio
        perf_contrato_ind_1 = desvios_ind_1.sum(axis=1)
        perf_contrato_ind_2 = desvios_ind_2.sum(axis=1)

        # monta um dataframe com um indice e as performances por contrato:
        # colunas: indice do contrato, perf_contrato_ind_1, perf_contrato_ind_2
        df = pd.DataFrame(columns=["ID_contrato", "melhor_performance",
                                   "ind_1_melhor", "individuo_1", "individuo_2"])
        df["ID_contrato"] = range(len(perf_contrato_ind_1))
        df["individuo_1"] = perf_contrato_ind_1
        df["individuo_2"] = perf_contrato_ind_2

        # # identifica que individuo teve melhor performance por contrato
        df.loc[df["individuo_1"] < df["individuo_2"],
               "melhor_performance"] = df["individuo_1"]
        df.loc[df["individuo_1"] < df["individuo_2"],
               "ind_1_melhor"] = True
        df.loc[df["individuo_1"] >= df["individuo_2"],
               "melhor_performance"] = df["individuo_2"]
        df.loc[df["individuo_1"] >= df["individuo_2"],
               "ind_1_melhor"] = False

        # ordena por performance
        df = df.sort_values("melhor_performance",
                            ascending=False, ignore_index=True)

        ind_1 = toolbox.clone(child_1)
        ind_2 = toolbox.clone(child_2)
        # child_1 = carrega para cada contrato a alocacao do melhor individuo
        # para o contrato. Carrega na ordem:
        # do contrato de pior perfomance para o de melhor performance,
        # de modo que os ultimos contratos alocados sofrem menos alteraçoes
        # dos contratos alocados anteriormente
        for i in range(len(df)):
            contrato = df["ID_contrato"][i]
            # pega a alocacao do melhor individuo
            if df["ind_1_melhor"][i]:
                # identifica os indices dos projetos que foram alocados
                # neste contrato
                inds = [index for index, element in enumerate(ind_1[:])
                        if element == contrato]
                # # aloca no child_1 o contrato nos projetos
                for j in inds:
                    child_1[j] = contrato
            else:
                # identifica os indices dos projetos que foram alocados
                # neste contrato
                inds = [index for index, element in enumerate(ind_2[:])
                        if element == contrato]
                # aloca no child_1 o contrato nos projetos
                for j in inds:
                    child_1[j] = contrato

        # child_2 = carrega para cada contrato a alocacao do melhor individuo para
        # o contrato. Carrega as alocacoes dos contratos de forma randomica.
        # os ultimos contratos alocados sofrem menos alteraçoes dos contratos alocados posteriromente
        random_list = list(range(len(df)))
        random.shuffle(random_list)
        for i in random_list:
            contrato = df["ID_contrato"][i]
            # pega a alocacao do melhor individuo
            if df["ind_1_melhor"][i]:
                # identifica os indices dos projetos que foram alocados
                # neste contrato
                inds = [index for index, element in enumerate(ind_1[:])
                        if element == contrato]
                # aloca no child_1 o contrato nos projetos
                for j in inds:
                    child_2[j] = contrato
            else:
                # identifica os indices dos projetos que foram alocados
                # neste contrato
                inds = [index for index, element in enumerate(ind_2[:])
                        if element == contrato]
                # aloca no child_1 o contrato nos projetos
                for j in inds:
                    child_2[j] = contrato

    return


def main():
    # definir rotinas de testes para as funcoes do modulo
    return


if __name__ == "__main__":
    main()
