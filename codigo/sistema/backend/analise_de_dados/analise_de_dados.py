"""
analise_de_dados.py
===================
Ponto de entrada principal para a execução do pipeline de diagnóstico estudantil.
Mantido para compatibilidade total com os comandos existentes.

Para ver a implementação modular, consulte:
- config.py         : Parâmetros, caminhos e mapeamentos
- data_loader.py    : Ingestão de dados (CSV, SQL, DB) e persistência
- indices.py        : Cálculo dos 5 índices multidimensionais (0 a 10)
- clustering.py     : PCA 2D e K-Means Clustering
- visualization.py  : Gráficos comparativos e nuvens de palavras
- pipeline.py       : Orquestração linear do fluxo analítico
"""

import sys
import os

# Adiciona o diretório atual ao path para importação direta de módulos
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from pipeline import run_pipeline
from indices import calculate_pedagogical_indices
from clustering import apply_pca_and_kmeans
from data_loader import load_dataset, export_analytics_to_sql, save_analytics_to_database


def main():
    """Executa o pipeline completo de análise diagnóstica."""
    return run_pipeline()


if __name__ == "__main__":
    main()
