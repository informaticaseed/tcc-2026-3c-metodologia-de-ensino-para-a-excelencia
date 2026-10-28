"""
visualization.py
================
Geração e exportação dos gráficos diagnósticos:
- Gráfico de dispersão PCA 2D com perfis
- Gráfico comparativo de dimensões por cluster
- Gráfico comparativo por turma e série
- Nuvens de palavras segmentadas por tema
"""

import os
import matplotlib.pyplot as plt
import seaborn as sns

try:
    from .config import READABLE_INDEX_NAMES
except (ImportError, ValueError):
    from config import READABLE_INDEX_NAMES

try:
    from wordcloud import WordCloud
except ImportError:
    WordCloud = None


def plot_comparative_charts(df, X_pca, pca, index_columns, cluster_means, profile_names, output_dir):
    """Gera e salva os 3 gráficos comparativos principais (PCA, dimensões e turmas)."""
    n_samples = len(df)
    n_components = X_pca.shape[1]

    # 1. Gráfico de Dispersão PCA 2D
    plt.figure(figsize=(9, 6))
    if n_components >= 2:
        sns.scatterplot(
            x=X_pca[:, 0],
            y=X_pca[:, 1],
            hue=df['pedagogical_profile'],
            palette='Set1',
            s=120,
            style=df['pedagogical_profile'],
            alpha=0.85
        )
        if n_samples <= 15:
            for i, name in enumerate(df['full_name']):
                plt.annotate(
                    name,
                    (X_pca[i, 0], X_pca[i, 1]),
                    xytext=(6, 4),
                    textcoords='offset points',
                    fontsize=9,
                    fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="gray", alpha=0.7)
                )
        v1 = pca.explained_variance_ratio_[0] * 100
        v2 = pca.explained_variance_ratio_[1] * 100
        plt.xlabel(f"Componente Principal 1 ({v1:.1f}% da variância explicada)", fontsize=11)
        plt.ylabel(f"Componente Principal 2 ({v2:.1f}% da variância explicada)", fontsize=11)
    else:
        sns.scatterplot(x=X_pca[:, 0], y=[0] * n_samples, hue=df['pedagogical_profile'], s=120)
        plt.xlabel("Componente Principal 1")

    plt.title("Mapeamento de Perfis Estudantis (PCA 2D)", fontsize=13, fontweight='bold', pad=12)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', frameon=True)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()

    pca_path = os.path.join(output_dir, "grafico_clusters_pca.png")
    plt.savefig(pca_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Gráfico de PCA salvo em: {pca_path}")

    # 2. Gráfico de Barras das 5 Dimensões por Cluster
    plot_means = cluster_means.rename(columns=READABLE_INDEX_NAMES)
    plot_means.index = [profile_names.get(c, f"Grupo {c+1}") for c in plot_means.index]

    plt.figure(figsize=(11, 5.5))
    plot_means.T.plot(kind='bar', figsize=(11, 5.5), colormap='viridis', edgecolor='black', width=0.75)
    plt.title("Comparativo das 5 Dimensões Pedagógicas por Perfil de Cluster (0 a 10)", fontsize=13, fontweight='bold', pad=12)
    plt.ylabel("Pontuação Média do Índice (0 a 10)", fontsize=11)
    plt.ylim(0, 10.5)
    plt.xticks(rotation=15, ha='right', fontsize=10)
    plt.grid(axis='y', linestyle='--', alpha=0.6)
    plt.legend(title="Perfis Identificados", bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.tight_layout()

    dim_path = os.path.join(output_dir, "grafico_dimensoes_clusters.png")
    plt.savefig(dim_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Gráfico comparativo de dimensões salvo em: {dim_path}")

    # 3. Comparativo Agrupado por Turma e Série
    if 'grade' in df.columns and 'school_class' in df.columns:
        df_cohort = df.copy()
        df_cohort['class_cohort'] = df_cohort['grade'].astype(str) + " - Turma " + df_cohort['school_class'].astype(str)
        class_stats = df_cohort.groupby('class_cohort')[index_columns].mean().rename(columns=READABLE_INDEX_NAMES)

        plt.figure(figsize=(10, 5))
        class_stats.T.plot(kind='bar', figsize=(10, 5), colormap='coolwarm', edgecolor='black', width=0.6)
        plt.title("Médias das Dimensões Diagnósticas por Turma e Série", fontsize=12, fontweight='bold')
        plt.ylabel("Média (0 a 10)")
        plt.ylim(0, 10.5)
        plt.xticks(rotation=15, ha='right')
        plt.grid(axis='y', linestyle='--', alpha=0.6)
        plt.legend(title="Série / Turma", bbox_to_anchor=(1.02, 1), loc='upper left')
        plt.tight_layout()

        turma_path = os.path.join(output_dir, "analise_por_turma.png")
        plt.savefig(turma_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Gráfico por turma salvo em: {turma_path}")


def generate_thematic_wordclouds(df, output_dir):
    """Gera o painel com 3 nuvens de palavras temáticas (Dificuldades, Sonhos e Apoio)."""
    if WordCloud is None:
        print("Aviso: 'wordcloud' não instalada. Pule a geração de nuvens de palavras com 'pip install wordcloud'.")
        return

    portuguese_stopwords = {
        "de", "a", "o", "que", "e", "do", "da", "em", "um", "para", "é", "com", 
        "não", "uma", "os", "no", "se", "na", "por", "mais", "as", "dos", "como", 
        "mas", "foi", "ao", "ele", "das", "tem", "à", "seu", "sua", "ou", "ser", 
        "quando", "muito", "nos", "já", "eu", "também", "só", "pelo", "pela", "até", 
        "isso", "ela", "entre", "era", "depois", "sem", "mesmo", "aos", "ter", "seus",
        "alguns", "alguma", "muito", "muitas", "muitos", "onde"
    }

    themes = [
        ("Dificuldades de Aprendizagem", "learning_difficulties", "Reds"),
        ("Expectativas e Sonhos de Futuro", "personal_professional_goals", "Purples"),
        ("Apoio Esperado da Escola", "school_support", "Blues")
    ]

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    for idx, (title, column, palette) in enumerate(themes):
        ax = axes[idx]
        if column in df.columns:
            texts = df[column].dropna().astype(str).tolist()
            unified_text = " ".join(texts)
        else:
            unified_text = ""

        if unified_text.strip():
            wc = WordCloud(
                width=600,
                height=400,
                background_color="white",
                colormap=palette,
                stopwords=portuguese_stopwords,
                min_word_length=3
            ).generate(unified_text)
            ax.imshow(wc, interpolation="bilinear")
            ax.set_title(title, fontsize=12, fontweight="bold", pad=10)
        else:
            ax.text(0.5, 0.5, "Sem dados textuais suficientes", ha="center", va="center")
            ax.set_title(title, fontsize=12, fontweight="bold")

        ax.axis("off")

    plt.suptitle("Nuvens de Palavras Segmentadas por Eixo do Diagnóstico", fontsize=15, fontweight="bold", y=1.02)
    plt.tight_layout()

    img_path = os.path.join(output_dir, "nuvens_palavras_segmentadas.png")
    plt.savefig(img_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Nuvens de palavras salvas em: {img_path}")

