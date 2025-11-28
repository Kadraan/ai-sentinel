import os
import google.generativeai as genai

def list_available_models():
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("[ERROR] GEMINI_API_KEY manquante.")
        return

    print(f"Configuration avec la clé API (longueur: {len(api_key)})...")
    genai.configure(api_key=api_key)

    print("\nRecherche des modèles disponibles supportant 'generateContent'...\n")
    
    try:
        count = 0
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
                count += 1
        
        if count == 0:
            print("[WARNING] Aucun modèle trouvé supportant 'generateContent'.")
        else:
            print(f"\nTotal : {count} modèles trouvés.")

    except Exception as e:
        print(f"[ERROR] Impossible de lister les modèles : {e}")

if __name__ == "__main__":
    list_available_models()
