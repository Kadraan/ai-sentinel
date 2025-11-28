import os
import requests
import google.generativeai as genai
from datetime import datetime, timedelta

# Configuration
GITHUB_API_URL = "https://api.github.com/search/repositories"
TOPICS = ["llm", "artificial-intelligence", "automation", "openai"]
DAYS_BACK = 30
MIN_STARS = 0  # Optional: filter by stars if needed

def get_recent_repos():
    """Récupère les dépôts récents sur les sujets donnés."""
    date_since = (datetime.now() - timedelta(days=DAYS_BACK)).strftime('%Y-%m-%d')
    query = f"created:>{date_since} " + " ".join([f"topic:{t}" for t in TOPICS])
    
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": 5
    }
    
    try:
        response = requests.get(GITHUB_API_URL, params=params)
        response.raise_for_status()
        return response.json().get("items", [])
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Erreur GitHub API : {e}")
        return []

def get_readme_content(repo_full_name, default_branch):
    """Récupère le contenu brut du README."""
    # Essayer README.md, readme.md, README.rst, etc.
    # Pour simplifier, on tape l'API raw content standard de GitHub
    url = f"https://raw.githubusercontent.com/{repo_full_name}/{default_branch}/README.md"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
    except:
        pass
    return None

def analyze_project(repo, readme_content):
    """Analyse le projet avec Gemini."""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("[ERROR] GEMINI_API_KEY manquante.")
        return

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')

    prompt = f"""
    Tu es un investisseur tech. Analyse ce projet GitHub.
    
    Nom: {repo['name']}
    Description: {repo['description']}
    URL: {repo['html_url']}
    
    README Content:
    {readme_content[:10000]}  # Truncate to avoid token limits if huge

    Est-il une opportunité concrète pour générer des revenus passifs ou automatiser du travail ? 
    Réponds strictement dans ce format :
    - NOTE : [Note sur 10]
    - VERDICT : [Oui/Non]
    - POURQUOI : [Une seule phrase explicative]
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"[ERROR] Erreur Gemini : {e}")
        return None

def main():
    print(f"🔍 Recherche de projets récents ({DAYS_BACK} jours) sur : {', '.join(TOPICS)}...")
    repos = get_recent_repos()
    
    if not repos:
        print("Aucun projet trouvé.")
        return

    print(f"Trouvé {len(repos)} projets. Analyse en cours...\n")

    for repo in repos:
        readme = get_readme_content(repo['full_name'], repo['default_branch'])
        if not readme:
            continue

        analysis = analyze_project(repo, readme)
        
        if analysis:
            # Parsing basique pour extraire la note (optionnel, ou juste afficher si > 7)
            # Ici on affiche si la note est > 7 comme demandé
            try:
                # Recherche simple de la note
                lines = analysis.split('\n')
                note_line = next((l for l in lines if "NOTE :" in l), None)
                if note_line:
                    note_str = note_line.split(':')[1].strip().split('/')[0]
                    note = float(note_str)
                    
                    if note > 7:
                        print(f"🚀 PROJET DÉTECTÉ : {repo['name']} ({repo['html_url']})")
                        print(analysis)
                        print("-" * 50)
            except:
                # Si parsing échoue, on affiche tout par sécurité ou on ignore
                pass

if __name__ == "__main__":
    main()
