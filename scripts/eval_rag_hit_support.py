#!/usr/bin/env python3
"""
Evaluate RAG retrieval quality against a seed set.

Metrics:
- hit@k:     any expected_id appears in top-k results
- support@k: any support_id (or expected_id if support_ids absent) appears in top-k
- MRR@k:     reciprocal rank using expected_ids
- Latency:   p50 / p95 for query time per request

Input seed file (JSONL or CSV):
Each row must have:
  query: str
  expected_ids: list[str] | pipe-separated "id|id|..."
Optional:
  support_ids: list[str] | pipe-separated string

Examples (JSONL):
{"query":"reset password", "expected_ids":["doc_12","doc_98"], "support_ids":["doc_12"]}
{"query":"refund policy",  "expected_ids":["doc_7"]}

Examples (CSV headers):
query,expected_ids,support_ids
"reset password","doc_12|doc_98","doc_12"
"refund policy","doc_7",""

Usage:
  python3 scripts/eval_rag_hit_support.py \
    --weaviate-url http://127.0.0.1:8080 \
    --class DocsV2 \
    --seed seeds/eval_seed.jsonl \
    --k 5 --support-k 3 \
    --expect-hit 0.97 --expect-support 0.95 \
    --mode nearText \
    --report artifacts/eval_rag_$(date -u +%Y%m%dT%H%M%SZ).json
"""

import argparse, csv, json, os, sys, time, statistics, re
from typing import List, Dict, Any
import requests

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weaviate-url", default=os.getenv("WEAVIATE_URL","http://127.0.0.1:8080"))
    ap.add_argument("--class", dest="clazz", default="DocsV2")
    ap.add_argument("--seed", required=True, help="Seed file (jsonl or csv)")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--support-k", type=int, default=3)
    ap.add_argument("--expect-hit", type=float, default=0.97)
    ap.add_argument("--expect-support", type=float, default=0.95)
    ap.add_argument("--mode", choices=["nearText","bm25","hybrid"], default="nearText")
    ap.add_argument("--timeout", type=float, default=10.0)
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--report", default=None)
    ap.add_argument("--id-field", default="doc_id", help="The property that holds the document ID")
    ap.add_argument("--auth-bearer", default=os.getenv("WEAVIATE_BEARER",""))
    return ap.parse_args()

def load_seed(path:str) -> List[Dict[str, Any]]:
    rows=[]
    if path.lower().endswith(".jsonl"):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                obj = json.loads(line)
                rows.append(obj)
    elif path.lower().endswith(".csv"):
        with open(path, newline="", encoding="utf-8") as f:
            rdr = csv.DictReader(f)
            for r in rdr:
                obj = {"query": r["query"]}
                for key in ("expected_ids","support_ids"):
                    s = (r.get(key) or "").strip()
                    if not s:
                        obj[key] = []
                    else:
                        # Allow JSON list or pipe-separated
                        if s.startswith("["):
                            obj[key] = json.loads(s)
                        else:
                            obj[key] = [t for t in s.split("|") if t]
                rows.append(obj)
    else:
        raise ValueError("Seed must be .jsonl or .csv")
    # normalize to sets of strings
    for r in rows:
        r["expected_ids"] = [str(x) for x in r.get("expected_ids",[])]
        supp = r.get("support_ids")
        r["support_ids"] = [str(x) for x in (supp if supp else r["expected_ids"])]
    return rows

def gql_query(url, q, timeout, retries, auth_bearer=""):
    headers = {"Content-Type":"application/json"}
    if auth_bearer:
        headers["Authorization"] = f"Bearer {auth_bearer}"
    last_err = None
    for _ in range(retries+1):
        try:
            t0 = time.time()
            r = requests.post(f"{url}/v1/graphql", json={"query": q}, headers=headers, timeout=timeout)
            dt = time.time()-t0
            if r.status_code != 200:
                last_err = RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")
            else:
                j = r.json()
                if "errors" in j:
                    last_err = RuntimeError(str(j["errors"])[:300])
                else:
                    return j, dt
        except Exception as e:
            last_err = e
        time.sleep(0.2)
    raise last_err

def build_query(clazz, mode, query_text, k, id_field):
    if mode == "nearText":
        # Use server-side vectorizer
        return f'{{ Get {{ {clazz}(nearText:{{concepts:["{escape(query_text)}"]}} limit:{k}) {{ {id_field} _additional{{distance}} }} }} }}'
    elif mode == "bm25":
        return f'{{ Get {{ {clazz}(bm25:{{query:"{escape(query_text)}"}} limit:{k}) {{ {id_field} _additional{{distance}} }} }} }}'
    else:  # hybrid = union of bm25 and nearText (do two queries and merge client-side)
        return None

def escape(s: str) -> str:
    # basic escaping for GraphQL string
    return s.replace("\\", "\\\\").replace('"', '\\"')

def merge_hybrid(res_a, res_b, id_field, k):
    # Stable merge: prefer lower distance when present; dedupe by id
    seen=set(); out=[]
    def items(res):
        # tries to read Get -> Class -> list
        top = res.get("data",{}).get("Get",{})
        key = next(iter(top.keys()), None)
        return top.get(key, []) if key else []
    cand = items(res_a) + items(res_b)
    # Score: favor present distance and smaller values; fallback rank
    def score(i, item):
        d = item.get("_additional",{}).get("distance", None)
        return (0, d) if d is not None else (1, float("inf"))
    ranked = sorted(enumerate(cand), key=lambda t: score(*t))
    for _, it in ranked:
        did = it.get(id_field)
        if did and did not in seen:
            seen.add(did)
            out.append(it)
        if len(out) >= k: break
    return out

def percentile(vals: List[float], p: float) -> float:
    if not vals: return 0.0
    vals_sorted = sorted(vals)
    idx = min(len(vals_sorted)-1, max(0, int(round((p/100.0)*(len(vals_sorted)-1)))))
    return vals_sorted[idx]

def main():
    args = parse_args()
    seeds = load_seed(args.seed)
    if not seeds:
        print("No seeds loaded.", file=sys.stderr); sys.exit(2)

    k = args.k
    sk = args.support_k
    url = args.weaviate_url.rstrip("/")

    hit_count=0
    support_count=0
    mrr_sum=0.0
    latencies=[]

    for row in seeds:
        q = row["query"].strip()
        expected = [str(x) for x in row["expected_ids"]]
        support  = [str(x) for x in row["support_ids"]]

        if args.mode == "hybrid":
            q1 = build_query(args.clazz, "nearText", q, k, args.id_field)
            q2 = build_query(args.clazz, "bm25",    q, k, args.id_field)

            res1, dt1 = gql_query(url, q1, args.timeout, args.retries, args.auth_bearer)
            res2, dt2 = gql_query(url, q2, args.timeout, args.retries, args.auth_bearer)
            latencies.append(max(dt1, dt2))
            topk = merge_hybrid(res1, res2, args.id_field, k)
        else:
            qgql = build_query(args.clazz, args.mode, q, max(k, sk), args.id_field)
            res, dt = gql_query(url, qgql, args.timeout, args.retries, args.auth_bearer)
            latencies.append(dt)
            # Extract list
            top = res.get("data",{}).get("Get",{}).get(args.clazz, [])
            topk = top[:max(k, sk)]

        ids = [str(it.get(args.id_field)) for it in topk if it.get(args.id_field) is not None]

        # hit@k
        hit = int(any(i in expected for i in ids[:k]))
        hit_count += hit

        # support@k (use support set; fallback handled in loader)
        sup = int(any(i in support for i in ids[:sk]))
        support_count += sup

        # MRR@k
        rr = 0.0
        for rank, i in enumerate(ids[:k], start=1):
            if i in expected:
                rr = 1.0 / rank
                break
        mrr_sum += rr

    n = len(seeds)
    hit_at_k      = hit_count / n
    support_at_k  = support_count / n
    mrr_at_k      = mrr_sum / n
    p50 = percentile(latencies, 50)
    p95 = percentile(latencies, 95)

    summary = {
        "total_queries": n,
        "k": k, "support_k": sk, "mode": args.mode, "class": args.clazz,
        "hit@k": round(hit_at_k, 4),
        "support@k": round(support_at_k, 4),
        "mrr@k": round(mrr_at_k, 4),
        "latency_sec_p50": round(p50, 4),
        "latency_sec_p95": round(p95, 4),
        "thresholds": {
            "hit@k": args.expect_hit,
            "support@k": args.expect_support
        },
        "passed": (hit_at_k >= args.expect_hit) and (support_at_k >= args.expect_support)
    }

    print(json.dumps(summary, indent=2))

    if args.report:
        os.makedirs(os.path.dirname(args.report), exist_ok=True)
        with open(args.report, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

    # Hard fail if gates missed
    if not summary["passed"]:
        print("Quality gates not met.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
