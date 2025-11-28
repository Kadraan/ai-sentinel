import requests
import time
import sys

def check_health(url):
    start_time = time.time()
    try:
        response = requests.get(url, timeout=10)
        latency = time.time() - start_time
        
        # Vérification du code statut
        if response.status_code != 200:
            print(f"[ERROR] Site inaccessible (Code: {response.status_code})")
            sys.exit(1)

        # Vérification du contenu
        if 'AI Text Cleaner' not in response.text:
            print(f"[ERROR] Site accessible mais contenu 'AI Text Cleaner' manquant.")
            sys.exit(1)

        # Succès
        print(f"[SUCCESS] Site en ligne ({latency:.2f}s)")

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Exception lors de la requête : {e}")

if __name__ == "__main__":
    TARGET_URL = "https://ai-text-cleaner-flax.vercel.app/"
    print(f"Surveillance de {TARGET_URL}...")
    check_health(TARGET_URL)
