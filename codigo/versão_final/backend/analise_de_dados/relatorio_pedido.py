"""
relatorio_pedido.py
===================
Geração sob demanda dos relatórios analíticos de um pedido de diagnóstico.

Diferente do pipeline global, este módulo carrega apenas as respostas do
pedido selecionado e treina PCA/K-Means dentro do próprio grupo. Os
arquivos são gravados em ``backend/relatorios_pedidos/pedido_<id>`` e só
podem ser servidos por rotas Flask autenticadas.
"""

import hashlib
import json
import math
import os
import threading
from datetime import datetime

import pandas as pd

import matplotlib
matplotlib.use("Agg")

from config import DB_CONFIG, INDEX_COLUMNS, REPORTS_ORDERS_DIR
from data_loader import load_data_from_database
from indices import calculate_pedagogical_indices
from clustering import apply_pca_and_kmeans
from visualization import (
    plot_comparative_charts,
    generate_thematic_wordclouds,
)

CSV_FILENAME = "relatorio_perfil_estudantil_completo.csv"
META_FILENAME = "_meta.json"

IMAGE_FILES = {
    "pca": "grafico_clusters_pca.png",
    "dimensoes": "grafico_dimensoes_clusters.png",
    "turma": "analise_por_turma.png",
    "nuvens": "nuvens_palavras_segmentadas.png",
}

_generation_lock = threading.Lock()


def order_report_dir(order_id):
    """Diretório protegido de relatórios do pedido informado."""
    return os.path.join(REPORTS_ORDERS_DIR, f"pedido_{int(order_id)}")


def get_report_image_path(order_id, image_name):
    """Retorna o caminho de uma imagem válida do pedido (ou None)."""
    file_name = IMAGE_FILES.get(image_name)

    if not file_name:
        return None

    path = os.path.join(order_report_dir(order_id), file_name)

    if os.path.isfile(path):
        return path

    return None


def get_report_csv_path(order_id):
    """Retorna o caminho do CSV do pedido, se ele já existir."""
    path = os.path.join(order_report_dir(order_id), CSV_FILENAME)

    if os.path.isfile(path):
        return path

    return None


def empty_summary():
    """Estrutura vazia compatível com o resumo analítico da tela."""
    return {
        "students": [],
        "total_diagnosticados": 0,
        "medias": {
            "socio": 0.0,
            "trabalho": 0.0,
            "vinculo": 0.0,
            "cultural": 0.0,
        },
        "perfis_count": {},
    }


def generate_order_reports(order_id, force=False):
    """
    Garante que os relatórios do pedido existam e devolve caminhos + resumo.

    O cache é invalidado automaticamente quando as respostas do pedido
    mudam (assinatura calculada sobre o conteúdo carregado).
    """
    order_id = int(order_id)
    df_raw = load_data_from_database(DB_CONFIG, order_id=order_id)

    if df_raw.empty:
        return {
            "available": False,
            "order_id": order_id,
            "reason": "Este pedido ainda não possui respostas.",
            "csv_path": None,
            "images": {},
            "summary": empty_summary(),
            "generated_at": None,
        }

    signature = _compute_signature(df_raw)
    order_dir = order_report_dir(order_id)
    meta_path = os.path.join(order_dir, META_FILENAME)
    csv_path = os.path.join(order_dir, CSV_FILENAME)

    cached = _is_cache_valid(order_dir, meta_path, signature, csv_path)

    if cached and not force:
        try:
            df_cached = pd.read_csv(csv_path)
            return _build_result(order_id, order_dir, df_cached, signature)
        except Exception:
            # Arquivo corrompido/incompleto: regenera abaixo.
            cached = False

    with _generation_lock:
        # Outra requisição pode ter gerado enquanto esperávamos o lock.
        if not force and _is_cache_valid(order_dir, meta_path, signature, csv_path):
            df_cached = pd.read_csv(csv_path)
            return _build_result(order_id, order_dir, df_cached, signature)

        os.makedirs(order_dir, exist_ok=True)

        df_indices = calculate_pedagogical_indices(df_raw)
        df_result, X_pca, pca, cluster_means, profile_names = (
            apply_pca_and_kmeans(df_indices)
        )

        generate_thematic_wordclouds(df_result, order_dir)
        plot_comparative_charts(
            df_result,
            X_pca,
            pca,
            INDEX_COLUMNS,
            cluster_means,
            profile_names,
            order_dir,
        )

        df_result.to_csv(csv_path, index=False, encoding="utf-8")

        meta = {
            "order_id": order_id,
            "signature": signature,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "answers": int(len(df_result)),
        }

        with open(meta_path, "w", encoding="utf-8") as handle:
            json.dump(meta, handle, ensure_ascii=False, indent=2)

    return _build_result(order_id, order_dir, df_result, signature)


def _build_result(order_id, order_dir, df_result, signature):
    return {
        "available": True,
        "order_id": order_id,
        "reason": None,
        "csv_path": os.path.join(order_dir, CSV_FILENAME),
        "images": {
            key: os.path.join(order_dir, file_name)
            for key, file_name in IMAGE_FILES.items()
        },
        "summary": _summary_from_dataframe(df_result),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "signature": signature,
    }


def _is_cache_valid(order_dir, meta_path, signature, csv_path):
    if not os.path.isfile(meta_path) or not os.path.isfile(csv_path):
        return False

    try:
        with open(meta_path, "r", encoding="utf-8") as handle:
            meta = json.load(handle)
    except Exception:
        return False

    if meta.get("signature") != signature:
        return False

    for file_name in IMAGE_FILES.values():
        if not os.path.isfile(os.path.join(order_dir, file_name)):
            return False

    return True


def _compute_signature(df_raw):
    """Assinatura estável do conjunto de respostas do pedido."""
    content = df_raw.to_csv(index=False, lineterminator="\n")
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _summary_from_dataframe(df_result):
    """Monta o resumo exibido na tela a partir da análise do pedido."""
    students = []

    for _, row in df_result.iterrows():
        students.append({
            "id": _safe_int(row.get("answer_id")),
            "nome": _safe_text(row.get("full_name")),
            "serie": _safe_text(row.get("grade")),
            "turma": _safe_text(row.get("school_class")),
            "idx_socio": _safe_float(row.get("idx_socioeconomic_digital")),
            "idx_trabalho": _safe_float(row.get("idx_work_overload")),
            "idx_vinculo": _safe_float(row.get("idx_school_bonding")),
            "idx_cultural": _safe_float(row.get("idx_cultural_capital")),
            "cluster_id": _safe_int(row.get("cluster")),
            "perfil": _safe_text(row.get("pedagogical_profile")),
            "pca_1": _safe_float(row.get("pca_1")),
            "pca_2": _safe_float(row.get("pca_2")),
        })

    students.sort(key=lambda item: (item["nome"] or "").lower())

    total = len(students)

    if total:
        avg_socio = round(sum(s["idx_socio"] for s in students) / total, 2)
        avg_trabalho = round(
            sum(s["idx_trabalho"] for s in students) / total, 2
        )
        avg_vinculo = round(
            sum(s["idx_vinculo"] for s in students) / total, 2
        )
        avg_cultural = round(
            sum(s["idx_cultural"] for s in students) / total, 2
        )
    else:
        avg_socio = avg_trabalho = avg_vinculo = avg_cultural = 0.0

    perfis_count = {}
    for student in students:
        profile = student["perfil"] or "Não classificado"
        perfis_count[profile] = perfis_count.get(profile, 0) + 1

    return {
        "students": students,
        "total_diagnosticados": total,
        "medias": {
            "socio": avg_socio,
            "trabalho": avg_trabalho,
            "vinculo": avg_vinculo,
            "cultural": avg_cultural,
        },
        "perfis_count": perfis_count,
    }


def _safe_float(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0

    if math.isnan(number) or math.isinf(number):
        return 0.0

    return number


def _safe_int(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if math.isnan(number) or math.isinf(number):
        return None

    return int(number)


def _safe_text(value):
    if value is None:
        return ""

    if isinstance(value, float) and math.isnan(value):
        return ""

    return str(value)
