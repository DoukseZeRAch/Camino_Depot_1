import os
import openai
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Récupérer la clé API depuis les variables d'environnement
openai.api_key = os.getenv("OPENAI_API_KEY")

# Fonction pour tester l'API OpenAI avec GPT-4
def test_openai_gpt4():
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Vous êtes un assistant utile et précis."},
                {"role": "user", "content": "Pouvez-vous me donner un exemple de test réussi avec GPT-4 ?"}
            ],
            max_tokens=100,
            temperature=0.7
        )
        print("Réponse de l'API OpenAI (GPT-4) :")
        print(response.choices[0].message["content"].strip())
    except Exception as e:
        print(f"Erreur lors de la connexion à l'API OpenAI : {e}")

if __name__ == "__main__":
    test_openai_gpt4()
