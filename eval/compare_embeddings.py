"""Bir embedding modelini Türkçe değerlendirme setiyle ölçer (ADR-006, eval/README.md).

Betik her çalıştırmada tek bir modeli ölçer; iki modeli karşılaştırmak için iki kez
çalıştırılır.

Her soru için sayfalar, bölümlerine olan en yüksek kosinüs benzerliğine göre sıralanır;
Hit@1, Hit@5 ve MRR hesaplanır. "Notlarda yok" sorularının en yüksek skoru, arama eşiğini
(SEARCH_MIN_SCORE) seçmek için raporlanır. Qdrant gerekmez; hesap bellekte yapılır.

Kullanım:
    uv run --project backend python eval/compare_embeddings.py --provider fake
    EMBEDDING_API_KEY=... uv run --project backend python eval/compare_embeddings.py \\
        --base-url https://api.openai.com/v1 --model text-embedding-3-small --dim 1536
"""

import argparse
import math
import os
import sys
import tomllib
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import openai

from kovan.application.ports.ai import EmbeddingProvider
from kovan.infrastructure.ai.fake import FakeEmbeddingProvider
from kovan.infrastructure.ai.openai_compatible import OpenAICompatibleEmbeddingProvider

EVAL_DIR = Path(__file__).resolve().parent
TOP_K = 5
QUESTION_TYPES = {"normal", "synonym", "not_found", "injection"}


@dataclass(frozen=True)
class Section:
    page: str
    text: str


@dataclass(frozen=True)
class Question:
    id: str
    type: str
    question: str
    expected_pages: tuple[str, ...]


@dataclass(frozen=True)
class Result:
    question: Question
    ranking: list[tuple[str, float]]  # (sayfa, skor), yüksekten düşüğe

    @property
    def rank(self) -> int | None:
        """Beklenen sayfalardan ilkinin sırası (1'den başlar); bulunamazsa None."""
        pages = [page for page, _ in self.ranking]
        ranks = [pages.index(p) + 1 for p in self.question.expected_pages if p in pages]
        return min(ranks) if ranks else None


def split_markdown(text: str) -> tuple[str, list[tuple[str, str]]]:
    """'# Başlık' ve '## Bölüm' satırlarına göre (başlık, [(bölüm, metin)]) döner.

    Sayfa başlığı yalnızca ilk '# ' satırıdır; sonraki '# ' satırları (ör. kod yorumu) metindir.
    """
    title, heading = "", ""
    lines: list[str] = []
    sections: list[tuple[str, str]] = []
    for line in text.splitlines():
        if line.startswith("# ") and not title:
            title = heading = line[2:].strip()
        elif line.startswith("## "):
            _append_section(sections, heading, lines)
            heading, lines = line[3:].strip(), []
        else:
            lines.append(line)
    _append_section(sections, heading, lines)
    return title, sections


def _append_section(sections: list[tuple[str, str]], heading: str, lines: list[str]) -> None:
    body = "\n".join(lines).strip()
    if body:
        sections.append((heading, body))


def load_sections(dataset_dir: Path) -> list[Section]:
    """Sayfa kimliği 'üye/dosya-adı'dır; farklı üyelerin aynı adlı dosyaları karışmaz."""
    result = []
    for path in sorted(dataset_dir.glob("*/*.md")):
        title, sections = split_markdown(path.read_text(encoding="utf-8"))
        page = f"{path.parent.name}/{path.stem}"
        result += [Section(page, f"{title} › {head}\n\n{body}") for head, body in sections]
    return result


def load_questions(questions_dir: Path) -> list[Question]:
    questions = []
    for path in sorted(questions_dir.glob("*.toml")):
        for item in tomllib.loads(path.read_text(encoding="utf-8")).get("question", []):
            questions.append(_parse_question(item, owner=path.stem))
    return questions


def _parse_question(item: dict[str, object], *, owner: str) -> Question:
    """Soruyu doğrular. Sayfa adı tek başına yazılmışsa sorunun sahibinin klasöründe aranır."""
    for key in ("id", "question"):
        if not str(item.get(key, "")).strip():
            raise ValueError(f"{owner}.toml: her soruda '{key}' alanı dolu olmalı ({item})")
    question_id = str(item["id"])
    if item.get("type") not in QUESTION_TYPES:
        raise ValueError(f"{question_id}: type şunlardan biri olmalı: {sorted(QUESTION_TYPES)}")
    expected = item.get("expected_pages")
    if not isinstance(expected, list):
        raise ValueError(f"{question_id}: expected_pages bir liste olmalı (notlarda yoksa [])")
    pages = [page if "/" in page else f"{owner}/{page}" for page in map(str, expected)]
    return Question(question_id, str(item["type"]), str(item["question"]), tuple(pages))


def check_expected_pages(questions: list[Question], pages: set[str]) -> None:
    """Yazım hatalı bir sayfa adı sessizce "bulunamadı" sayılıp sonucu bozmasın diye durur."""
    unknown = sorted({p for q in questions for p in q.expected_pages if p not in pages})
    if unknown:
        raise ValueError(f"Olmayan sayfalara atıf var: {', '.join(unknown)}")


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return sum(x * y for x, y in zip(a, b, strict=True)) / norm if norm else 0.0


def evaluate(
    provider: EmbeddingProvider, sections: list[Section], questions: list[Question]
) -> list[Result]:
    section_vectors = provider.embed([section.text for section in sections])
    question_vectors = provider.embed([question.question for question in questions])
    results = []
    for question, q_vector in zip(questions, question_vectors, strict=True):
        best: dict[str, float] = {}
        for section, s_vector in zip(sections, section_vectors, strict=True):
            best[section.page] = max(best.get(section.page, -1.0), cosine(q_vector, s_vector))
        ranking = sorted(best.items(), key=lambda item: item[1], reverse=True)
        results.append(Result(question, ranking))
    return results


def report(label: str, results: list[Result]) -> str:
    answerable = [r for r in results if r.question.expected_pages]
    unanswerable = [r for r in results if not r.question.expected_pages]
    ranks = [r.rank for r in answerable]
    hit1 = sum(1 for rank in ranks if rank == 1) / len(ranks) if ranks else 0.0
    hit5 = sum(1 for rank in ranks if rank and rank <= TOP_K) / len(ranks) if ranks else 0.0
    mrr = sum(1 / rank for rank in ranks if rank) / len(ranks) if ranks else 0.0
    best_answerable = [r.ranking[0][1] for r in answerable if r.ranking]
    best_missing = [r.ranking[0][1] for r in unanswerable if r.ranking]

    lines = [
        f"## Embedding ölçümü: {label}",
        "",
        f"{len(results)} soru ({len(answerable)} cevaplanabilir, {len(unanswerable)} notlarda yok)",
        "",
        "| Metrik | Değer |",
        "| --- | --- |",
        f"| Hit@1 | {hit1:.2f} |",
        f"| Hit@{TOP_K} | {hit5:.2f} |",
        f"| MRR | {mrr:.2f} |",
        f"| Cevaplanabilir soruların en iyi skor ortalaması | {_mean(best_answerable):.3f} |",
        f"| 'Notlarda yok' sorularının en yüksek skoru | {max(best_missing, default=0.0):.3f} |",
        "",
        "| Soru | Tür | Beklenen sayfanın sırası | En yakın sayfa | Skor |",
        "| --- | --- | --- | --- | --- |",
    ]
    for r in results:
        top_page, top_score = r.ranking[0] if r.ranking else ("-", 0.0)
        rank = "-" if not r.question.expected_pages else (r.rank or "bulunamadı")
        lines.append(
            f"| {r.question.id} | {r.question.type} | {rank} | {top_page} | {top_score:.3f} |"
        )
    return "\n".join(lines)


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def build_provider(args: argparse.Namespace) -> EmbeddingProvider:
    if args.provider == "fake":
        return FakeEmbeddingProvider(dimension=256)
    api_key = os.environ.get(args.api_key_env, "")
    if not api_key:
        sys.exit(f"{args.api_key_env} ortam değişkeni boş. Anahtarı koda değil ortama verin.")
    client = openai.OpenAI(api_key=api_key, base_url=args.base_url, timeout=60)
    return OpenAICompatibleEmbeddingProvider(client, model=args.model, dimension=args.dim)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--provider", choices=["fake", "openai_compatible"], default="openai_compatible"
    )
    parser.add_argument("--base-url", default="https://api.openai.com/v1")
    parser.add_argument("--model", default="text-embedding-3-small")
    parser.add_argument("--dim", type=int, default=1536)
    parser.add_argument("--api-key-env", default="EMBEDDING_API_KEY")
    args = parser.parse_args()

    sections = load_sections(EVAL_DIR / "dataset")
    questions = load_questions(EVAL_DIR / "questions")
    check_expected_pages(questions, {section.page for section in sections})
    page_count = len({section.page for section in sections})
    if page_count <= TOP_K:
        print(f"Uyarı: {page_count} sayfa var; Hit@{TOP_K} her zaman 1.00 çıkar.", file=sys.stderr)
    label = "fake" if args.provider == "fake" else args.model
    print(report(label, evaluate(build_provider(args), sections, questions)))


if __name__ == "__main__":
    main()
