"""
Conjunto de funcoes para realizar o processo de selecao na implementacao
do algoritmo genetico.

Utilizadas no programa para otimizar O RCA (distribuição dos desembolsos dos
projetos de P&D do CENPES para o cumprimento da obrigação legal) de
forma eficiente, buscando minimizar o valor excedente desembolsado.

 Autor: MFB
 Atualizacao: 01/07/2021

"""
import random
from deap import tools

# Definicao de constantes e parametros
TOURNSIZE_POP_PERCENT = 0.15

"""
funcao: tipo(toolbox, numero_contratos, indice_contratos, contratos, projetos)

  Objetivo: seleciona randomicamente uma das opcoes disponiveis de metodo
            utilizado para o processo de selecao dos individuos para a 
            proxima geracao.
            - do DEAP: tools.selBest, tools.selRoulette, 
                       tools.selStochasticUniversalSampling, 
                       tools.selRoulette
            - selecao_metodo_1 : algoritmo customizado definido neste modulo.           

  Parametros:
             toolbox: objeto toolbox do DEAP

  Retorna:
          toolbox: objeto toolbox do DEAP
"""


def tipo(toolbox, numero_contratos, indice_contratos, contratos, projetos):
    # selecionarandomicamente uma das opcoes abaixo:
    opcoes = 1  ### ATENCAO ### , Nao chama as opcoes 2, 3, 4, 5, 6, 7
    i = random.randint(1, opcoes)
    i = 1  # ### ATENCAO ###
    if i == 1:
        toolbox.register("select", selectthebest,
                         numero_contratos=numero_contratos,
                         indice_contratos=indice_contratos,
                         contratos=contratos,
                         projetos=projetos)
    elif i == 2:
        toolbox.register("select", selecttournament,
                         numero_contratos=numero_contratos,
                         indice_contratos=indice_contratos,
                         contratos=contratos,
                         projetos=projetos)
    elif i == 3:
        toolbox.register("select", tools.selBest)
    elif i == 4:
        # toolbox.register("select", tools.selTournament,
        #                  tournsize=TOURNSIZE)
        a=1
    elif i == 5:
        toolbox.register("select", tools.selStochasticUniversalSampling)
    elif i == 6:  # ### ATENCAO ### verificar se funciona perto do zero...
        # warning na documentacao do DEAP
        toolbox.register("select", tools.selRoulette)
    elif i == 7:
        toolbox.register("select", selecao_metodo_1,
                         numero_contratos=numero_contratos,
                         indice_contratos=indice_contratos,
                         contratos=contratos,
                         projetos=projetos)

    return toolbox


def selectthebest(individuos, k, numero_contratos, indice_contratos,
                  contratos, projetos):

    tam_performance = int(len(individuos[0].fitness.values)/2)
    dict_tmp = {sum(ind.fitness.values[0:tam_performance]): ind for ind in individuos}
    ranking = sorted(dict_tmp.items())
    selecao = ranking[0:k]
    selecao = [ind[1] for ind in selecao]

    return selecao


def selecttournament(individuos, k, numero_contratos, indice_contratos,
                  contratos, projetos):

    tam_performance = int(len(individuos[0].fitness.values)/2)
    dict_tmp = {sum(i.fitness.values[0:tam_performance]): i for i in individuos}
    ranking = sorted(dict_tmp.items())

    selecao_indices = []
    i = 0
    tournsize = int(len(individuos) * TOURNSIZE_POP_PERCENT)
    indices = range(len(individuos))
    while i < k:
        opcao = min(random.choices(indices, k=tournsize))
        selecao_indices.append(opcao)
        i+=1

    # ordena individuos selecionados por ordem de performance
    selecao_indices.sort()
    selecao = [ranking[ind][1] for ind in selecao_indices]

    return selecao




def selecao_metodo_1(individuos, k, numero_contratos, indice_contratos,
                     contratos, projetos):
    a = 1
    return individuos,


def main():
    # definir rotinas de testes para as funcoes do modulo
    return


if __name__ == "__main__":
    main()