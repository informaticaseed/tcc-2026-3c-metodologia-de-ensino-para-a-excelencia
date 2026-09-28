"""
clustering.py
=============
Processamento estatístico não-supervisionado:
- Padronização de matriz (StandardScaler)
- Projeção 2D (PCA)
- Agrupamento (K-Means)
- Profiling pedagógico descritivo
"""

import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

try:
    from .config import INDEX_COLUMNS
except (ImportError, ValueError):
    from config import INDEX_COLUMNS


def apply_pca_and_kmeans(df, n_clusters=3, random_state=42):
    """
    Padroniza os índices, calcula projeção PCA 2D e classifica em clusters K-Means.
    """
    df = df.copy()
    X = df[INDEX_COLUMNS]

    # 1. Padronização
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 2. Redução de Dimensionalidade (PCA 2D)
    n_samples, n_features = X_scaled.shape
    n_components = min(2, n_samples, n_features)
    pca = PCA(n_components=n_components)
    X_pca = pca.fit_transform(X_scaled)

    df['pca_1'] = np.round(X_pca[:, 0], 3) if n_components >= 1 else 0.0
    df['pca_2'] = np.round(X_pca[:, 1], 3) if n_components >= 2 else 0.0

    # 3. Clusterização K-Means
    effective_clusters = min(n_clusters, n_samples)
    kmeans = KMeans(n_clusters=effective_clusters, random_state=random_state, n_init=10)
    df['cluster'] = kmeans.fit_predict(X_scaled)

    # 4. Profiling Pedagógico
    df, cluster_means, profile_names = characterize_clusters(df, INDEX_COLUMNS)

    return df, X_pca, pca, cluster_means, profile_names


def characterize_clusters(df, index_columns):
    """
    Calcula as médias das dimensões por cluster e aplica heurísticas pedagógicas
    para rotular descritivamente cada grupo identificado.
    """
    cluster_means = df.groupby('cluster')[index_columns].mean()
    profile_names = {}

    for c in cluster_means.index:
        vulnerability = 10.0 - cluster_means.loc[c, 'idx_socioeconomic_digital']
        work_burden = cluster_means.loc[c, 'idx_work_overload']
        politics = cluster_means.loc[c, 'idx_political_engagement']
        school_climate = cluster_means.loc[c, 'idx_school_bonding']
        culture = cluster_means.loc[c, 'idx_cultural_capital']

        if work_burden >= 4.0 or vulnerability >= 6.0:
            profile_names[c] = "Perfil Trabalhador / Vulnerabilidade Econômica"
        elif politics >= 6.0 and culture >= 6.0:
            profile_names[c] = "Perfil Engajado / Participativo e Cultural"
        elif school_climate >= 7.0 and cluster_means.loc[c, 'idx_socioeconomic_digital'] >= 6.0:
            profile_names[c] = "Perfil Conectado / Foco Tecnológico e Acadêmico"
        else:
            profile_names[c] = f"Perfil em Desenvolvimento (Grupo {c+1})"

    df['pedagogical_profile'] = df['cluster'].map(profile_names)
    return df, cluster_means, profile_names

