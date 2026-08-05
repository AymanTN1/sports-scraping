import pandas as pd
from pathlib import Path

from src import report_generator


def test_normalize_dataframe_uses_enriched_columns():
    frame = pd.DataFrame(
        [
            {
                "title": "Derby capital",
                "source": "BBC Sport",
                "date": "2026-04-26",
                "category": "Football",
                "resume": "Un resume du match",
                "url": "https://example.com/article",
                "image_url": "https://images.example.com/photo.jpg",
                "credibility": 5,
            }
        ]
    )

    normalized = report_generator.normalize_dataframe(frame)

    assert len(normalized) == 1
    assert normalized.iloc[0]["summary"] == "Un resume du match"
    assert normalized.iloc[0]["image"] == "https://images.example.com/photo.jpg"
    assert normalized.iloc[0]["category"] == "Football"


def test_generate_daily_report_creates_summary_cards(tmp_path, monkeypatch):
    csv_path = tmp_path / "articles.csv"
    pd.DataFrame(
        [
            {
                "title": "Premier sujet fort",
                "source": "BBC Sport",
                "date": "2026-04-26",
                "category": "Football",
                "summary": "Le premier resume detaille",
                "url": "https://example.com/1",
                "image_url": "https://images.example.com/1.jpg",
                "credibility": 5,
            },
            {
                "title": "Deuxieme sujet fort",
                "source": "L'Equipe",
                "date": "2026-04-26",
                "category": "Football",
                "summary": "Le second resume detaille",
                "url": "https://example.com/2",
                "image_url": "",
                "credibility": 4,
            },
            {
                "title": "Temps fort en tennis",
                "source": "Eurosport",
                "date": "2026-04-26",
                "category": "Tennis",
                "summary": "Le resume tennis",
                "url": "https://example.com/3",
                "image_url": "",
                "credibility": 4,
            },
        ]
    ).to_csv(csv_path, index=False)

    monkeypatch.setattr(report_generator, "REPORTS_DIR", tmp_path / "reports")
    report_generator.REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    result = report_generator.generate_daily_report(csv_path)

    assert result is not None
    assert result["count"] == 2

    index_html = Path(result["html"]).read_text(encoding="utf-8")
    football_html = (report_generator.REPORTS_DIR / "Football_latest.html").read_text(encoding="utf-8")

    assert "Rapports quotidiens par categorie" in index_html
    assert "Football" in index_html
    assert "Temps fort" in football_html
    assert "Premier sujet fort" in football_html
    assert "https://images.example.com/1.jpg" in football_html
