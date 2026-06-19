import ast
import csv
import json
import os
from collections import Counter


ROOTS = {
    "original_test": "/root/rivermind-data/gfm-rag-main/GFM-RAG/GFM-RAG/Test",
    "original_train": "/root/rivermind-data/gfm-training-data/large_scale",
    "converted": "/root/rivermind-data/gfm-training-data-converted/large_scale",
}
OUTPUT = "/root/rivermind-data/gfmrag-all-data-audit.json"


def load_json(path):
    with open(path, encoding="utf-8") as file:
        return json.load(file)


def find_corpus(dataset):
    for name in ("documents.json", "dataset_corpus.json"):
        for directory in ("raw", os.path.join("processed", "stage1")):
            path = os.path.join(dataset, directory, name)
            if os.path.exists(path):
                return path
    return None


def inspect_dataset(group, dataset):
    result = {"group": group, "path": dataset, "name": os.path.basename(dataset)}
    corpus_path = find_corpus(dataset)
    corpus = load_json(corpus_path) if corpus_path else None
    result["corpus_path"] = corpus_path
    result["corpus_documents"] = len(corpus) if isinstance(corpus, dict) else None

    qa = {}
    for split in ("train", "test"):
        candidates = [
            os.path.join(dataset, "processed", "stage1", f"{split}.json"),
            os.path.join(dataset, "raw", f"{split}.json"),
        ]
        path = next((item for item in candidates if os.path.exists(item)), None)
        if path:
            data = load_json(path)
            qa[split] = {
                "path": path,
                "samples": len(data),
                "missing_question": sum(not item.get("question") for item in data),
                "missing_answer": sum("answer" not in item for item in data),
            }
    result["qa"] = qa

    stage = os.path.join(dataset, "processed", "stage1")
    graph_paths = {name: os.path.join(stage, name) for name in ("nodes.csv", "relations.csv", "edges.csv")}
    if not all(os.path.exists(path) for path in graph_paths.values()):
        result["graph"] = {"complete": False}
        return result

    graph = {"complete": True}
    with open(graph_paths["nodes.csv"], newline="", encoding="utf-8") as file:
        nodes = list(csv.DictReader(file))
    names = {row.get("name", row.get("uid")) for row in nodes}
    node_types = Counter(row.get("type") for row in nodes)
    documents = [row for row in nodes if row.get("type") == "document"]
    content_present = 0
    content_matches = 0
    invalid_attributes = 0
    for row in documents:
        try:
            attributes = ast.literal_eval(row.get("attributes") or "{}")
        except Exception:
            invalid_attributes += 1
            continue
        content = attributes.get("content", "")
        content_present += bool(content)
        if corpus and content and content == corpus.get(row.get("name")):
            content_matches += 1
    graph.update(
        {
            "nodes": len(nodes),
            "node_types": dict(node_types),
            "duplicate_node_names": len(nodes) - len(names),
            "document_content_present": content_present,
            "document_content_missing": len(documents) - content_present,
            "document_content_matches_corpus": content_matches,
            "invalid_node_attributes": invalid_attributes,
        }
    )
    relation_names = set()
    with open(graph_paths["relations.csv"], newline="", encoding="utf-8") as file:
        relations = list(csv.DictReader(file))
        relation_names = {row["name"] for row in relations}
    missing_edge_nodes = 0
    missing_edge_relations = 0
    edge_count = 0
    with open(graph_paths["edges.csv"], newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            edge_count += 1
            missing_edge_nodes += row["source"] not in names or row["target"] not in names
            missing_edge_relations += row["relation"] not in relation_names
    graph.update(
        {
            "relations": len(relations),
            "edges": edge_count,
            "edges_missing_nodes": missing_edge_nodes,
            "edges_missing_relations": missing_edge_relations,
        }
    )
    result["graph"] = graph
    return result


results = []
for group, root in ROOTS.items():
    if not os.path.isdir(root):
        continue
    for name in sorted(os.listdir(root)):
        dataset = os.path.join(root, name)
        if os.path.isdir(dataset):
            results.append(inspect_dataset(group, dataset))

summary = {}
for group in ROOTS:
    datasets = [item for item in results if item["group"] == group]
    summary[group] = {
        "datasets": len(datasets),
        "complete_graphs": sum(item["graph"]["complete"] for item in datasets),
        "datasets_missing_document_content": sum(
            item["graph"].get("document_content_missing", 0) > 0 for item in datasets
        ),
        "total_missing_document_content": sum(
            item["graph"].get("document_content_missing", 0) for item in datasets
        ),
        "datasets_with_broken_edges": sum(
            item["graph"].get("edges_missing_nodes", 0) > 0
            or item["graph"].get("edges_missing_relations", 0) > 0
            for item in datasets
        ),
    }

report = {"summary": summary, "datasets": results}
with open(OUTPUT, "w", encoding="utf-8") as file:
    json.dump(report, file, indent=2)
print(json.dumps(summary, indent=2))
print(OUTPUT)
