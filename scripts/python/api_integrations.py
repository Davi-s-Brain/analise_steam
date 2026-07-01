"""
Módulo de integração com APIs externas:
- ProtonDB API para compatibilidade Steam Deck
- Metacritic API para scores de jogos (com fallback via dataset)
- OpenCritic API para scores alternativos
"""

import requests
import time
import logging
import pandas as pd
from typing import Optional, Dict, Any
from pathlib import Path
import os

logger = logging.getLogger(__name__)

# ==================== PROTONDB API ====================

class ProtonDBAPI:
    """Cliente para API pública do ProtonDB"""
    
    BASE_URL = "https://www.protondb.com/api/v1"
    
    # Mapeamento de tiers para status legível
    TIER_MAP = {
        "native": "Nativo",
        "platinum": "Platina",
        "gold": "Ouro",
        "silver": "Prata",
        "bronze": "Bronze",
        "borked": "Não funciona",
        "pending": "Pendente"
    }
    
    @classmethod
    def get_game_summary(cls, app_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtém resumo de compatibilidade de um jogo.
        
        Args:
            app_id: ID do jogo na Steam
            
        Returns:
            Dict com tier, confidence, score, total reports ou None
        """
        url = f"{cls.BASE_URL}/reports/summaries/{app_id}.json"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                "tier": data.get("tier", "pending"),
                "tier_pt": cls.TIER_MAP.get(data.get("tier", ""), "Desconhecido"),
                "confidence": data.get("confidence", "none"),
                "total_reports": data.get("total", 0),
                "score": data.get("score", 0),
                "best_reported_tier": data.get("bestReportedTier"),
                "trending_tier": data.get("trendingTier")
            }
        except requests.exceptions.RequestException as e:
            logger.warning(f"Erro ao buscar ProtonDB para app {app_id}: {e}")
            return None
    
    @classmethod
    def get_steam_deck_status(cls, app_id: int) -> str:
        """
        Retorna status simplificado para Steam Deck.
        
        Returns:
            "Verified", "Playable", "ProtonDB OK", "Unknown"
        """
        summary = cls.get_game_summary(app_id)
        
        if not summary:
            return "Unknown"
        
        tier = summary["tier"]
        score = summary["score"]
        
        # Classificar baseado no tier e score
        if tier == "native":
            return "Verified"
        elif tier in ["platinum", "gold"] and score >= 0.7:
            return "Verified"
        elif tier in ["silver", "bronze"] and score >= 0.4:
            return "Playable"
        elif tier == "borked":
            return "Unsupported"
        else:
            return "Unknown"


# ==================== METACRITIC API ====================

class MetacriticAPI:
    """Cliente para busca de scores no Metacritic"""
    
    # Dataset local de fallback
    DATASET_PATH = Path("/tmp/metacritic_games.csv")
    _dataset = None
    
    @classmethod
    def _load_dataset(cls):
        """Carrega dataset local de Metacritic"""
        if cls._dataset is None and cls.DATASET_PATH.exists():
            try:
                cls._dataset = pd.read_csv(cls.DATASET_PATH)
                logger.info(f"Dataset Metacritic carregado: {len(cls._dataset)} jogos")
            except Exception as e:
                logger.warning(f"Erro ao carregar dataset Metacritic: {e}")
                cls._dataset = pd.DataFrame()
        return cls._dataset
    
    @classmethod
    def search_game_score(cls, game_name: str) -> Optional[int]:
        """
        Busca score Metacritic de um jogo.
        
        Args:
            game_name: Nome do jogo
            
        Returns:
            Score (0-100) ou None se não encontrado
        """
        # 1. Tentar dataset local primeiro (mais rápido e confiável)
        dataset = cls._load_dataset()
        if dataset is not None and not dataset.empty:
            # Buscar por nome (case-insensitive, parcial)
            match = dataset[dataset['game'].str.contains(game_name, case=False, na=False)]
            if not match.empty:
                score = match.iloc[0]['metascore']
                if pd.notna(score):
                    return int(score)
        
        # 2. Tentar OpenCritic como alternativa
        open_critic_score = OpenCriticAPI.get_game_score(game_name)
        if open_critic_score:
            return open_critic_score
        
        # 3. Tentar API online do Metacritic (fallback final)
        try:
            autocomplete_url = f"https://www.metacritic.com/autosearch?query={game_name.replace(' ', '+')}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json'
            }
            
            response = requests.get(autocomplete_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'result' in data and data['result']:
                    for item in data['result']:
                        if item.get('type') == 'game':
                            item_url = item.get('url', '')
                            if '/game/' in item_url:
                                return cls._extract_score_from_url(item_url)
            
            return None
            
        except Exception as e:
            logger.warning(f"Erro ao buscar Metacritic para '{game_name}': {e}")
            return None
    
    @classmethod
    def _extract_score_from_url(cls, url: str) -> Optional[int]:
        """Tenta extrair score de uma URL do Metacritic"""
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(f"https://www.metacritic.com{url}", headers=headers, timeout=10)
            
            if response.status_code == 200:
                import re
                match = re.search(r'"scoreValue"\s*:\s*"?(\d+)"?', response.text)
                if match:
                    return int(match.group(1))
        except:
            pass
        return None


# ==================== OPENCRITIC API ====================

class OpenCriticAPI:
    """Cliente para API do OpenCritic (via RapidAPI)"""
    
    BASE_URL = "https://opencritic-api.p.rapidapi.com"
    
    # Tier mapping do OpenCritic
    TIER_MAP = {
        "Mighty": "Excelente",
        "Strong": "Bom",
        "Fair": "Regular",
        "Weak": "Fraco"
    }
    
    @classmethod
    def _get_api_key(cls) -> Optional[str]:
        """Obtém chave da API do OpenCritic"""
        # Tentar variável de ambiente
        api_key = os.getenv("OPENCRITIC_API_KEY")
        if api_key:
            return api_key
        
        # Tentar arquivo .env
        try:
            from dotenv import load_dotenv
            load_dotenv()
            return os.getenv("OPENCRITIC_API_KEY")
        except:
            pass
        
        return None
    
    @classmethod
    def search_game(cls, game_name: str) -> Optional[Dict[str, Any]]:
        """
        Busca jogo no OpenCritic.
        
        Args:
            game_name: Nome do jogo
            
        Returns:
            Dict com id, name, score, tier ou None
        """
        api_key = cls._get_api_key()
        if not api_key:
            logger.debug("Chave API OpenCritic não configurada")
            return None
        
        try:
            url = f"{cls.BASE_URL}/game/search"
            params = {"criteria": game_name}
            headers = {
                "X-RapidAPI-Key": api_key,
                "X-RapidAPI-Host": "opencritic-api.p.rapidapi.com"
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    # Retornar primeiro resultado
                    game = data[0]
                    return {
                        "id": game.get("id"),
                        "name": game.get("name"),
                        "score": game.get("topCriticScore"),
                        "tier": game.get("tier"),
                        "tier_pt": cls.TIER_MAP.get(game.get("tier", ""), "Desconhecido"),
                        "num_reviews": game.get("numReviews", 0)
                    }
            
            return None
            
        except Exception as e:
            logger.warning(f"Erro ao buscar OpenCritic para '{game_name}': {e}")
            return None
    
    @classmethod
    def get_game_score(cls, game_name: str) -> Optional[int]:
        """
        Obtém score do OpenCritic.
        
        Args:
            game_name: Nome do jogo
            
        Returns:
            Score (0-100) ou None
        """
        result = cls.search_game(game_name)
        if result and result.get("score"):
            return int(result["score"])
        return None
    
    @classmethod
    def get_game_tier(cls, game_name: str) -> Optional[str]:
        """
        Obtém tier do OpenCritic.
        
        Returns:
            Tier em português ou None
        """
        result = cls.search_game(game_name)
        if result:
            return result.get("tier_pt")
        return None


# ==================== FUNÇÕES AUXILIARES ====================

def enrich_game_data(game: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enriquece dados do jogo com informações do ProtonDB e Metacritic.
    
    Args:
        game: Dict com app_id e name
        
    Returns:
        Dict enriquecido com protondb_tier, metacritic_score
    """
    app_id = game.get('app_id')
    name = game.get('name', '')
    
    # Buscar dados do ProtonDB
    if app_id is not None:
        protondb_data = ProtonDBAPI.get_game_summary(int(app_id))
        if protondb_data:
            game['protondb_tier'] = protondb_data['tier']
            game['protondb_tier_pt'] = protondb_data['tier_pt']
            game['protondb_confidence'] = protondb_data['confidence']
            game['protondb_score'] = protondb_data['score']
            game['steam_deck_status'] = ProtonDBAPI.get_steam_deck_status(int(app_id))
        else:
            game['protondb_tier'] = 'unknown'
            game['protondb_tier_pt'] = 'Desconhecido'
            game['protondb_confidence'] = 'none'
            game['protondb_score'] = 0
            game['steam_deck_status'] = 'Unknown'
    else:
        game['protondb_tier'] = 'unknown'
        game['protondb_tier_pt'] = 'Desconhecido'
        game['protondb_confidence'] = 'none'
        game['protondb_score'] = 0
        game['steam_deck_status'] = 'Unknown'
    
    # Rate limiting
    time.sleep(0.5)
    
    return game


# ==================== HOW LONG TO BEAT API ====================

class HowLongToBeatAPI:
    """Cliente para HowLongToBeat - dados de duração de jogos"""

    @staticmethod
    def search_game(game_name: str) -> Optional[Dict[str, Any]]:
        """
        Busca dados de duração de um jogo no HowLongToBeat.

        Args:
            game_name: Nome do jogo

        Returns:
            Dict com hltb_main_story, hltb_main_extra, hltb_completionist, hltb_all_styles ou None
        """
        try:
            from howlongtobeatpy import HowLongToBeat

            results = HowLongToBeat(0.4).search(game_name, similarity_case_sensitive=False)

            if results is not None and len(results) > 0:
                best = max(results, key=lambda e: e.similarity)

                return {
                    "hltb_main_story": best.main_story or 0,
                    "hltb_main_extra": best.main_extra or 0,
                    "hltb_completionist": best.completionist or 0,
                    "hltb_all_styles": best.all_styles or 0,
                    "hltb_game_name": best.game_name,
                    "hltb_similarity": best.similarity
                }

            return None

        except Exception as e:
            logger.warning(f"Erro ao buscar HLTB para '{game_name}': {e}")
            return None


if __name__ == "__main__":
    # Teste rápido
    print("=== Teste ProtonDB API ===")
    summary = ProtonDBAPI.get_game_summary(413150)  # Stardew Valley
    if summary:
        print(f"Stardew Valley: {summary['tier_pt']} (score: {summary['score']:.2f})")
    
    print("\n=== Teste Steam Deck Status ===")
    status = ProtonDBAPI.get_steam_deck_status(413150)
    print(f"Stardew Valley Deck Status: {status}")
