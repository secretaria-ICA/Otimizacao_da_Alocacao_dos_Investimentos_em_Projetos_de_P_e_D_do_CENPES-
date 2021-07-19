"""
Funcao objetivo 2 utilizada para calcular a performance e a validade
de um individuo quanto as regras de negocio.

Utilizadas no programa para otimizar a distribuição dos desembolsos dos
projetos de P&D do CENPES para o cumprimento da obrigação legal de
forma eficiente, buscando minimizar o valor excedente desembolsado.

 Autor: MFB
 Atualizacao: 29/06/2021

"""
import numpy as np
import pandas as pd
import utilidades as util
import funcao_restricao as negocio

NOME_ARQUIVO_INDIVIDUOS_VALIDOS = "Individuos_Validos.rca"
FATOR_MUITO_PEQUENO = 1e-12


"""
funcao: funcao_objetivo(individuo, indice_contratos, contratos, projetos):

  Objetivo: Calcular a performance de uma alocacao dos projetos nos contratos,
            representada por um individuo.
            A performance por contrato e calculada como a soma quadratica dos
            valores de todos os desvios na alocacao.
            A performance final e um tuple com o valor do quadrado de todos
            os desvios de todos os contratos.
            
            Desvios sao:
                         - "Valor que falta alocar no contrato",
                            (soma dos valores negativos)";
                         - "Valor excedente alocado no contrato",
                            (soma dos valores positivos)"

  Parametros:
              **kargs (individuo): representacao de uma alocacao para
                                   todos os projetos nos contratos.
                     
  Retorna:
          O valor da performance
          
"""
def funcao_objetivo(individuo, indice_contratos, contratos, projetos):
    df = util.carrega_consolida_individuo(individuo,
                                          indice_contratos,
                                          contratos, projetos)

    # verifica a regra de negocio de todos os contratos estarem alocados
    # se todos os contratos tem ao menos 1 projeto alocado
    # neste caso,
    if len(df) < len(indice_contratos):
        negocio.todos_contratos_alocados(individuo, indice_contratos)
        df = util.carrega_consolida_individuo(individuo,
                                              indice_contratos,
                                              contratos, projetos)

    # verifica se o individuo atende a todas as regras de negócio,

    # inclui no dataframe a avaliacao das regras de negocio para
    # todos os contratos
    df, valido, regra_ativa = negocio.funcao_restricao(df)

    # grava individuo valido em arquivo
    if valido:
        util.grava_individuo(NOME_ARQUIVO_INDIVIDUOS_VALIDOS,
                             individuo)

    # retira a linha do "Total Geral" das regras de negocio ativas
    r1_ativa, r2_ativa, r3_ativa = regra_ativa
    r1_ativa.drop(index=len(r1_ativa) - 1)
    r2_ativa.drop(index=len(r2_ativa) - 1)
    r3_ativa.drop(index=len(r3_ativa) - 1)

    # cria um dataframe somente com os desvios de alocacao
    p = df[["Critério (TOTAL - Obrigação)",
            "Criterio Mínimo Externo",
            "Critério Máximo Interno"]]

    # retira a linha do "Total Geral"
    p = p.drop(index=len(p) - 1)

    # desconsiderar os desvios para as regras de negocio NAO ativas
    p.loc[r1_ativa == False, "Critério (TOTAL - Obrigação)"] = 0
    p.loc[r2_ativa == False, "Criterio Mínimo Externo"] = 0
    p.loc[r3_ativa == False, "Critério Máximo Interno"] = 0

    tab_desvios = p.values

    # calcular a tabela de performance como um tuple com o quadrado
    # de todos os desvios de todos os contratos.
    tab_performance = tab_desvios * tab_desvios
    r = salva_performance(tab_performance, tab_desvios)

    return r  # retorna obrigatoriamente um tuple


def cria_performance(num_contratos):
    # otimizacao multivariavel da tabela de desvios, calculada na
    # funcao objetivo.
    # Nesta tabela sao 3 colunas com valores de desvios por contrato,
    # com uma linha final "Total Geral".

    # retira a linha de total geral, e divide em 3 colunas
    tam_objetivo = 3 * (num_contratos - 1)

    # cria um tuple com o pesos -1.0 para cada um dos desvios no objetivo
    fit_weights = [-1.]
    for i in range(tam_objetivo - 1):
        fit_weights.append(-1.)

    # incluir a tabela de performance nas variaveis
    # da optimizacao multivariavel com peso muitas ordens de grandeza
    # menores, de modo a nao afetar o calculo da performance
    for i in range(tam_objetivo):
        fit_weights.append(FATOR_MUITO_PEQUENO)

    fit_weights = tuple(fit_weights)

    return fit_weights


def salva_performance(tab_performance, tab_desvios):
    lin, col = tab_performance.shape
    tab_performance = tab_performance.reshape(1, lin * col)
    tab_performance = tab_performance[0]

    lin, col = tab_desvios.shape
    tab_desvios = tab_desvios.reshape(1, lin * col)
    tab_desvios = tab_desvios[0]

    # monta um tuple com a tabela de performance seguida da tabela de
    # desvios, multiplicada por umVALOR_MUITO_PEQUENO, de modo a
    # ter muitas ordens de grandeza menores que a tabela de performance
    tab_desvios = tab_desvios * FATOR_MUITO_PEQUENO
    performance = tuple(np.concatenate((tab_performance, tab_desvios)))

    return performance


def performance(individuo):
    r = sum(individuo.fitness.values[0:int(len(individuo.fitness.values)/2)])
    ## identificar se a performance e invalida
    # if math.isnan(r):
    #     a=1
    return r


def tabela_performance(individuo):
    # recuperar a tabela de performance do individuo
    perf = individuo.fitness
    perf = np.array(perf.values)
    perf = perf.reshape(int(len(perf) / 3), 3)
    perf = pd.DataFrame(perf)
    tab_perf = perf[:][0:int(len(perf)/2)]
    # tab_desvios = perf_ind[:][int(len(perf_ind) / 2):len(perf_ind)]
    tab_perf = tab_perf.reset_index(drop=True)

    return tab_perf


def tabela_desvios(individuo):
    # recuperar a tabela de desvios do individuo
    desvios = individuo.fitness
    desvios = np.array(desvios.values)
    desvios = desvios.reshape(int(len(desvios) / 3), 3)
    desvios = pd.DataFrame(desvios)
    # tab_perf = perf[:][0:int(len(perf) / 2)]
    tab_desvios = desvios[:][int(len(desvios) / 2):len(desvios)]
    tab_desvios = tab_desvios.reset_index(drop=True)

    # a tabela de desvios foi multiplicada pelo FATOR_MUITO_PEQUENO
    # para ter valores muitas ordens de grandeza menores que os
    # objetivos(desvios)
    tab_desvios = tab_desvios / FATOR_MUITO_PEQUENO

    return tab_desvios


def main():
    # definir rotinas de testes para as funcoes do modulo
    return


if __name__ == "__main__":
    main()
