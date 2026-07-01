"""
Steam Games Data Extraction - Versão Otimizada
================================================
Extração rápida com cache e processamento paralelo.
"""

import os
import requests
import pandas as pd
import json
import time
import logging
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Importar módulo de APIs
from api_integrations import ProtonDBAPI, MetacriticAPI, HowLongToBeatAPI

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

API_KEY = os.getenv("API_KEY")
STEAM_ID = os.getenv("STEAM_ID")

STEAM_API_URL = "http://api.steampowered.com/"

# Cache para evitar requisições repetidas
CACHE_DIR = Path("/home/dsouza/Documentos/Projetinhos/analise_steam/data/cache")
CACHE_FILE = CACHE_DIR / "steam_cache.json"

# ==================== CACHE ====================

def load_cache():
    """Carrega cache de requisições anteriores"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE) as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_cache(cache):
    """Salva cache em disco"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)

# ==================== STEAM API ====================

def get_owned_games():
    """Extrai lista de jogos da Steam"""
    logger.info(f"Extraindo jogos da Steam para usuário {STEAM_ID}...")
    url = f"{STEAM_API_URL}IPlayerService/GetOwnedGames/v0001/?key={API_KEY}&steamid={STEAM_ID}&format=json&include_appinfo=1"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('response') and data['response'].get('games'):
            games = data['response']['games']
            logger.info(f"Total de {len(games)} jogos encontrados")
            return games
        else:
            logger.warning("Nenhum jogo encontrado")
            return []
    except Exception as e:
        logger.error(f"Erro ao extrair jogos: {e}")
        return []

def get_game_details(app_id):
    """Busca detalhes do jogo na Steam Store"""
    url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if data.get(str(app_id), {}).get('success'):
            return data[str(app_id)]['data']
    except:
        pass
    return None

# ==================== PROCESSAMENTO PARALELO ====================

def process_single_game(game, cache):
    """Processa um único jogo (thread-safe)"""
    app_id = game.get('appid')
    name = game.get('name', 'Unknown')
    playtime_hours = game.get('playtime_forever', 0) / 60
    
    # Verificar cache
    cache_key = str(app_id)
    if cache_key in cache:
        cached = cache[cache_key]
        cached['name'] = name
        cached['playtime_hours'] = playtime_hours
        cached['is_backlog'] = playtime_hours == 0
        return cached
    
    # Buscar detalhes do jogo (opcional, pode ser lento)
    categories = []
    # Pular busca de detalhes para ganhar tempo
    # details = get_game_details(app_id)
    # if details:
    #     categories = [cat.get('description', '') for cat in details.get('categories', [])]
    
    # Buscar ProtonDB (mais rápido)
    protondb_data = ProtonDBAPI.get_game_summary(app_id)
    steam_deck_status = ProtonDBAPI.get_steam_deck_status(app_id)
    
    # Metacritic (usa cache do dataset local)
    metacritic_score = MetacriticAPI.search_game_score(name)

    # HowLongToBeat (duração estimada)
    hltb_data = HowLongToBeatAPI.search_game(name)
    if hltb_data:
        hltb_main_story = hltb_data['hltb_main_story']
        hltb_main_extra = hltb_data['hltb_main_extra']
        hltb_completionist = hltb_data['hltb_completionist']
        hltb_all_styles = hltb_data['hltb_all_styles']
    else:
        hltb_main_story = 0
        hltb_main_extra = 0
        hltb_completionist = 0
        hltb_all_styles = 0

    # Rate limiting para HLTB
    time.sleep(0.3)

    result = {
        'app_id': app_id,
        'name': name,
        'playtime_hours': playtime_hours,
        'is_backlog': playtime_hours == 0,
        'categories': '; '.join(categories) if categories else 'Unknown',
        'steam_deck_status': steam_deck_status,
        'protondb_tier': protondb_data['tier'] if protondb_data else 'unknown',
        'protondb_score': protondb_data['score'] if protondb_data else 0,
        'metacritic_score': metacritic_score,
        'hltb_main_story': hltb_main_story,
        'hltb_main_extra': hltb_main_extra,
        'hltb_completionist': hltb_completionist,
        'hltb_all_styles': hltb_all_styles
    }
    
    # Salvar no cache
    cache[cache_key] = result
    
    return result

def process_games_parallel(games, max_workers=5):
    """Processa jogos em paralelo"""
    cache = load_cache()
    games_data = []
    
    logger.info(f"Processando {len(games)} jogos com {max_workers} threads...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submeter todas as tarefas
        future_to_game = {
            executor.submit(process_single_game, game, cache): game 
            for game in games
        }
        
        # Coletar resultados
        for idx, future in enumerate(as_completed(future_to_game), 1):
            try:
                result = future.result(timeout=30)
                games_data.append(result)
                
                if idx % 10 == 0:
                    logger.info(f"Progresso: {idx}/{len(games)} jogos processados")
                    save_cache(cache)  # Salvar cache periodicamente
                    
            except Exception as e:
                game = future_to_game[future]
                logger.warning(f"Erro ao processar {game.get('name')}: {e}")
    
    # Salvar cache final
    save_cache(cache)
    
    return games_data

# ==================== MAIN ====================

def main():
    """Função principal"""
    start_time = time.time()
    
    if not API_KEY or not STEAM_ID:
        logger.error("Variáveis de ambiente API_KEY e STEAM_ID não configuradas!")
        return
    
    # Extrair jogos da Steam
    games = get_owned_games()
    
    if not games:
        logger.error("Nenhum jogo encontrado.")
        return
    
    # Processar em paralelo
    games_data = process_games_parallel(games, max_workers=10)
    
    # Converter para DataFrame
    df = pd.DataFrame(games_data)
    
    # Criar diretórios
    raw_dir = Path("/home/dsouza/Documentos/Projetinhos/analise_steam/data/raw")
    processed_dir = Path("/home/dsouza/Documentos/Projetinhos/analise_steam/data/processed")
    
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Salvar dados
    df.to_csv(raw_dir / 'steam_games.csv', index=False, encoding='utf-8')
    df.to_csv(processed_dir / 'steam_games_processed.csv', index=False, encoding='utf-8')
    
    elapsed = time.time() - start_time
    
    # Resumo
    logger.info(f"\n{'='*50}")
    logger.info(f"PROCESSAMENTO CONCLUÍDO EM {elapsed:.1f} SEGUNDOS")
    logger.info(f"{'='*50}")
    logger.info(f"Total de jogos: {len(df)}")
    logger.info(f"Total de horas: {df['playtime_hours'].sum():.1f}")
    logger.info(f"Jogos no backlog: {df['is_backlog'].sum()}")
    logger.info(f"Com Metacritic: {df['metacritic_score'].notna().sum()}")
    logger.info(f"Status Steam Deck:")
    for status, count in df['steam_deck_status'].value_counts().items():
        logger.info(f"  {status}: {count}")
    logger.info(f"Com HLTB: {df['hltb_all_styles'].gt(0).sum()}")
    logger.info(f"Média duração (All Styles): {df[df['hltb_all_styles'] > 0]['hltb_all_styles'].mean():.1f}h")

if __name__ == "__main__":
    main()
