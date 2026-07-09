import sys
import logging
import asyncio
import os
from pathlib import Path

# Asegurar que la carpeta scripts/ esté en el path para importaciones locales
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
from tqdm import tqdm

from config import Config
from youtube_extractor import YouTubeExtractor
from transcript_corrector import TranscriptCorrector
from rag_formatter import RAGFormatter
from twitter_scraper import TwitterPlaywrightScraper

# Configurar logs básicos en consola
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    # 1. Cargar configuración y argumentos de entrada
    config_parser = Config()
    args = config_parser.parse()
    
    # 2. Inicializar formateador común (su salida por defecto será app/data/policy_snippets)
    formatter = RAGFormatter(output_dir=args.output_dir)
    
    all_videos_data = []
    all_tweets_data = []
    
    # 3. EJECUCIÓN DE EXTRACCIÓN DE YOUTUBE (si se especificó --channel)
    if args.channel:
        logger.info("=========================================")
        logger.info("PROCESANDO EXTRACCIÓN DE YOUTUBE")
        logger.info("=========================================")
        extractor = YouTubeExtractor(language_preference=[args.language, "en"])
        corrector = TranscriptCorrector(model_name=args.model)
        
        videos = extractor.get_channel_videos(
            channel_url=args.channel,
            start_date_str=args.start_date,
            end_date_str=args.end_date
        )
        
        if not videos:
            logger.info("No se encontraron videos de YouTube en el rango especificado.")
        else:
            logger.info(f"Comenzando procesamiento de {len(videos)} videos de YouTube...")
            is_ai_active = corrector.client is not None
            if not is_ai_active:
                logger.warning("PROCESANDO EN MODO SIN IA: Los fragmentos no serán corregidos. Define GEMINI_API_KEY en tu .env para habilitar la corrección.")
                
            for idx, video in enumerate(videos, 1):
                video_id = video['id']
                video_title = video['title']
                logger.info(f"[{idx}/{len(videos)}] Procesando video: {video_title} (ID: {video_id})")
                
                transcript_data = extractor.download_transcript(video_id)
                if not transcript_data or not transcript_data.get('segments'):
                    logger.warning(f"Omitiendo video '{video_title}' por falta de subtítulos.")
                    continue
                    
                segments = transcript_data['segments']
                logger.info(f"Subtítulos descargados. Dividiendo en fragmentos de {args.chunk_minutes} minutos...")
                
                chunks = corrector.chunk_transcript(segments, chunk_minutes=args.chunk_minutes)
                logger.info(f"Se crearon {len(chunks)} fragmentos para corregir.")
                
                corrected_chunks = []
                prev_corrected_text = ""
                
                for chunk in tqdm(chunks, desc="Corrigiendo fragmentos", unit="chunk"):
                    raw_text = chunk['text']
                    
                    if is_ai_active:
                        corrected_text = corrector.correct_chunk(
                            raw_text=raw_text,
                            start_time=chunk['start'],
                            end_time=chunk['end'],
                            prev_corrected_text=prev_corrected_text
                        )
                        prev_corrected_text = corrected_text
                    else:
                        corrected_text = raw_text
                        
                    corrected_chunks.append({
                        'start': chunk['start'],
                        'end': chunk['end'],
                        'text_raw': raw_text,
                        'text_corrected': corrected_text
                    })
                    
                # Guardar archivos individuales del video (Markdown va directo al RAG)
                formatter.save_video_data(video, corrected_chunks)
                all_videos_data.append((video, corrected_chunks))
                
    # 4. EJECUCIÓN DE EXTRACCIÓN DE TWITTER (si se especificó --twitter)
    if args.twitter:
        logger.info("\n=========================================")
        logger.info("PROCESANDO EXTRACCIÓN DE TWITTER / X")
        logger.info("=========================================")
        
        # El raspador de Twitter de Playwright es asíncrono, lo ejecutamos mediante asyncio.run
        logger.info(f"Iniciando raspado de publicaciones de Twitter para la cuenta: {args.twitter}")
        # headless=not args.visible controla si se muestra la ventana del navegador
        scraper = TwitterPlaywrightScraper(headless=not args.visible)
        
        try:
            # Ejecutar el scraper de Playwright asíncronamente
            df_tweets = asyncio.run(scraper.run_scraper(
                accounts=[args.twitter],
                start_date=args.start_date,
                end_date=args.end_date
            ))
        except Exception as e:
            logger.error(f"Error crítico en la ejecución del raspador de Twitter: {e}", exc_info=True)
            df_tweets = pd.DataFrame()
            
        if df_tweets.empty:
            logger.warning(f"No se pudieron extraer publicaciones para @{args.twitter} o la cuenta no tiene publicaciones en las fechas indicadas.")
        else:
            logger.info(f"Se extrajeron exitosamente {len(df_tweets)} publicaciones.")
            # Guardar archivos de Twitter (Markdown va directo al RAG)
            formatter.save_tweets_data(args.twitter, df_tweets, args.start_date, args.end_date)
            all_tweets_data.append((args.twitter, df_tweets))
            
    # 5. CREAR BASE DE DATOS UNIFICADA
    if all_videos_data or all_tweets_data:
        unified_path = formatter.create_unified_database(all_videos_data, all_tweets_data)
        logger.info(f"\n=========================================")
        logger.info("PROCESO UNIFICADO FINALIZADO CON ÉXITO")
        logger.info("=========================================")
        logger.info(f"Los archivos de Markdown listos para RAG han sido guardados directamente en: '{args.output_dir}'")
        logger.info(f"Base de datos JSON consolidada creada en: {unified_path}")
    else:
        logger.warning("\nNo se pudo extraer ninguna información (ni de YouTube ni de Twitter). Verifica los parámetros y logs.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nProceso cancelado por el usuario. Saliendo...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error crítico en la ejecución: {e}", exc_info=True)
        sys.exit(1)
