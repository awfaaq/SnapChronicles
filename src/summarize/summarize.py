# src/summarize/summarize.py
import os
from groq import Groq
from llama_cpp import Llama

# Le chemin du modèle local est maintenant une constante configurable
LOCAL_MODEL_PATH = "./models/Llama-2-7B-Q4_K_M.gguf"

def _summarize_with_groq(prompt_text: str) -> str:
    """Génère un résumé via l’API Groq."""
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        resp = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You are a synthesis assistant. Summarize the key information in one clear sentence."},
                {"role": "user", "content": prompt_text}
            ],
            max_tokens=100, temperature=0.2, stop=["\n"]
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"[ERROR Groq] {e}")
        return f"Erreur API Groq : {e}"

def _summarize_with_local_llama(prompt_text: str, model_path: str) -> str:
    """Génère un résumé en local via llama.cpp."""
    if not os.path.exists(model_path):
        return f"Erreur : Modèle local introuvable à {model_path}."
    try:
        llama = Llama(model_path=model_path, verbose=False, n_ctx=2048)
        out = llama(prompt=prompt_text, max_tokens=100, temperature=0.2, stop=["\n", "</s>"])
        return out['choices'][0]['text'].strip()
    except Exception as e:
        print(f"[ERROR Llama] {e}")
        return f"Erreur LLM Local : {e}"

def generate_summary(ocr_text: str, audio_text: str, mode: str = 'local') -> str:
    """
    Génère un résumé à partir des textes OCR et audio.
    Fonction principale appelée par l'agent.
    """
    prompt = (
        "Synthesize the following information from a screen capture and an audio transcript.\n\n"
        f"Screen Text: {ocr_text if ocr_text else 'None'}\n"
        f"Audio Transcript: {audio_text if audio_text else 'None'}\n\n"
        "Concise summary:"
    )

    if not ocr_text and not audio_text:
        return "No data to summarize."

    print(f"🧠 Génération du résumé en mode '{mode}'...")
    if mode == 'groq':
        return _summarize_with_groq(prompt)
    else: # mode 'local'
        return _summarize_with_local_llama(prompt, LOCAL_MODEL_PATH)
