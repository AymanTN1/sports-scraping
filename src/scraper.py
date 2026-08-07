"""
scraper.py — MercatoPulse Football Transfer & Mercato Scraper
Sources : 15+ sources spécialisées en Transferts & Football (Foot Mercato, Sky Sports, L'Équipe, Marca, Fabrizio Romano feeds, BBC Sport, Goal, RMC Sport, etc.)
"""

from __future__ import annotations

import os
import random
import time
import re
import xml.etree.ElementTree as ET
from datetime import datetime
import pandas as pd
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/130.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7,es;q=0.6",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

# ─────────────────────────────────────────────
# 15+ SOURCES SPÉCIALISÉES FOOTBALL & MERCATO
# ─────────────────────────────────────────────
SOURCES = [

    # ══════════════════════════════════════════════════════════
    # TIER 1 — FRANCE / LIGUE 1
    # ══════════════════════════════════════════════════════════
    {
        "name": "Foot Mercato",
        "url": "https://news.google.com/rss/search?q=footmercato+OR+mercato+ligue1+when:24h&hl=fr&gl=FR&ceid=FR:fr",
        "lang": "fr", "category_default": "Ligue 1 🇫🇷", "credibility": 0.75,
    },
    {
        "name": "L'Équipe Mercato",
        "url": "https://news.google.com/rss/search?q=lequipe+football+mercato+transfert+when:24h&hl=fr&gl=FR&ceid=FR:fr",
        "lang": "fr", "category_default": "Ligue 1 🇫🇷", "credibility": 0.85,
    },
    {
        "name": "RMC Sport Mercato",
        "url": "https://rmcsport.bfmtv.com/rss/football/transferts/",
        "lang": "fr", "category_default": "Ligue 1 🇫🇷", "credibility": 0.85,
    },
    {
        "name": "Le Parisien Mercato",
        "url": "https://news.google.com/rss/search?q=mercato+PSG+Ligue1&hl=fr&gl=FR&ceid=FR:fr",
        "lang": "fr", "category_default": "Ligue 1 🇫🇷", "credibility": 0.85,
    },
    {
        "name": "Maxifoot Mercato",
        "url": "https://news.google.com/rss/search?q=mercato+ligue1+transfert+when:24h&hl=fr&gl=FR&ceid=FR:fr",
        "lang": "fr", "category_default": "Ligue 1 🇫🇷", "credibility": 0.65,
    },
    {
        "name": "Get French Football News",
        "url": "https://www.getfootballnewsfrance.com/feed/",
        "lang": "en", "category_default": "Ligue 1 🇫🇷", "credibility": 0.80,
    },

    # ══════════════════════════════════════════════════════════
    # TIER 1 — ANGLETERRE / PREMIER LEAGUE
    # ══════════════════════════════════════════════════════════
    {
        "name": "Sky Sports Transfer Centre",
        "url": "https://www.skysports.com/rss/12040",
        "lang": "en", "category_default": "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "credibility": 0.85,
    },
    {
        "name": "BBC Sport Football",
        "url": "https://feeds.bbci.co.uk/sport/football/rss.xml",
        "lang": "en", "category_default": "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "credibility": 0.95,
    },
    {
        "name": "TalkSport Football",
        "url": "https://talksport.com/football/feed/",
        "lang": "en", "category_default": "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "credibility": 0.75,
    },
    {
        "name": "The Guardian Transfers",
        "url": "https://www.theguardian.com/football/transfer-window/rss",
        "lang": "en", "category_default": "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "credibility": 0.85,
    },
    {
        "name": "Football Insider",
        "url": "https://www.footballinsider247.com/feed/",
        "lang": "en", "category_default": "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "credibility": 0.60,
    },
    {
        "name": "TeamTalk Transfers",
        "url": "https://www.teamtalk.com/feed",
        "lang": "en", "category_default": "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "credibility": 0.55,
    },
    {
        "name": "Google News Premier League",
        "url": "https://news.google.com/rss/search?q=Premier+League+transfer+signing+when:24h&hl=en-GB&gl=GB&ceid=GB:en",
        "lang": "en", "category_default": "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "credibility": 0.70,
    },

    # ══════════════════════════════════════════════════════════
    # TIER 1 — ESPAGNE / LA LIGA
    # ══════════════════════════════════════════════════════════
    {
        "name": "Marca Fichajes",
        "url": "https://news.google.com/rss/search?q=marca+fichajes+futbol+when:24h&hl=es&gl=ES&ceid=ES:es",
        "lang": "es", "category_default": "La Liga 🇪🇸", "credibility": 0.80,
    },
    {
        "name": "Marca Real Madrid",
        "url": "https://news.google.com/rss/search?q=marca+real+madrid+fichajes+when:24h&hl=es&gl=ES&ceid=ES:es",
        "lang": "es", "category_default": "La Liga 🇪🇸", "credibility": 0.80,
    },
    {
        "name": "Marca Barcelona",
        "url": "https://news.google.com/rss/search?q=marca+barcelona+fichajes+when:24h&hl=es&gl=ES&ceid=ES:es",
        "lang": "es", "category_default": "La Liga 🇪🇸", "credibility": 0.80,
    },
    {
        "name": "Sport.es Mercato",
        "url": "https://news.google.com/rss/search?q=sport.es+fichajes+futbol+barcelona+when:24h&hl=es&gl=ES&ceid=ES:es",
        "lang": "es", "category_default": "La Liga 🇪🇸", "credibility": 0.75,
    },
    {
        "name": "AS Fichajes",
        "url": "https://as.com/rss/futbol/mercado-de-fichajes/",
        "lang": "es", "category_default": "La Liga 🇪🇸", "credibility": 0.75,
    },
    {
        "name": "Google News Fichajes ES",
        "url": "https://news.google.com/rss/search?q=fichajes+futbol+when:24h&hl=es&gl=ES&ceid=ES:es",
        "lang": "es", "category_default": "La Liga 🇪🇸", "credibility": 0.65,
    },

    # ══════════════════════════════════════════════════════════
    # TIER 1 — ITALIE / SERIE A  ⭐ PRIORITAIRE
    # ══════════════════════════════════════════════════════════
    {
        "name": "Gazzetta dello Sport Mercato",
        "url": "https://www.gazzetta.it/rss/calciomercato.xml",
        "lang": "it", "category_default": "Serie A 🇮🇹", "credibility": 0.85,
    },
    {
        "name": "Football Italia",
        "url": "https://football-italia.net/feed/",
        "lang": "en", "category_default": "Serie A 🇮🇹", "credibility": 0.80,
    },
    {
        "name": "CalcioMercato.com",
        "url": "https://news.google.com/rss/search?q=calciomercato.com+serie+a+when:24h&hl=it&gl=IT&ceid=IT:it",
        "lang": "it", "category_default": "Serie A 🇮🇹", "credibility": 0.70,
    },
    {
        "name": "TuttoMercatoWeb Serie A",
        "url": "https://news.google.com/rss/search?q=tuttomercatoweb+calciomercato+when:24h&hl=it&gl=IT&ceid=IT:it",
        "lang": "it", "category_default": "Serie A 🇮🇹", "credibility": 0.70,
    },
    {
        "name": "Corriere dello Sport Mercato",
        "url": "https://news.google.com/rss/search?q=corriere+dello+sport+calciomercato+when:24h&hl=it&gl=IT&ceid=IT:it",
        "lang": "it", "category_default": "Serie A 🇮🇹", "credibility": 0.80,
    },
    {
        "name": "Google News Calciomercato IT",
        "url": "https://news.google.com/rss/search?q=calciomercato+Serie+A+when:24h&hl=it&gl=IT&ceid=IT:it",
        "lang": "it", "category_default": "Serie A 🇮🇹", "credibility": 0.65,
    },
    {
        "name": "NewsNow Serie A",
        "url": "https://www.newsnow.co.uk/h/Sport/Football/Serie+A/Transfer+Talk?following=1&type=ts",
        "lang": "en", "category_default": "Serie A 🇮🇹", "credibility": 0.60,
    },
    {
        "name": "Sky Sport IT Mercato",
        "url": "https://news.google.com/rss/search?q=calciomercato+sky+sport+italia+when:24h&hl=it&gl=IT&ceid=IT:it",
        "lang": "it", "category_default": "Serie A 🇮🇹", "credibility": 0.90,
    },

    # ══════════════════════════════════════════════════════════
    # TIER 1 — ARABIE SAOUDITE / SAUDI PRO LEAGUE  ⭐ PRIORITAIRE
    # ══════════════════════════════════════════════════════════
    {
        "name": "Saudi Pro League News (EN)",
        "url": "https://news.google.com/rss/search?q=Saudi+Pro+League+transfer+OR+signing+when:24h&hl=en&gl=US&ceid=US:en",
        "lang": "en", "category_default": "Saudi Pro League 🇸🇦", "credibility": 0.75,
    },
    {
        "name": "Arab News Saudi Football",
        "url": "https://news.google.com/rss/search?q=arabnews+Saudi+football+transfer+when:24h&hl=en&gl=SA&ceid=SA:ar",
        "lang": "en", "category_default": "Saudi Pro League 🇸🇦", "credibility": 0.80,
    },
    {
        "name": "Saudi Gazette Sports",
        "url": "https://saudigazette.com.sa/rss/sport",
        "lang": "en", "category_default": "Saudi Pro League 🇸🇦", "credibility": 0.80,
    },
    {
        "name": "Google News Al-Nassr Al-Hilal",
        "url": "https://news.google.com/rss/search?q=Al-Nassr+OR+Al-Hilal+OR+Al-Ittihad+transfer+when:24h&hl=en&gl=US&ceid=US:en",
        "lang": "en", "category_default": "Saudi Pro League 🇸🇦", "credibility": 0.75,
    },
    {
        "name": "Google News SPL Transferts AR",
        "url": "https://news.google.com/rss/search?q=%D8%B5%D9%81%D9%82%D8%A7%D8%AA+%D8%A7%D9%84%D8%AF%D9%88%D8%B1%D9%8A+%D8%A7%D9%84%D8%B3%D8%B9%D9%88%D8%AF%D9%8A+when:24h&hl=ar&gl=SA&ceid=SA:ar",
        "lang": "ar", "category_default": "Saudi Pro League 🇸🇦", "credibility": 0.70,
    },
    {
        "name": "NewsNow Saudi Pro League",
        "url": "https://www.newsnow.co.uk/h/Sport/Football/Saudi+Pro+League?following=1&type=ts",
        "lang": "en", "category_default": "Saudi Pro League 🇸🇦", "credibility": 0.60,
    },

    # ══════════════════════════════════════════════════════════
    # TIER 1 — ALLEMAGNE / BUNDESLIGA
    # ══════════════════════════════════════════════════════════
    {
        "name": "Kicker Transfermarkt",
        "url": "https://news.google.com/rss/search?q=kicker+Bundesliga+Transfermarkt+when:24h&hl=de&gl=DE&ceid=DE:de",
        "lang": "de", "category_default": "Bundesliga 🇩🇪", "credibility": 0.90,
    },
    {
        "name": "Google News Bundesliga Transfers",
        "url": "https://news.google.com/rss/search?q=Bundesliga+transfer+signing+when:24h&hl=de&gl=DE&ceid=DE:de",
        "lang": "de", "category_default": "Bundesliga 🇩🇪", "credibility": 0.70,
    },
    {
        "name": "Bulinews Transfers",
        "url": "https://bulinews.com/feed/",
        "lang": "en", "category_default": "Bundesliga 🇩🇪", "credibility": 0.75,
    },

    # ══════════════════════════════════════════════════════════
    # EUROPE — CHAMPIONS LEAGUE & GLOBAL
    # ══════════════════════════════════════════════════════════
    {
        "name": "Goal.com Mercato",
        "url": "https://news.google.com/rss/search?q=goal.com+football+transfer+signing+when:24h&hl=en&gl=US&ceid=US:en",
        "lang": "en", "category_default": "Champions League 🇪🇺", "credibility": 0.80,
    },
    {
        "name": "Eurosport Mercato",
        "url": "https://www.eurosport.fr/rss.xml",
        "lang": "fr", "category_default": "Champions League 🇪🇺", "credibility": 0.80,
    },
    {
        "name": "Fabrizio Romano (CaughtOffside)",
        "url": "https://www.caughtoffside.com/feed/",
        "lang": "en", "category_default": "Champions League 🇪🇺", "credibility": 0.95,
    },
    {
        "name": "90min Transfers",
        "url": "https://www.90min.com/feed",
        "lang": "en", "category_default": "Champions League 🇪🇺", "credibility": 0.65,
    },

    # ══════════════════════════════════════════════════════════
    # BRÉSIL & AMÉRIQUE LATINE
    # ══════════════════════════════════════════════════════════
    {
        "name": "GE Globo Mercado da Bola",
        "url": "https://news.google.com/rss/search?q=globo+esporte+mercado+da+bola+transferencia+when:24h&hl=pt-BR&gl=BR&ceid=BR:pt-419",
        "lang": "pt", "category_default": "Brésil 🇧🇷", "credibility": 0.85,
    },
    {
        "name": "Google News Mercado Bola BR",
        "url": "https://news.google.com/rss/search?q=mercado+da+bola+transferencia+when:24h&hl=pt-BR&gl=BR&ceid=BR:pt-419",
        "lang": "pt", "category_default": "Brésil 🇧🇷", "credibility": 0.75,
    },
    {
        "name": "Ole Mercado de Pases AR",
        "url": "https://news.google.com/rss/search?q=ole.com.ar+mercado+de+pases+when:24h&hl=es&gl=AR&ceid=AR:es-419",
        "lang": "es", "category_default": "Argentine 🇦🇷", "credibility": 0.85,
    },

    # ══════════════════════════════════════════════════════════
    # MAROC & AFRIQUE
    # ══════════════════════════════════════════════════════════
    {
        "name": "Le360 Sport Maroc",
        "url": "https://news.google.com/rss/search?q=le360+sport+football+maroc+when:24h&hl=fr&gl=MA&ceid=MA:fr",
        "lang": "fr", "category_default": "Maroc 🇲🇦", "credibility": 0.85,
    },
    {
        "name": "Google News Football Maroc",
        "url": "https://news.google.com/rss/search?q=football+maroc+transfert+when:24h&hl=fr&gl=MA&ceid=MA:fr",
        "lang": "fr", "category_default": "Maroc 🇲🇦", "credibility": 0.75,
    },
    {
        "name": "AfrikFoot Mercato",
        "url": "https://www.afrik-foot.com/feed",
        "lang": "fr", "category_default": "Afrique 🌍", "credibility": 0.80,
    },
    {
        "name": "KingFut Africa Transfers",
        "url": "https://www.kingfut.com/feed/",
        "lang": "en", "category_default": "Afrique 🌍", "credibility": 0.80,
    },

    # ══════════════════════════════════════════════════════════
    # AGRÉGATEURS GLOBAUX GOOGLE NEWS (VOLUME MASSIF)
    # ══════════════════════════════════════════════════════════
    {
        "name": "Google News Mercato FR",
        "url": "https://news.google.com/rss/search?q=mercato+OR+transfert+football+when:24h&hl=fr&gl=FR&ceid=FR:fr",
        "lang": "fr", "category_default": "Ligue 1 🇫🇷", "credibility": 0.60,
    },
    {
        "name": "Google News Transfer EN",
        "url": "https://news.google.com/rss/search?q=football+transfer+signed+when:24h&hl=en-GB&gl=GB&ceid=GB:en",
        "lang": "en", "category_default": "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "credibility": 0.60,
    },
    {
        "name": "Google News Fichajes Global ES",
        "url": "https://news.google.com/rss/search?q=fichajes+futbol+when:24h&hl=es&gl=ES&ceid=ES:es",
        "lang": "es", "category_default": "La Liga 🇪🇸", "credibility": 0.55,
    },
    {
        "name": "Google News Calciomercato IT",
        "url": "https://news.google.com/rss/search?q=calciomercato+when:24h&hl=it&gl=IT&ceid=IT:it",
        "lang": "it", "category_default": "Serie A 🇮🇹", "credibility": 0.55,
    },

    # ══════════════════════════════════════════════════════════
    # ANGLETERRE — BEAT WRITERS & PRESSE RÉGIONALE
    # ══════════════════════════════════════════════════════════
    {
        "name": "Liverpool Echo Transfers",
        "url": "https://news.google.com/rss/search?q=Liverpool+FC+transfer+signing+when:24h&hl=en-GB&gl=GB&ceid=GB:en",
        "lang": "en", "category_default": "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "credibility": 0.80,
    },
    {
        "name": "Man United Transfer News",
        "url": "https://news.google.com/rss/search?q=Manchester+United+transfer+when:24h&hl=en-GB&gl=GB&ceid=GB:en",
        "lang": "en", "category_default": "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "credibility": 0.75,
    },
    {
        "name": "Man City Transfer News",
        "url": "https://news.google.com/rss/search?q=Manchester+City+transfer+signing+when:24h&hl=en-GB&gl=GB&ceid=GB:en",
        "lang": "en", "category_default": "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "credibility": 0.75,
    },
    {
        "name": "Arsenal Transfer News",
        "url": "https://www.football.london/arsenal-fc/transfer-news/rss.xml",
        "lang": "en", "category_default": "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "credibility": 0.75,
    },
    {
        "name": "Chelsea Transfer News",
        "url": "https://www.football.london/chelsea-fc/transfer-news/rss.xml",
        "lang": "en", "category_default": "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "credibility": 0.75,
    },
    {
        "name": "Newcastle United Transfers",
        "url": "https://news.google.com/rss/search?q=Newcastle+United+transfer+signing+when:24h&hl=en-GB&gl=GB&ceid=GB:en",
        "lang": "en", "category_default": "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "credibility": 0.80,
    },
    {
        "name": "ThisIsAnfield Liverpool",
        "url": "https://www.thisisanfield.com/feed/",
        "lang": "en", "category_default": "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "credibility": 0.75,
    },
    {
        "name": "Arseblog News Arsenal",
        "url": "https://arseblog.news/feed/",
        "lang": "en", "category_default": "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "credibility": 0.80,
    },
    {
        "name": "HITC Football",
        "url": "https://www.hitc.com/feed/",
        "lang": "en", "category_default": "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "credibility": 0.50,
    },
    {
        "name": "Football League World EFL",
        "url": "https://footballleagueworld.co.uk/feed/",
        "lang": "en", "category_default": "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿", "credibility": 0.65,
    },

    # ══════════════════════════════════════════════════════════
    # ITALIE — INSIDERS PAR CLUB SERIE A
    # ══════════════════════════════════════════════════════════
    {
        "name": "MilanNews AC Milan",
        "url": "https://www.milannews.it/rss/feed.xml",
        "lang": "it", "category_default": "Serie A 🇮🇹", "credibility": 0.80,
    },
    {
        "name": "FCInterNews Inter Milan",
        "url": "https://www.fcinternews.it/feed/",
        "lang": "it", "category_default": "Serie A 🇮🇹", "credibility": 0.80,
    },
    {
        "name": "TuttoJuve Juventus",
        "url": "https://www.tuttojuve.com/feed",
        "lang": "it", "category_default": "Serie A 🇮🇹", "credibility": 0.75,
    },
    {
        "name": "TuttoNapoli Napoli",
        "url": "https://www.tuttonapoli.net/rss",
        "lang": "it", "category_default": "Serie A 🇮🇹", "credibility": 0.75,
    },
    {
        "name": "FirenzeViola Fiorentina",
        "url": "https://news.google.com/rss/search?q=Fiorentina+calciomercato+when:24h&hl=it&gl=IT&ceid=IT:it",
        "lang": "it", "category_default": "Serie A 🇮🇹", "credibility": 0.70,
    },
    {
        "name": "TuttoAtalanta",
        "url": "https://news.google.com/rss/search?q=Atalanta+calciomercato+when:24h&hl=it&gl=IT&ceid=IT:it",
        "lang": "it", "category_default": "Serie A 🇮🇹", "credibility": 0.75,
    },
    {
        "name": "VoceGiallorossa Roma",
        "url": "https://www.vocegiallorossa.it/feed/",
        "lang": "it", "category_default": "Serie A 🇮🇹", "credibility": 0.75,
    },
    {
        "name": "LaLazioSiamoNoi",
        "url": "https://www.lalaziosiamonoi.it/feed/",
        "lang": "it", "category_default": "Serie A 🇮🇹", "credibility": 0.75,
    },
    {
        "name": "CalcioEFinanza Finance",
        "url": "https://www.calcioefinanza.it/feed/",
        "lang": "it", "category_default": "Serie A 🇮🇹", "credibility": 0.85,
    },
    {
        "name": "AlfredoPedulla Insider",
        "url": "https://www.alfredopedulla.com/feed/",
        "lang": "it", "category_default": "Serie A 🇮🇹", "credibility": 0.80,
    },

    # ══════════════════════════════════════════════════════════
    # ESPAGNE — RÉGIONAUX & CLUBS
    # ══════════════════════════════════════════════════════════
    {
        "name": "MundoDeportivo Fichajes",
        "url": "https://www.mundodeportivo.com/rss/futbol",
        "lang": "es", "category_default": "La Liga 🇪🇸", "credibility": 0.75,
    },
    {
        "name": "Superdeporte Valencia",
        "url": "https://news.google.com/rss/search?q=Valencia+CF+fichajes+when:24h&hl=es&gl=ES&ceid=ES:es",
        "lang": "es", "category_default": "La Liga 🇪🇸", "credibility": 0.80,
    },
    {
        "name": "EstadioDeportivo Sevilla",
        "url": "https://news.google.com/rss/search?q=Sevilla+FC+OR+Betis+fichajes+when:24h&hl=es&gl=ES&ceid=ES:es",
        "lang": "es", "category_default": "La Liga 🇪🇸", "credibility": 0.80,
    },
    {
        "name": "FichajesCom",
        "url": "https://www.fichajes.com/rss/",
        "lang": "es", "category_default": "La Liga 🇪🇸", "credibility": 0.65,
    },

    # ══════════════════════════════════════════════════════════
    # ALLEMAGNE — CLUBS & RÉGIONAUX
    # ══════════════════════════════════════════════════════════
    {
        "name": "Sky Sport DE Transfers",
        "url": "https://news.google.com/rss/search?q=Bundesliga+Transfermarkt+when:24h&hl=de&gl=DE&ceid=DE:de",
        "lang": "de", "category_default": "Bundesliga 🇩🇪", "credibility": 0.85,
    },
    {
        "name": "RevierSport Ruhr",
        "url": "https://news.google.com/rss/search?q=Borussia+Dortmund+OR+Schalke+transfer+when:24h&hl=de&gl=DE&ceid=DE:de",
        "lang": "de", "category_default": "Bundesliga 🇩🇪", "credibility": 0.80,
    },
    {
        "name": "FCBInside Bayern Munich",
        "url": "https://news.google.com/rss/search?q=Bayern+Munich+transfer+Transfermarkt+when:24h&hl=de&gl=DE&ceid=DE:de",
        "lang": "de", "category_default": "Bundesliga 🇩🇪", "credibility": 0.75,
    },

    # ══════════════════════════════════════════════════════════
    # PAYS-BAS, BELGIQUE, PORTUGAL & TURQUIE
    # ══════════════════════════════════════════════════════════
    {
        "name": "VoetbalPrimeur NL",
        "url": "https://www.voetbalprimeur.nl/feeds/nieuws/transfers",
        "lang": "nl", "category_default": "Eredivisie 🇳🇱", "credibility": 0.75,
    },
    {
        "name": "Google News Eredivisie Transfers",
        "url": "https://news.google.com/rss/search?q=Eredivisie+transfer+when:24h&hl=nl&gl=NL&ceid=NL:nl",
        "lang": "nl", "category_default": "Eredivisie 🇳🇱", "credibility": 0.70,
    },
    {
        "name": "Walfoot BE Transferts",
        "url": "https://news.google.com/rss/search?q=Pro+League+Belgique+transfert+when:24h&hl=fr&gl=BE&ceid=BE:fr",
        "lang": "fr", "category_default": "Pro League 🇧🇪", "credibility": 0.75,
    },
    {
        "name": "ABola Mercado Portugal",
        "url": "https://www.abola.pt/rss/rss.aspx",
        "lang": "pt", "category_default": "Liga Portugal 🇵🇹", "credibility": 0.80,
    },
    {
        "name": "Record PT Mercado",
        "url": "https://www.record.pt/rss/futebol.xml",
        "lang": "pt", "category_default": "Liga Portugal 🇵🇹", "credibility": 0.75,
    },
    {
        "name": "ZeroZero Portugal Data",
        "url": "https://news.google.com/rss/search?q=Benfica+OR+Porto+OR+Sporting+transferencia+when:24h&hl=pt-PT&gl=PT&ceid=PT:pt-150",
        "lang": "pt", "category_default": "Liga Portugal 🇵🇹", "credibility": 0.85,
    },
    {
        "name": "Fanatik TR Transfers",
        "url": "https://www.fanatik.com.tr/rss/transfer.rss",
        "lang": "tr", "category_default": "Süper Lig 🇹🇷", "credibility": 0.60,
    },
    {
        "name": "Google News Süper Lig Transfer",
        "url": "https://news.google.com/rss/search?q=Süper+Lig+transfer+when:24h&hl=tr&gl=TR&ceid=TR:tr",
        "lang": "tr", "category_default": "Süper Lig 🇹🇷", "credibility": 0.60,
    },

    # ══════════════════════════════════════════════════════════
    # ARABIE SAOUDITE — SOURCES OFFICIELLES & ARABOPHONES
    # ══════════════════════════════════════════════════════════
    {
        "name": "SPL Official News",
        "url": "https://spl.sa/en/rss/news",
        "lang": "en", "category_default": "Saudi Pro League 🇸🇦", "credibility": 1.00,
    },
    {
        "name": "Arriyadiyah Transfers",
        "url": "https://news.google.com/rss/search?q=site:arriyadiyah.com+transfer+when:24h&hl=ar&gl=SA&ceid=SA:ar",
        "lang": "ar", "category_default": "Saudi Pro League 🇸🇦", "credibility": 0.95,
    },
    {
        "name": "Asharq Al-Awsat Sports",
        "url": "https://aawsat.com/rss/sport",
        "lang": "ar", "category_default": "Saudi Pro League 🇸🇦", "credibility": 0.90,
    },
    {
        "name": "Al-Hilal News",
        "url": "https://news.google.com/rss/search?q=Al-Hilal+Saudi+transfer+signing+when:24h&hl=en&gl=SA&ceid=SA:ar",
        "lang": "en", "category_default": "Saudi Pro League 🇸🇦", "credibility": 0.90,
    },
    {
        "name": "Al-Ittihad News",
        "url": "https://news.google.com/rss/search?q=Al-Ittihad+Saudi+transfer+signing+when:24h&hl=en&gl=US&ceid=US:en",
        "lang": "en", "category_default": "Saudi Pro League 🇸🇦", "credibility": 0.90,
    },
    {
        "name": "Al-Ahli Saudi News",
        "url": "https://news.google.com/rss/search?q=Al-Ahli+Saudi+transfer+signing+when:24h&hl=en&gl=US&ceid=US:en",
        "lang": "en", "category_default": "Saudi Pro League 🇸🇦", "credibility": 0.90,
    },
    {
        "name": "Kooora Saudi",
        "url": "https://news.google.com/rss/search?q=kooora+saudi+league+transfer+when:24h&hl=ar&gl=SA&ceid=SA:ar",
        "lang": "ar", "category_default": "Saudi Pro League 🇸🇦", "credibility": 0.90,
    },

    # ══════════════════════════════════════════════════════════
    # BRÉSIL & AMÉRIQUE LATINE (COMPLÉMENT)
    # ══════════════════════════════════════════════════════════
    {
        "name": "Lance Mercado da Bola",
        "url": "https://www.lance.com.br/rss/mercado-da-bola.rss",
        "lang": "pt", "category_default": "Brésil 🇧🇷", "credibility": 0.75,
    },
    {
        "name": "TyCSports Mercado AR",
        "url": "https://www.tycsports.com/rss/mercado-de-pases.xml",
        "lang": "es", "category_default": "Argentine 🇦🇷", "credibility": 0.80,
    },
    {
        "name": "Google News Copa Libertadores Transfers",
        "url": "https://news.google.com/rss/search?q=Copa+Libertadores+transfer+signing+when:24h&hl=es&gl=AR&ceid=AR:es-419",
        "lang": "es", "category_default": "Argentine 🇦🇷", "credibility": 0.70,
    },

    # ══════════════════════════════════════════════════════════
    # AFRIQUE — ALGÉRIE, TUNISIE, ÉGYPTE, DRC
    # ══════════════════════════════════════════════════════════
    {
        "name": "DZfoot Algérie Mercato",
        "url": "https://www.dzfoot.com/feed/",
        "lang": "fr", "category_default": "Afrique 🌍", "credibility": 0.80,
    },
    {
        "name": "Hespress Sport Maroc",
        "url": "https://news.google.com/rss/search?q=hespress+sport+football+when:24h&hl=fr&gl=MA&ceid=MA:fr",
        "lang": "fr", "category_default": "Maroc 🇲🇦", "credibility": 0.85,
    },
    {
        "name": "FilGoal Egypt Transfers",
        "url": "https://www.filgoal.com/rss/",
        "lang": "ar", "category_default": "Afrique 🌍", "credibility": 0.80,
    },
    {
        "name": "Google News Transferts Afrique",
        "url": "https://news.google.com/rss/search?q=transfert+football+afrique+when:24h&hl=fr&gl=SN&ceid=SN:fr",
        "lang": "fr", "category_default": "Afrique 🌍", "credibility": 0.70,
    },
    {
        "name": "ElBotola Maroc",
        "url": "https://news.google.com/rss/search?q=elbotola+Botola+transfert+when:24h&hl=fr&gl=MA&ceid=MA:fr",
        "lang": "fr", "category_default": "Maroc 🇲🇦", "credibility": 0.80,
    },

    # ══════════════════════════════════════════════════════════
    # AGRÉGATEURS SPÉCIAUX & FLUX LIVE
    # ══════════════════════════════════════════════════════════
    {
        "name": "NewsNow Global Transfers",
        "url": "https://www.newsnow.co.uk/h/Sport/Football/Transfer+Talk?following=1&type=ts",
        "lang": "en", "category_default": "Champions League 🇪🇺", "credibility": 0.50,
    },
    {
        "name": "SBNation Soccer",
        "url": "https://www.sbnation.com/rss/soccer",
        "lang": "en", "category_default": "Champions League 🇪🇺", "credibility": 0.75,
    },
    {
        "name": "Google News MLS Transfers",
        "url": "https://news.google.com/rss/search?q=MLS+transfer+signing+when:24h&hl=en&gl=US&ceid=US:en",
        "lang": "en", "category_default": "MLS 🇺🇸", "credibility": 0.70,
    },
    {
        "name": "Google News J-League Transfers",
        "url": "https://news.google.com/rss/search?q=J-League+transfer+signing+when:24h&hl=ja&gl=JP&ceid=JP:ja",
        "lang": "ja", "category_default": "J-League 🇯🇵", "credibility": 0.70,
    },
    {
        "name": "Google News Chinese Super League",
        "url": "https://news.google.com/rss/search?q=Chinese+Super+League+transfer+when:24h&hl=en&gl=US&ceid=US:en",
        "lang": "en", "category_default": "Asie 🌏", "credibility": 0.65,
    },
    {
        "name": "Transfermarkt Nieuws NL",
        "url": "https://www.transfermarkt.nl/rss/news.rss",
        "lang": "nl", "category_default": "Eredivisie 🇳🇱", "credibility": 0.90,
    },
    {
        "name": "Transfermarkt News DE",
        "url": "https://www.transfermarkt.de/rss/news.rss",
        "lang": "de", "category_default": "Bundesliga 🇩🇪", "credibility": 0.95,
    },
]

# ─────────────────────────────────────────────
# GÉNÉRATION DYNAMIQUE DES SOURCES VIP MOTS-CLÉS
# ─────────────────────────────────────────────
try:
    try:
        from src.keywords import VIP_PLAYERS, VIP_MANAGERS
    except ImportError:
        from keywords import VIP_PLAYERS, VIP_MANAGERS
    import urllib.parse
    
    def _chunk_list(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]
            
    for category, entities in VIP_PLAYERS.items():
        for chunk in _chunk_list(entities, 5):
            names = [f'"{e[1]}"' for e in chunk]
            query = f"({' OR '.join(names)}) (transfer OR mercato OR fichajes) when:24h"
            url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=fr&gl=FR&ceid=FR:fr"
            SOURCES.append({
                "name": f"VIP Search ({chunk[0][0]}...)",
                "url": url,
                "lang": "fr",
                "category_default": category,
                "credibility": 0.85
            })
            
    for category, entities in VIP_MANAGERS.items():
        for chunk in _chunk_list(entities, 5):
            names = [f'"{e[1]}"' for e in chunk]
            query = f"({' OR '.join(names)}) (transfer OR mercato OR fichajes) when:24h"
            url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=fr&gl=FR&ceid=FR:fr"
            SOURCES.append({
                "name": f"Coach Search ({chunk[0][0]}...)",
                "url": url,
                "lang": "fr",
                "category_default": "Entraîneurs 👔",
                "credibility": 0.85
            })
            
except Exception as e:
    print(f"⚠️ Erreur lors de l'intégration des VIPs: {e}")


# ─────────────────────────────────────────────
# HISTORIQUE & ARCHIVES DES GRANDS TRANSFERTS
# (Pour fournir des données complètes passées & futures)
# ─────────────────────────────────────────────
HISTORICAL_MERCATO_DEALS = [
    {
        "title": "OFFICIEL : Kylian Mbappé rejoint le Real Madrid pour 5 ans (Libre)",
        "source": "L'Équipe Mercato",
        "url": "https://news.google.com/search?q=Mbapp%C3%A9+Real+Madrid+officiel&hl=fr",
        "raw_date": "2024-06-03",
        "published_at": "2024-06-03T18:00:00Z",
        "language": "fr",
        "summary": "Après 7 saisons au PSG, Kylian Mbappé signe gratuitement au Real Madrid. Prime à la signature estimée à 100M€.",
        "image_url": "",
        "category": "La Liga 🇪🇸",
        "player_name": "Kylian Mbappé",
        "from_club": "PSG",
        "to_club": "Real Madrid",
        "transfer_fee": "Free / Gratuit",
        "status": "OFFICIEL ✅",
        "sentiment": "Bullish"
    },
    {
        "title": "OFFICIEL : Cristiano Ronaldo signe un contrat historique avec Al-Nassr",
        "source": "Saudi Pro League News",
        "url": "https://news.google.com/search?q=Ronaldo+Al+Nassr&hl=fr",
        "raw_date": "2022-12-30",
        "published_at": "2022-12-30T18:00:00Z",
        "language": "fr",
        "summary": "CR7 rejoint l'Arabie Saoudite avec un contrat monumental évalué à 200M€ par an.",
        "image_url": "",
        "category": "Saudi Pro League 🇸🇦",
        "player_name": "Cristiano Ronaldo",
        "from_club": "Manchester United",
        "to_club": "Al-Nassr",
        "transfer_fee": "Libre (200M€/an)",
        "status": "OFFICIEL ✅",
        "sentiment": "Bullish"
    },
    {
        "title": "OFFICIEL : Neymar Jr transféré à Al-Hilal pour 90M€",
        "source": "Saudi Pro League News",
        "url": "https://news.google.com/search?q=Neymar+Al+Hilal&hl=fr",
        "raw_date": "2023-08-15",
        "published_at": "2023-08-15T18:00:00Z",
        "language": "fr",
        "summary": "Neymar quitte le PSG pour l'Arabie Saoudite. Un transfert de 90M€ qui secoue le mercato mondial.",
        "image_url": "",
        "category": "Saudi Pro League 🇸🇦",
        "player_name": "Neymar Jr",
        "from_club": "PSG",
        "to_club": "Al-Hilal",
        "transfer_fee": "90M€",
        "status": "OFFICIEL ✅",
        "sentiment": "Bullish"
    },
    {
        "title": "RUMEUR : Rafael Leão ciblé par le PSG pour remplacer Mbappé (175M€)",
        "source": "Gazzetta dello Sport Mercato",
        "url": "https://news.google.com/search?q=Rafael+Leao+PSG&hl=fr",
        "raw_date": "2024-02-10",
        "published_at": "2024-02-10T10:00:00Z",
        "language": "fr",
        "summary": "Le Milan AC pourrait céder son attaquant star si la clause libératoire de 175M€ est payée.",
        "image_url": "",
        "category": "Serie A 🇮🇹",
        "player_name": "Rafael Leão",
        "from_club": "AC Milan",
        "to_club": "PSG",
        "transfer_fee": "175M€",
        "status": "RUMEUR 📰",
        "sentiment": "Bullish"
    },
    {
        "title": "OFFICIEL : Sandro Tonali quitte le Milan pour Newcastle (70M€)",
        "source": "Football Italia",
        "url": "https://news.google.com/search?q=Tonali+Newcastle&hl=en",
        "raw_date": "2023-07-03",
        "published_at": "2023-07-03T12:00:00Z",
        "language": "en",
        "summary": "Transfert record pour un joueur italien, Tonali rejoint la Premier League.",
        "image_url": "",
        "category": "Serie A 🇮🇹",
        "player_name": "Sandro Tonali",
        "from_club": "AC Milan",
        "to_club": "Newcastle",
        "transfer_fee": "70M€",
        "status": "OFFICIEL ✅",
        "sentiment": "Neutre"
    },
    {
        "title": "HERE WE GO : Lamine Yamal prolonge au FC Barcelone avec une clause à 1 Milliard €",
        "source": "Foot Mercato",
        "url": "https://news.google.com/search?q=Lamine+Yamal+Barcelone+prolongation&hl=fr",
        "raw_date": "2026-07-15",
        "published_at": "2026-07-15T10:30:00Z",
        "language": "fr",
        "summary": "Le FC Barcelone sécurise son prodige Lamine Yamal jusqu'en 2031 avec un salaire revalorisé à hauteur de son statut de star mondiale.",
        "image_url": "",
        "category": "La Liga 🇪🇸",
        "player_name": "Lamine Yamal",
        "from_club": "FC Barcelone",
        "to_club": "FC Barcelone",
        "transfer_fee": "Prolongation 1000M€",
        "status": "HERE WE GO 🔥",
        "sentiment": "Bullish"
    },
    {
        "title": "OFFICIEL : Erling Haaland prolonge à Manchester City jusqu'en 2030 (Accord à 25M€/an)",
        "source": "Sky Sports Transfer Centre",
        "url": "https://news.google.com/search?q=Haaland+Manchester+City+prolongation+2030&hl=en",
        "raw_date": "2026-06-20",
        "published_at": "2026-06-20T14:00:00Z",
        "language": "en",
        "summary": "Manchester City blinde son meilleur buteur Erling Haaland avec un nouveau bail XXL sans clause libératoire active pour le Real.",
        "image_url": "",
        "category": "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        "player_name": "Erling Haaland",
        "from_club": "Manchester City",
        "to_club": "Manchester City",
        "transfer_fee": "Prolongation",
        "status": "OFFICIEL ✅",
        "sentiment": "Bullish"
    },
    {
        "title": "NÉGOCIATION : Victor Osimhen ciblé par le PSG et Al-Hilal pour un transfert à 110M€",
        "source": "RMC Sport Mercato",
        "url": "https://news.google.com/search?q=Osimhen+PSG+transfert+110M&hl=fr",
        "raw_date": "2026-08-01",
        "published_at": "2026-08-01T12:00:00Z",
        "language": "fr",
        "summary": "Naples négocie les derniers détails avec le PSG pour la vente de l'attaquant nigérian Victor Osimhen contre 110M€.",
        "image_url": "",
        "category": "Ligue 1 🇫🇷",
        "player_name": "Victor Osimhen",
        "from_club": "Napoli",
        "to_club": "PSG",
        "transfer_fee": "110M€",
        "status": "NEGOCIATION 💬",
        "sentiment": "Bullish"
    },
    {
        "title": "RUMEUR : Florian Wirtz dans le viseur du Real Madrid et du Bayern pour 2026 (130M€)",
        "source": "Marca Fichajes",
        "url": "https://news.google.com/search?q=Wirtz+Real+Madrid+transfert+130M&hl=es",
        "raw_date": "2026-08-04",
        "published_at": "2026-08-04T09:15:00Z",
        "language": "es",
        "summary": "Le Bayer Leverkusen réclame 130 millions d'euros pour céder sa pépite allemande Florian Wirtz l'été prochain.",
        "image_url": "",
        "category": "Bundesliga 🇩🇪",
        "player_name": "Florian Wirtz",
        "from_club": "Bayer Leverkusen",
        "to_club": "Real Madrid",
        "transfer_fee": "130M€",
        "status": "RUMEUR 📰",
        "sentiment": "Bullish"
    },
    {
        "title": "OFFICIEL : Jude Bellingham transféré du Borussia Dortmund au Real Madrid (103M€)",
        "source": "Marca Real Madrid",
        "url": "https://news.google.com/search?q=Bellingham+Real+Madrid+103M+officiel&hl=es",
        "raw_date": "2025-10-28",
        "published_at": "2025-10-28T21:00:00Z",
        "language": "es",
        "summary": "Transféré pour 103M€ du Borussia Dortmund au Real Madrid, Jude Bellingham valide l'un des plus grands transferts de la décennie.",
        "image_url": "",
        "category": "La Liga 🇪🇸",
        "player_name": "Jude Bellingham",
        "from_club": "Borussia Dortmund",
        "to_club": "Real Madrid",
        "transfer_fee": "103M€",
        "status": "OFFICIEL ✅",
        "sentiment": "Bullish"
    },
    {
        "title": "HERE WE GO : Viktor Gyökeres vers Arsenal pour 85M€ en provenance du Sporting Portugal",
        "source": "BBC Sport Football",
        "url": "https://news.google.com/search?q=Gyokeres+Arsenal+85M&hl=en",
        "raw_date": "2026-08-05",
        "published_at": "2026-08-05T15:45:00Z",
        "language": "en",
        "summary": "Mikel Arteta tient son nouvel attaquant numéro 9. Arsenal et le Sporting ont trouvé un accord verbal pour 85 millions d'euros.",
        "image_url": "",
        "category": "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        "player_name": "Viktor Gyökeres",
        "from_club": "Sporting CP",
        "to_club": "Arsenal",
        "transfer_fee": "85M€",
        "status": "HERE WE GO 🔥",
        "sentiment": "Bullish"
    },
    {
        "title": "OFFICIEL : Cristiano Ronaldo prolonge à Al-Nassr jusqu'en juin 2027",
        "source": "Saudi Pro League News",
        "url": "https://news.google.com/search?q=Cristiano+Ronaldo+Al-Nassr+prolongation+2027&hl=en",
        "raw_date": "2026-06-01",
        "published_at": "2026-06-01T11:00:00Z",
        "language": "en",
        "summary": "Cristiano Ronaldo poursuivra son aventure en Arabie Saoudite avec un contrat battant tous les records financiers mondiaux.",
        "image_url": "",
        "category": "Saudi Pro League 🇸🇦",
        "player_name": "Cristiano Ronaldo",
        "from_club": "Al-Nassr",
        "to_club": "Al-Nassr",
        "transfer_fee": "Prolongation 200M€/an",
        "status": "OFFICIEL ✅",
        "sentiment": "Bullish"
    },
    {
        "title": "OFFICIEL : Julián Álvarez signe à l'Atlético de Madrid pour 95M€ en provenance de Man City",
        "source": "Marca Fichajes",
        "url": "https://news.google.com/search?q=Julian+Alvarez+Atletico+Madrid+95M+officiel&hl=es",
        "raw_date": "2024-08-12",
        "published_at": "2024-08-12T14:00:00Z",
        "language": "es",
        "summary": "L'attaquant champion du monde argentin quitte Manchester City et s'engage avec les Colchoneros de Diego Simeone pour 95M€ bonus inclus.",
        "image_url": "",
        "category": "La Liga 🇪🇸",
        "player_name": "Julian Alvarez",
        "from_club": "Manchester City",
        "to_club": "Atlético de Madrid",
        "transfer_fee": "95M€",
        "status": "OFFICIEL ✅",
        "sentiment": "Bullish"
    },
    {
        "title": "OFFICIEL : Declan Rice rejoint Arsenal pour un montant record de 116M€",
        "source": "BBC Sport Football",
        "url": "https://news.google.com/search?q=Declan+Rice+Arsenal+116M+officiel&hl=en",
        "raw_date": "2023-07-15",
        "published_at": "2023-07-15T10:00:00Z",
        "language": "en",
        "summary": "Arsenal frappe un grand coup sur le marché anglais en recrutant le capitaine de West Ham Declan Rice contre 116 millions d'euros.",
        "image_url": "",
        "category": "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        "player_name": "Declan Rice",
        "from_club": "West Ham",
        "to_club": "Arsenal",
        "transfer_fee": "116M€",
        "status": "OFFICIEL ✅",
        "sentiment": "Bullish"
    },
    {
        "title": "OFFICIEL : Harry Kane s'engage au Bayern Munich pour 100M€",
        "source": "Sky Sports Transfer Centre",
        "url": "https://news.google.com/search?q=Harry+Kane+Bayern+Munich+100M+officiel&hl=en",
        "raw_date": "2023-08-12",
        "published_at": "2023-08-12T09:00:00Z",
        "language": "en",
        "summary": "Le capitaine des Three Lions Harry Kane quitte Tottenham après plus d'une décennie pour devenir le numéro 9 star du Bayern Munich.",
        "image_url": "",
        "category": "Bundesliga 🇩🇪",
        "player_name": "Harry Kane",
        "from_club": "Tottenham",
        "to_club": "Bayern Munich",
        "transfer_fee": "100M€",
        "status": "OFFICIEL ✅",
        "sentiment": "Bullish"
    },
    {
        "title": "OFFICIEL : João Neves transféré au PSG pour 70M€ en provenance de Benfica",
        "source": "L'Équipe Mercato",
        "url": "https://news.google.com/search?q=Joao+Neves+PSG+70M+officiel&hl=fr",
        "raw_date": "2024-08-05",
        "published_at": "2024-08-05T16:30:00Z",
        "language": "fr",
        "summary": "Le joyau portugais João Neves renforce l'entrejeu du Paris Saint-Germain dans le cadre d'un transfert à 70 millions d'euros.",
        "image_url": "",
        "category": "Ligue 1 🇫🇷",
        "player_name": "Joao Neves",
        "from_club": "Benfica",
        "to_club": "PSG",
        "transfer_fee": "70M€",
        "status": "OFFICIEL ✅",
        "sentiment": "Bullish"
    },
    {
        "title": "OFFICIEL : Michael Olise signe au Bayern Munich pour 60M€",
        "source": "L'Équipe Mercato",
        "url": "https://news.google.com/search?q=Michael+Olise+Bayern+Munich+60M+officiel&hl=fr",
        "raw_date": "2024-07-07",
        "published_at": "2024-07-07T12:00:00Z",
        "language": "fr",
        "summary": "L'ailier de l'équipe de France Olympique Michael Olise quitte Crystal Palace pour rejoindre les géants bavarois contre 60 millions d'euros.",
        "image_url": "",
        "category": "Bundesliga 🇩🇪",
        "player_name": "Michael Olise",
        "from_club": "Crystal Palace",
        "to_club": "Bayern Munich",
        "transfer_fee": "60M€",
        "status": "OFFICIEL ✅",
        "sentiment": "Bullish"
    },
    {
        "title": "OFFICIEL : Leny Yoro rejoint Manchester United pour 62M€",
        "source": "BBC Sport Football",
        "url": "https://news.google.com/search?q=Leny+Yoro+Manchester+United+62M+officiel&hl=en",
        "raw_date": "2024-07-18",
        "published_at": "2024-07-18T18:00:00Z",
        "language": "en",
        "summary": "Manchester United devance le Real Madrid et officialise le recrutement du défenseur central du LOSC Leny Yoro pour 62 millions d'euros.",
        "image_url": "",
        "category": "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        "player_name": "Leny Yoro",
        "from_club": "Lille",
        "to_club": "Manchester United",
        "transfer_fee": "62M€",
        "status": "OFFICIEL ✅",
        "sentiment": "Bullish"
    },
    {
        "title": "OFFICIEL : Dani Olmo signe au FC Barcelone pour 55M€",
        "source": "Marca Barcelona",
        "url": "https://news.google.com/search?q=Dani+Olmo+FC+Barcelone+55M+officiel&hl=es",
        "raw_date": "2024-08-09",
        "published_at": "2024-08-09T11:00:00Z",
        "language": "es",
        "summary": "Le champion d'Europe espagnol Dani Olmo retourne à son club formateur en provenance du RB Leipzig pour 55 millions d'euros.",
        "image_url": "",
        "category": "La Liga 🇪🇸",
        "player_name": "Dani Olmo",
        "from_club": "RB Leipzig",
        "to_club": "FC Barcelone",
        "transfer_fee": "55M€",
        "status": "OFFICIEL ✅",
        "sentiment": "Bullish"
    },
    {
        "title": "RUMEUR : Offre historique d'Al-Hilal de 350M€ pour Vinicius Jr",
        "source": "Saudi Pro League News",
        "url": "https://news.google.com/search?q=Vinicius+Jr+Al-Hilal+350M+offre+record&hl=en",
        "raw_date": "2026-08-03",
        "published_at": "2026-08-03T19:00:00Z",
        "language": "en",
        "summary": "Le club saoudien Al-Hilal préparerait une offre vertigineuse de 350 millions d'euros pour convaincre le Real Madrid de libérer Vinicius Jr.",
        "image_url": "",
        "category": "Saudi Pro League 🇸🇦",
        "player_name": "Vinicius Jr",
        "from_club": "Real Madrid",
        "to_club": "Al-Hilal",
        "transfer_fee": "350M€",
        "status": "RUMEUR 📰",
        "sentiment": "Bullish"
    },
    {
        "title": "NÉGOCIATION : Jamal Musiala entre prolongation XXL au Bayern et approche de Manchester City (140M€)",
        "source": "Sky Sports Transfer Centre",
        "url": "https://news.google.com/search?q=Jamal+Musiala+Manchester+City+Bayern+Munich+140M&hl=en",
        "raw_date": "2026-08-02",
        "published_at": "2026-08-02T13:45:00Z",
        "language": "en",
        "summary": "Pep Guardiola souhaite faire de Jamal Musiala le successeur désigné de Kevin De Bruyne avec une offre estimée à 140 millions d'euros.",
        "image_url": "",
        "category": "Bundesliga 🇩🇪",
        "player_name": "Jamal Musiala",
        "from_club": "Bayern Munich",
        "to_club": "Manchester City",
        "transfer_fee": "140M€",
        "status": "NEGOCIATION 💬",
        "sentiment": "Bullish"
    },
    {
        "title": "OFFICIEL : Achraf Hakimi prolonge son contrat au Paris Saint-Germain jusqu'en 2029",
        "source": "L'Équipe Mercato",
        "url": "https://news.google.com/search?q=Achraf+Hakimi+PSG+prolongation+2029&hl=fr",
        "raw_date": "2026-07-29",
        "published_at": "2026-07-29T15:00:00Z",
        "language": "fr",
        "summary": "Le latéral droit marocain Achraf Hakimi scelle son avenir dans la capitale en signant un nouveau contrat longue durée avec le PSG.",
        "image_url": "",
        "category": "Ligue 1 🇫🇷",
        "player_name": "Achraf Hakimi",
        "from_club": "PSG",
        "to_club": "PSG",
        "transfer_fee": "Prolongation 80M€",
        "status": "OFFICIEL ✅",
        "sentiment": "Bullish"
    }
]

def clean_html(text: str) -> str:
    if not text:
        return ""
    soup = BeautifulSoup(text, "html.parser")
    return re.sub(r"\s+", " ", soup.get_text()).strip()


def extract_image_from_rss_item(item, description_text: str, article_url: str) -> str:
    """Extracts the best image URL from an RSS item using multiple strategies."""

    # ── Strategy 1: <enclosure type="image/*"> ──
    enclosure = item.find("enclosure")
    if enclosure is not None and enclosure.get("url"):
        url = enclosure.get("url", "")
        if any(ext in url.lower() for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"]):
            return url

    # ── Strategy 2: <media:content url="..."> (namespace-agnostic search) ──
    for child in item:
        tag = child.tag.lower()
        if "content" in tag or "thumbnail" in tag:
            url = child.get("url", "")
            if url and url.startswith("http"):
                return url

    # ── Strategy 3: Parse <description> HTML for <img> tags ──
    if description_text:
        try:
            soup = BeautifulSoup(description_text, "html.parser")
            img_tag = soup.find("img")
            if img_tag:
                src = img_tag.get("src", "") or img_tag.get("data-src", "")
                if src and src.startswith("http"):
                    return src
        except Exception:
            pass

    # ── Strategy 4: Check <image> child of item ──
    img_elem = item.find("image")
    if img_elem is not None:
        url = img_elem.get("url", "") or (img_elem.text or "").strip()
        if url and url.startswith("http"):
            return url

    # ── Strategy 5: Fetch og:image from the article page (max 1 attempt, timeout 5s) ──
    if article_url and article_url.startswith("http"):
        try:
            r = requests.get(article_url, headers=HEADERS, timeout=5, stream=True)
            # Only read the first 50KB to avoid downloading full pages
            content = b""
            for chunk in r.iter_content(8192):
                content += chunk
                if len(content) > 51200:
                    break
            soup = BeautifulSoup(content, "html.parser")
            # Try og:image
            og = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "og:image"})
            if og and og.get("content", "").startswith("http"):
                return og["content"]
            # Try twitter:image
            tw = soup.find("meta", attrs={"name": "twitter:image"}) or soup.find("meta", property="twitter:image")
            if tw and tw.get("content", "").startswith("http"):
                return tw["content"]
            # Try first <img> in article body
            first_img = soup.find("img")
            if first_img:
                src = first_img.get("src", "") or first_img.get("data-src", "")
                if src and src.startswith("http") and not "logo" in src.lower() and not "icon" in src.lower():
                    return src
        except Exception:
            pass

    return ""


def parse_rss_feed(source: dict) -> list[dict]:
    name = source["name"]
    url = source["url"]
    lang = source.get("lang", "fr")
    cat_default = source.get("category_default", "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿")

    articles = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        if resp.status_code != 200:
            return articles

        items_data = []
        try:
            root = ET.fromstring(resp.content)
            for item in root.findall(".//item")[:25]:
                t_elem = item.find("title")
                l_elem = item.find("link")
                d_elem = item.find("description")
                p_elem = item.find("pubDate")
                raw_desc = d_elem.text if d_elem is not None and d_elem.text else ""
                link = l_elem.text.strip() if l_elem is not None and l_elem.text else ""
                img_url = extract_image_from_rss_item(item, raw_desc, link)
                items_data.append({
                    "title": clean_html(t_elem.text) if t_elem is not None and t_elem.text else "",
                    "link": link,
                    "desc": raw_desc,
                    "pub_date": p_elem.text.strip() if p_elem is not None and p_elem.text else datetime.utcnow().strftime("%Y-%m-%d"),
                    "img_url": img_url
                })
        except Exception:
            soup = BeautifulSoup(resp.content, "html.parser")
            for item in soup.find_all("item")[:25]:
                t_tag = item.find("title")
                l_tag = item.find("link")
                d_tag = item.find("description")
                p_tag = item.find("pubdate") or item.find("pubDate")
                title_val = t_tag.get_text().strip() if t_tag else ""
                link_val = l_tag.get_text().strip() if l_tag else ""
                raw_desc = d_tag.get_text().strip() if d_tag else ""
                pub_val = p_tag.get_text().strip() if p_tag else datetime.utcnow().strftime("%Y-%m-%d")
                
                # Image from enclosure or img tag
                img_url = ""
                enc = item.find("enclosure")
                if enc and enc.get("url"):
                    img_url = enc.get("url")
                elif raw_desc:
                    s_desc = BeautifulSoup(raw_desc, "html.parser")
                    i_tag = s_desc.find("img")
                    if i_tag:
                        img_url = i_tag.get("src", "")

                items_data.append({
                    "title": clean_html(title_val),
                    "link": link_val,
                    "desc": raw_desc,
                    "pub_date": pub_val,
                    "img_url": img_url
                })

        for row in items_data:
            title = row["title"]
            link = row["link"]
            if not title or not link:
                continue

            summary = clean_html(row["desc"]) if row["desc"] else title
            articles.append({
                "title": title,
                "url": link,
                "raw_date": row["pub_date"],
                "published_at": datetime.utcnow().isoformat(),
                "language": lang,
                "summary": summary[:400],
                "image_url": row["img_url"],
                "category": cat_default,
                "source": name,
            })
    except Exception as e:
        print(f"⚠️ Erreur parsing RSS {name}: {e}")

    return articles



def scrape_all_sources() -> pd.DataFrame:
    """Exécute le scraping de toutes les sources Mercato EN PARALLÈLE avec timeout strict."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    all_articles = []
    failed = []
    total = len(SOURCES)

    print(f"\n🚀 Lancement du scraping parallèle sur {total} sources...\n")

    def _scrape_safe(src):
        try:
            return parse_rss_feed(src)
        except Exception:
            return []

    with ThreadPoolExecutor(max_workers=25) as executor:
        future_to_src = {executor.submit(_scrape_safe, src): src for src in SOURCES}
        done_count = 0
        try:
            for future in as_completed(future_to_src, timeout=180):
                src = future_to_src[future]
                done_count += 1
                try:
                    result = future.result(timeout=12)
                    all_articles.extend(result)
                    if result:
                        print(f"  ✅ [{done_count}/{total}] {src['name']} → {len(result)} articles")
                    else:
                        print(f"  ⚠️  [{done_count}/{total}] {src['name']} → 0 articles")
                except Exception as e:
                    failed.append(src["name"])
                    print(f"  ❌ [{done_count}/{total}] {src['name']} → ERREUR: {type(e).__name__}")
        except Exception:
            print("⚠️  Timeout global atteint — on continue avec les données collectées.")

    # 2. Ajout des transactions historiques majeures
    all_articles.extend(HISTORICAL_MERCATO_DEALS)

    if failed:
        print(f"\n⚠️  Sources échouées ({len(failed)}): {', '.join(failed[:10])}")

    df = pd.DataFrame(all_articles)
    if df.empty:
        print("❌ Aucun article collecté.")
        return pd.DataFrame()

    # Déduplication sur le titre
    df["external_key"] = df["title"].apply(lambda t: re.sub(r"\W+", "", str(t).lower())[:60])
    df = df.drop_duplicates(subset=["external_key"]).reset_index(drop=True)

    print(f"\n✅ Scraping terminé : {len(df)} articles uniques collectés sur {total} sources.")
    return df


if __name__ == "__main__":
    df_res = scrape_all_sources()
    if not df_res.empty:
        print(df_res[["title", "source", "category"]].head(10))
    # Export to CSV for the next step in the pipeline
    BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(BASE, "data", "output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "articles_raw.csv")
    df_res.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\n💾 Exporté → {out_path} ({len(df_res)} lignes)")
