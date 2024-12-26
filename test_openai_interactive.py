import os
import openai
import logging
from dotenv import load_dotenv
from openai import OpenAI
from core.settings.base import OPENAI_API_KEY

client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Configurer la journalisation
logging.basicConfig(
    filename="test_openai.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Récupérer la clé API depuis les variables d'environnement
openai.api_key = os.getenv("OPENAI_API_KEY")

def envoyer_prompt(prompt):
    try:
        # Appel à l'API OpenAI
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Vous êtes un assistant utile."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,  # Contrôle la créativité de la réponse
            max_tokens=150,   # Limite le nombre de tokens dans la réponse
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Erreur : {e}"
if __name__ == "__main__":
    prompt = "Explique la théorie de la relativité en termes simples."
    reponse = envoyer_prompt(prompt)
    print(reponse)

