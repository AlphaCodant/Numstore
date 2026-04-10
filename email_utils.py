"""
Utilitaires d'envoi d'emails via Resend.
"""

import os
import asyncio
import logging
import resend

logger = logging.getLogger(__name__)

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "onboarding@resend.dev")

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY


async def send_access_code_email(email: str, code: str, product_name: str, expires_in_hours: int = 6) -> bool:
    """Envoie le code d'accès par email."""
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY non configuré, email ignoré")
        return False
    
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
                ⏰ <strong>Ce code est valide pendant {expires_in_hours} heures.</strong>
            </p>
        </div>
    </body>
    </html>
    """
    
    try:
        params = {
            "from": SENDER_EMAIL,
            "to": [email],
            "subject": f"🔐 Votre code d'accès NumStore - {product_name}",
            "html": html_content
        }
        await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Email envoyé à {email}")
        return True
    except Exception as e:
        logger.error(f"Échec envoi email: {e}")
        return False


async def send_portfolio_completion_email(email: str, full_name: str, portfolio_url: str) -> bool:
    """Envoie l'email de confirmation quand le portfolio est terminé."""
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY non configuré, email ignoré")
        return False
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
        <div style="background-color: #ffffff; padding: 40px; border-radius: 8px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #C9A227; margin: 0; font-size: 28px;">NumStore</h1>
            </div>
            <h2 style="color: #0a0a0a; margin-bottom: 20px;">🎉 Votre portfolio est prêt !</h2>
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
            "from": SENDER_EMAIL,
            "to": [email],
            "subject": "🎉 Votre portfolio est prêt !",
            "html": html_content
        }
        await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Email portfolio envoyé à {email}")
        return True
    except Exception as e:
        logger.error(f"Échec envoi email portfolio: {e}")
        return False
