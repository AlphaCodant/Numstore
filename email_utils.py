"""
Utilitaires d'envoi d'emails via Resend.
"""

import os
import asyncio
import logging
import resend
from dotenv import load_dotenv
load_dotenv()


logger = logging.getLogger(__name__)


def get_resend_api_key():
    """Récupère la clé API Resend en nettoyant les guillemets."""
    key = os.getenv("RESEND_API_KEY")
    # Enlever les guillemets si présents
    return key


def get_sender_email():
    """Récupère l'email expéditeur en nettoyant les guillemets."""
    email = os.getenv("SENDER_EMAIL")
    return email


async def send_access_code_email(email: str, code: str, product_name: str, expires_in_hours: int = 6) -> bool:
    """Envoie le code d'accès par email."""
    api_key = get_resend_api_key()
    sender_email = get_sender_email()
    
    if not api_key:
        logger.warning("RESEND_API_KEY non configuré, email ignoré")
        return False
    
    # Configure Resend avec la clé
    resend.api_key = api_key
    
    logger.info(f"Envoi email à {email} avec clé: {api_key[:10]}...")
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
        <div style="background-color: #ffffff; padding: 40px; border-radius: 8px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #C9A227; margin: 0; font-size: 28px;">NumStore</h1>
            </div>
            <h2 style="color: #0a0a0a; margin-bottom: 20px;">Votre code d'accès</h2>
            <p style="color: #52525b; font-size: 16px; line-height: 1.6;">
                Merci pour votre achat de <strong>{product_name}</strong> !
            </p>
            <div style="background-color: #0a0a0a; padding: 30px; text-align: center; margin: 30px 0; border-radius: 8px;">
                <p style="color: #a1a1aa; margin: 0 0 10px 0; font-size: 14px;">Votre code d'accès :</p>
                <h1 style="color: #C9A227; font-size: 42px; letter-spacing: 8px; margin: 0; font-family: monospace;">{code}</h1>
            </div>
            <p style="color: #52525b; font-size: 14px; line-height: 1.6;">
                Ce code est valide pendant <strong>{expires_in_hours} heures</strong>.
            </p>
            <p style="color: #52525b; font-size: 14px; line-height: 1.6;">
                Rendez-vous sur notre site et entrez ce code pour accéder à votre produit.
            </p>
        </div>
    </body>
    </html>
    """
    
    try:
        params = {
            "from": sender_email,
            "to": [email],
            "subject": f"Votre code d'accès NumStore - {product_name}",
            "html": html_content
        }
        result = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Email envoyé à {email}, résultat: {result}")
        return True
    except Exception as e:
        logger.error(f"Échec envoi email à {email}: {e}")
        return False


async def send_portfolio_completion_email(email: str, full_name: str, portfolio_url: str) -> bool:
    """Envoie l'email de confirmation quand le portfolio est terminé."""
    api_key = get_resend_api_key()
    sender_email = get_sender_email()
    
    if not api_key:
        logger.warning("RESEND_API_KEY non configuré, email ignoré")
        return False
    
    resend.api_key = api_key
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
        <div style="background-color: #ffffff; padding: 40px; border-radius: 8px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #C9A227; margin: 0; font-size: 28px;">NumStore</h1>
            </div>
            <h2 style="color: #0a0a0a; margin-bottom: 20px;">Votre portfolio est prêt !</h2>
            <p style="color: #52525b; font-size: 16px; line-height: 1.6;">
                Bonjour {full_name},
            </p>
            <p style="color: #52525b; font-size: 16px; line-height: 1.6;">
                Votre portfolio professionnel est maintenant disponible :
            </p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{portfolio_url}" style="display: inline-block; background-color: #C9A227; color: #0a0a0a; padding: 16px 32px; text-decoration: none; font-weight: bold; border-radius: 4px;">
                    Voir mon portfolio
                </a>
            </div>
            <p style="color: #52525b; font-size: 14px; line-height: 1.6;">
                Merci de votre confiance !
            </p>
        </div>
    </body>
    </html>
    """
    
    try:
        params = {
            "from": sender_email,
            "to": [email],
            "subject": "Votre portfolio est prêt !",
            "html": html_content
        }
        result = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Email portfolio envoyé à {email}, résultat: {result}")
        return True
    except Exception as e:
        logger.error(f"Échec envoi email portfolio: {e}")
        return False
