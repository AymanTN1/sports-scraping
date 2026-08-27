from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from backend.core import settings
from backend.models import Article
from backend.repositories import ArticleRepository, SourceRepository
from backend.schemas.article import CsvImportResponse


class CsvIngestionService:
    def __init__(self, db: Session):
        self.db = db
        self.article_repository = ArticleRepository(db)
        self.source_repository = SourceRepository(db)

    @staticmethod
    def get_default_csv_path() -> Path | None:
        candidates_dirs = [
            settings.default_database_path.parent / "output",
            settings.BASE_DIR / "data" / "output",
            Path.cwd() / "data" / "output",
            Path(__file__).resolve().parents[2] / "data" / "output",
        ]
        for c_dir in candidates_dirs:
            if not c_dir.exists():
                continue
            for file_name in ("verified_articles.csv", "organized_articles.csv", "articles.csv"):
                candidate = c_dir / file_name
                if candidate.exists():
                    return candidate
        return None

    def bootstrap_if_needed(self) -> CsvImportResponse | None:
        csv_path = self.get_default_csv_path()
        if not csv_path:
            return None
        return self.import_csv(csv_path)

    def import_csv(self, csv_path: str | Path) -> CsvImportResponse:
        path = Path(csv_path)
        if not path.exists():
            raise FileNotFoundError(path)

        df = pd.read_csv(path)
        normalized = self._normalize_dataframe(df)

        from backend.models import Article, Source

        existing_sources = {s.name: s for s in self.db.query(Source).all() if s.name}
        existing_articles = {a.external_key: a for a in self.db.query(Article).all() if a.external_key}

        inserted = 0
        updated = 0
        batch_to_add = []

        for row in normalized:
            s_name = row["source"]
            source = existing_sources.get(s_name)
            if not source:
                source = Source(
                    name=s_name,
                    language=row["language"],
                    credibility_score=row["credibility"],
                )
                self.db.add(source)
                self.db.flush()
                existing_sources[s_name] = source
            else:
                if row["language"] and not source.language:
                    source.language = row["language"]
                if row["credibility"] and row["credibility"] > float(source.credibility_score or 0):
                    source.credibility_score = row["credibility"]

            article = existing_articles.get(row["external_key"])
            if not article:
                article = Article(external_key=row["external_key"], source_id=source.id)
                batch_to_add.append(article)
                existing_articles[row["external_key"]] = article
                inserted += 1
            else:
                updated += 1

            article.title = row["title"]
            article.url = row["url"]
            article.raw_date = row["raw_date"]
            article.published_at = row["published_at"]
            article.language = row["language"]
            article.category = row["category"]
            article.sentiment = row["sentiment"]
            article.player_name = row.get("player_name")
            article.from_club = row.get("from_club")
            article.to_club = row.get("to_club")
            article.league = row.get("league") or row.get("category")
            article.transfer_fee = row.get("transfer_fee")
            article.status = row.get("status") or "RUMEUR 📰"
            article.summary = row["summary"]
            img_url = str(row.get("image_url") or "").strip()
            if not img_url or img_url == "nan" or not img_url.startswith("http"):
                img_url = ""
            article.image_url = img_url or None
            article.image_caption = row.get("image_caption")
            article.credibility_score = row["credibility"]
            fee_num = row.get("fee_numeric")
            try:
                article.fee_numeric = float(fee_num) if fee_num and str(fee_num) != "nan" else 0
            except (ValueError, TypeError):
                article.fee_numeric = 0
            sem_hash = str(row.get("semantic_hash") or "").strip()
            article.semantic_hash = sem_hash if sem_hash and sem_hash != "nan" else None
            article.source_id = source.id

        if batch_to_add:
            self.db.add_all(batch_to_add)

        self.db.commit()
        return CsvImportResponse(
            source_file=str(path),
            inserted_articles=inserted,
            updated_articles=updated,
            total_articles=self.article_repository.count(),
        )

    def _normalize_dataframe(self, df: pd.DataFrame) -> list[dict]:
        from src.ai_organizer import analyze_sentiment, extract_mercato_entities, classify_article

        frame = df.copy()
        frame.columns = [str(column).strip() for column in frame.columns]

        rows: list[dict] = []
        seen_keys: set[str] = set()
        for _, row in frame.iterrows():
            title = self._polish_text(self._first_non_empty(row, "title", "titre"))
            summary = self._polish_text(self._first_non_empty(row, "summary", "summary.1", "resume", "resume.1"))
            source = self._polish_text(self._first_non_empty(row, "source")) or "Source inconnue"
            from src.mercato_nlp import is_football_mercato_article
            if not title or not is_football_mercato_article(title, summary or "", source=source):
                continue
            raw_date = self._clean_value(self._first_non_empty(row, "date"))
            url = self._clean_value(self._first_non_empty(row, "url", "lien"))
            summary = self._polish_text(self._first_non_empty(row, "summary", "summary.1", "resume", "resume.1"))
            category = self._polish_text(self._first_non_empty(row, "category", "categorie", "discipline", "league")) or classify_article({"title": title, "summary": summary})
            language = self._clean_value(self._first_non_empty(row, "lang", "language"))
            sentiment = self._clean_value(self._first_non_empty(row, "sentiment"))
            image_url = self._normalize_image_url(self._first_non_empty(row, "image", "image_url", "image.1", "image_url.1"))
            image_caption = self._polish_text(self._first_non_empty(row, "image_caption", "caption"))
            credibility = self._parse_float(self._first_non_empty(row, "credibility", "credibilite"))

            player_name = self._clean_value(self._first_non_empty(row, "player_name", "player"))
            from_club = self._clean_value(self._first_non_empty(row, "from_club"))
            to_club = self._clean_value(self._first_non_empty(row, "to_club"))
            league = self._clean_value(self._first_non_empty(row, "league")) or category
            transfer_fee = self._clean_value(self._first_non_empty(row, "transfer_fee", "fee"))
            status = self._clean_value(self._first_non_empty(row, "status"))

            if not summary:
                summary = self._shorten(title, 220)

            if not sentiment:
                sentiment = analyze_sentiment(title, summary)

            # Toujours appliquer le moteur NLP haute précision pour corriger inversions et placeholders
            extracted = extract_mercato_entities(title, summary)
            if not player_name or player_name in ["Joueur Star", "Joueur Mercato", "nan"]:
                player_name = extracted["player_name"]
            if not from_club or from_club in ["Club Vendeur", "Club Acquéreur", "nan"]:
                from_club = extracted["from_club"]
            if not to_club or to_club in ["Club Acheteur", "Club Cible", "nan"]:
                to_club = extracted["to_club"]
            if not status or status == "nan":
                status = extracted["status"]
            if not transfer_fee or transfer_fee == "nan":
                transfer_fee = extracted.get("transfer_fee", "Non communiqué")

            external_key = self._build_external_key(source=source, title=title, raw_date=raw_date, url=url)
            if external_key in seen_keys:
                continue
            seen_keys.add(external_key)

            rows.append(
                {
                    "external_key": external_key,
                    "title": title,
                    "source": source,
                    "raw_date": raw_date,
                    "published_at": self._parse_date(raw_date),
                    "url": url or None,
                    "summary": summary,
                    "category": category,
                    "sentiment": sentiment,
                    "player_name": player_name,
                    "from_club": from_club,
                    "to_club": to_club,
                    "league": league,
                    "transfer_fee": transfer_fee,
                    "status": status,
                    "language": language or None,
                    "image_url": image_url or None,
                    "image_caption": image_caption or None,
                    "credibility": credibility,
                }
            )
        return rows

    @staticmethod
    def _column_matches(column_name: str, alias: str) -> bool:
        name = column_name.lower()
        alias_lower = alias.lower()
        return name == alias_lower or name.startswith(f"{alias_lower}.")

    def _first_non_empty(self, row: pd.Series, *aliases: str) -> str:
        for alias in aliases:
            for column in row.index:
                if self._column_matches(str(column), alias):
                    value = self._clean_value(row.get(column))
                    if value:
                        return value
        return ""

    @staticmethod
    def _clean_value(value) -> str:
        if pd.isna(value):
            return ""
        text = str(value).strip()
        return "" if text.lower() in {"", "nan", "none", "null", "nat"} else text

    def _polish_text(self, value) -> str:
        text = self._clean_value(value)
        if not text:
            return ""
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"([,;:!?])([^\s])", r"\1 \2", text)
        text = re.sub(r"([a-zà-öø-ÿ])([A-ZÀ-ÖØ-Þ])", r"\1 \2", text)
        text = re.sub(r"([0-9])([A-Za-zÀ-ÿ])", r"\1 \2", text)
        text = re.sub(r"([A-Za-zÀ-ÿ])([0-9])", r"\1 \2", text)
        return text.strip()

    @staticmethod
    def _shorten(text: str, limit: int) -> str:
        return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"

    @staticmethod
    def _parse_float(value) -> float:
        text = "" if value is None else str(value).strip()
        try:
            return float(text) if text else 0.0
        except ValueError:
            return 0.0

    @staticmethod
    def _normalize_image_url(value: str) -> str:
        text = str(value or "").strip()
        if not text:
            return ""
        if text.startswith(("http://", "https://", "/images/")):
            return text
        normalized = text.replace("\\", "/")
        if normalized.startswith("data/images/"):
            normalized = normalized.removeprefix("data/images/")
        if normalized.startswith("images/"):
            normalized = normalized.removeprefix("images/")
        return f"/images/{normalized.lstrip('/')}"

    @staticmethod
    def _build_external_key(*, source: str, title: str, raw_date: str, url: str) -> str:
        payload = f"{source}|{title}|{url}|{raw_date}"
        return hashlib.sha1(payload.encode("utf-8", errors="ignore")).hexdigest()

    @staticmethod
    def _parse_date(raw_date: str) -> datetime | None:
        text = (raw_date or "").strip()
        if not text:
            return None
        token = text[:10]
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(token, fmt)
            except ValueError:
                continue
        return None
