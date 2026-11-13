"""
pipeline.py
===========
Orquestrador central do fluxo de análise de dados (Pipeline):
1. Ingestão de dados (SQL / PostgreSQL)
2. Engenharia de recursos (Índices pedagógicos de 0 a 10)
3. Aprendizado não-supervisionado (PCA 2D e K-Means)
4. Geração de relatórios gráficos e nuvens de palavras
5. Exportação (script SQL e persistência no PostgreSQL)
"""

import os
from config import (
    SQL_ANALYTICS_PATH,
    USE_POSTGRESQL_DB,
    DB_CONFIG,
    INDEX_COLUMNS,
    REPORTS_GLOBAL_DIR
)
from data_loader import (
    load_dataset,
    export_analytics_to_sql,
    save_analytics_to_database
)
from indices import calculate_pedagogical_indices
from clustering import apply_pca_and_kmeans
from visualization import (
    plot_comparative_charts,
    generate_thematic_wordclouds
)


def run_pipeline():
    """Executa o pipeline completo de diagnóstico e análise estatística."""
    # 1. Carregamento dos dados
    df_raw = load_dataset()

    # 2. Engenharia de Recursos: Cálculo dos 4 Índices
    df_indices = calculate_pedagogical_indices(df_raw)

    print("\n--- ÍNDICES MULTIDIMENSIONAIS DOS ESTUDANTES (0 a 10) ---")
    summary_cols = ['full_name', 'grade', 'school_class'] + INDEX_COLUMNS
    print(df_indices[summary_cols].to_string(index=False))

    # 3. Modelagem Estatística: PCA 2D e K-Means Clustering
    df_result, X_pca, pca, cluster_means, profile_names = apply_pca_and_kmeans(df_indices)

    # 4. Geração de Nuvens de Palavras e Gráficos Comparativos
    os.makedirs(REPORTS_GLOBAL_DIR, exist_ok=True)
    generate_thematic_wordclouds(df_result, REPORTS_GLOBAL_DIR)
    plot_comparative_charts(
        df_result, X_pca, pca, INDEX_COLUMNS, cluster_means, profile_names, REPORTS_GLOBAL_DIR
    )

    # 5. Exportação de Relatórios e Persistência
    export_analytics_to_sql(df_result, SQL_ANALYTICS_PATH)

    if USE_POSTGRESQL_DB:
        save_analytics_to_database(df_result, DB_CONFIG)

    # 6. Síntese Final dos Perfis
    print("\n" + "="*80)
    print("SÍNTESE DOS PERFIS ESTUDANTIS IDENTIFICADOS (TCC)")
    print("="*80)
    display_cols = ['full_name', 'grade', 'school_class', 'income_category', 'work_hours', 'pedagogical_profile']
    available_cols = [c for c in display_cols if c in df_result.columns]
    print(df_result[available_cols].to_string(index=False))
    print("="*80 + "\n")

    return df_result


if __name__ == "__main__":
    run_pipeline()
