"""
Script pour migrer la fonctionnalité de src/ vers backend/services
"""

import os
import shutil

# Fichiers à créer/remplacer
FILES_TO_CREATE = {
    "backend/services/ranking_service.py": """\"\"\"
ranking_service.py - Service de classement et filtrage des articles
\"\"\"

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RankingService:
    \"\"\"Service pour le classement et le filtrage des articles\"\"\"
    
    def __init__(self):
        self.weights = {
            "credibility": 0.40,
            "recency": 0.20,
            "engagement": 0.15,
            "source": 0.15,
            "keywords": 0.10,
        }
    
    def rank_articles(self, articles: List[Dict]) -> List[Dict]:
        \"\"\"Classe les articles par pertinence et crédibilité\"\"\"
        scored_articles = []
        
        for article in articles:
            score = self._calculate_ranking_score(article)
            article["ranking_score"] = score
            scored_articles.append(article)
        
        return sorted(scored_articles, key=lambda x: x.get("ranking_score", 0), reverse=True)
    
    def _calculate_ranking_score(self, article: Dict) -> float:
        \"\"\"Calcule le score de classement d'un article\"\"\"
        scores = {}
        
        # 1. Crédibilité (0-1)
        scores["credibility"] = article.get("credibility_score", 0.3)
        
        # 2. Récence (0-1)
        scores["recency"] = self._calculate_recency_score(article)
        
        # 3. Engagement/Reviews (0-1)
        scores["engagement"] = self._calculate_engagement_score(article)
        
        # 4. Source (0-1)
        scores["source"] = min(1.0, article.get("source_credibility", 0.3))
        
        # 5. Keywords/Topics (0-1)
        scores["keywords"] = min(1.0, len(article.get("keywords", [])) / 5.0)
        
        # Score pondéré
        total_score = sum(scores[k] * self.weights[k] for k in scores)
        return min(1.0, total_score)
    
    def _calculate_recency_score(self, article: Dict) -> float:
        \"\"\"Calcule le score de récence\"\"\"
        try:
            if "publish_date" in article and article["publish_date"]:
                pub_date = datetime.fromisoformat(article["publish_date"].replace('Z', '+00:00'))
                now = datetime.utcnow()
                age_hours = (now - pub_date).total_seconds() / 3600
                
                if age_hours < 1:
                    return 1.0
                elif age_hours < 24:
                    return max(0.5, 1.0 - (age_hours / 24) * 0.5)
                elif age_hours < 168:
                    return max(0.1, 0.5 - ((age_hours - 24) / 144) * 0.4)
                else:
                    return 0.1
        except Exception as e:
            logger.warning(f"Erreur calcul récence: {e}")
        
        return 0.5
    
    def _calculate_engagement_score(self, article: Dict) -> float:
        \"\"\"Calcule le score d'engagement\"\"\"
        review_count = article.get("review_count", 0)
        avg_rating = article.get("avg_rating", 0)
        
        if review_count == 0:
            return 0.0
        
        review_score = min(1.0, review_count / 10)
        
        if avg_rating > 0:
            rating_score = min(avg_rating / 5.0)
        else:
            rating_score = 0.5
        
        return (review_score + rating_score) / 2
    
    def filter_articles(self, articles: List[Dict], filters: Dict) -> List[Dict]:
        \"\"\"Filtre les articles selon des critères\"\"\"
        result = articles
        
        if language := filters.get("language"):
            result = [a for a in result if a.get("language") == language]
        
        if source := filters.get("source"):
            result = [a for a in result if source.lower() in (a.get("source", "") or "").lower()]
        
        if min_credibility := filters.get("min_credibility"):
            result = [a for a in result if a.get("credibility_score", 0) >= min_credibility]
        
        if keywords := filters.get("keywords"):
            result = [
                a for a in result
                if any(kw in (a.get("keywords", []) or []) for kw in keywords)
            ]
        
        if max_age_hours := filters.get("max_age_hours"):
            result = [
                a for a in result
                if self._is_within_age_limit(a, max_age_hours)
            ]
        
        if filters.get("verified_only"):
            result = [a for a in result if a.get("verified", False)]
        
        return result
    
    def _is_within_age_limit(self, article: Dict, max_hours: int) -> bool:
        \"\"\"Vérifie si l'article est dans la limite d'âge\"\"\"
        try:
            if "publish_date" in article and article["publish_date"]:
                pub_date = datetime.fromisoformat(article["publish_date"].replace('Z', '+00:00'))
                now = datetime.utcnow()
                age_hours = (now - pub_date).total_seconds() / 3600
                return age_hours <= max_hours
        except Exception as e:
            logger.warning(f"Erreur vérification age: {e}")
        
        return True
\"\"\"
}

def migrate():
    \"\"\"Effectue la migration\"\"\"
    for filepath, content in FILES_TO_CREATE.items():
        full_path = os.path.join(os.getcwd(), filepath)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Créé: {filepath}")

if __name__ == "__main__":
    migrate()
    print("✅ Migration terminée!")
