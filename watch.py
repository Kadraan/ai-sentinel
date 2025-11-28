import os
import requests
import google.generativeai as genai
from datetime import datetime, timedelta
import time

# Configuration
GITHUB_API_URL = "https://api.github.com"
SEARCH_TOPICS = ["llm", "agentic", "automation", "ai-marketing"]
DAYS_BACK = 30
MIN_NOTE = 7
GEMINI_MODEL = "models/gemini-2.5-flash" # As requested

def get_env_var(name):
    val = os.getenv(name)
    if not val:
        print(f"[ERROR] Variable d'environnement manquante : {name}")
    return val

def get_trending_repos(token):
    """Récupère les dépôts populaires récents."""
    print(f"🔍 Recherche de projets récents ({DAYS_BACK} jours)...")
    date_since = (datetime.now() - timedelta(days=DAYS_BACK)).strftime('%Y-%m-%d')
    query = f"created:>{date_since} " + " ".join([f"topic:{t}" for t in SEARCH_TOPICS])
    
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    params = {"q": query, "sort": "stars", "order": "desc", "per_page": 5}
    
    try:
        resp = requests.get(f"{GITHUB_API_URL}/search/repositories", headers=headers, params=params)
        resp.raise_for_status()
        return resp.json().get("items", [])
    except Exception as e:
        print(f"[ERROR] Recherche GitHub : {e}")
        return []

def issue_exists(token, repo_slug, title_search):
    """Vérifie si une issue existe déjà avec ce titre dans NOTRE dépôt."""
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    # On cherche dans les issues du dépôt courant
    # query: repo:OWNER/REPO is:issue "Titre"
    q = f"repo:{repo_slug} is:issue \"{title_search}\""
    params = {"q": q}
    
    try:
        resp = requests.get(f"{GITHUB_API_URL}/search/issues", headers=headers, params=params)
        resp.raise_for_status()
        count = resp.json().get("total_count", 0)
        return count > 0
    except Exception as e:
        print(f"[WARNING] Vérification issue échouée : {e}")
        return False

def get_readme(repo_full_name, default_branch):
    """Récupère le README brut."""
    url = f"https://raw.githubusercontent.com/{repo_full_name}/{default_branch}/README.md"
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            return resp.text
    except:
        pass
    return None

def analyze_with_gemini(api_key, project_name, readme_content):
    """Analyse le README avec Gemini."""
    genai.configure(api_key=api_key)
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        prompt = f"""
        Tu es un expert en Micro-SaaS et automatisation.
        Analyse ce projet : {project_name}
        
        README:
        {readme_content[:15000]} # Truncate

        Est-il une opportunité pour du Micro-SaaS ou de l'automatisation ?
        Réponds strictement avec ce format :
        NOTE : [0-10]
        VERDICT : [Oui/Non]
        ANALYSE : [Ton analyse détaillée ici]
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"[ERROR] Gemini Analysis : {e}")
        return None

def create_github_issue(token, repo_slug, title, body):
    """Crée une issue sur GitHub."""
    url = f"{GITHUB_API_URL}/repos/{repo_slug}/issues"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    data = {"title": title, "body": body, "labels": ["veille-auto"]}
    
    try:
        resp = requests.post(url, headers=headers, json=data)
        resp.raise_for_status()
        print(f"✅ Issue créée : {title}")
    except Exception as e:
        print(f"[ERROR] Création issue : {e}")

def parse_note(analysis_text):
    try:
        for line in analysis_text.split('\n'):
            if "NOTE :" in line:
                # Extrait "8" de "NOTE : 8/10" ou "NOTE : 8"
                part = line.split(":")[1].strip()
                score = part.split("/")[0].strip()
                return float(score)
    except:
        pass
    return 0

def main():
    # 1. Load Env
    gemini_key = get_env_var('GEMINI_API_KEY')
    github_token = get_env_var('GITHUB_TOKEN')
    my_repo = get_env_var('GITHUB_REPOSITORY') # Format: "owner/repo"

    if not all([gemini_key, github_token, my_repo]):
        return

    # 2. Search
    repos = get_trending_repos(github_token)
    if not repos:
        print("Aucun projet trouvé.")
        return

    print(f"Traitement de {len(repos)} projets...\n")

    for repo in repos:
        name = repo['name']
        full_name = repo['full_name']
        url = repo['html_url']
        issue_title = f"Veille : {name}"

        print(f"👉 Projet : {name}")

        # 3. Deduplication
        if issue_exists(github_token, my_repo, issue_title):
            print(f"   ⚠️ Doublon détecté (Issue existe déjà). Ignoré.")
            continue

        # 4. Get Content
        readme = get_readme(full_name, repo['default_branch'])
        if not readme:
            print("   ⚠️ Pas de README trouvé.")
            continue

        # 5. Analyze
        print("   🤖 Analyse Gemini en cours...")
        analysis = analyze_with_gemini(gemini_key, name, readme)
        if not analysis:
            continue

        note = parse_note(analysis)
        print(f"   📊 Note : {note}/10")

        # 6. Action
        if note > MIN_NOTE:
            body = f"""
# 🤖 Rapport de Veille Automatique

**Projet** : [{name}]({url})
**Description** : {repo['description']}

---

## 🧠 Analyse Gemini
{analysis}

---
*Généré automatiquement par Watch.py*
            """
            create_github_issue(github_token, my_repo, issue_title, body)
        else:
            print("   ❌ Note insuffisante.")
        
        time.sleep(1) # Pause pour éviter rate limits

if __name__ == "__main__":
    main()
