"""Buscador de frases: encuentra la frase conocida más parecida.
Cada frase se convierte en una lista de números (qué palabras tiene y qué tan
raras son, esto se llama TF-IDF). Dos frases se parecen si sus listas de
números apuntan en direcciones parecidas. """

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from modelo.limpiar import limpiar

def construir_indice(frases_es):
    """Aprende el vocabulario de las frases conocidas y las convierte en números.
    Devuelve (vectorizador, matriz). Usamos nuestra función limpiar() para
    separar las palabras, así todo el proyecto limpia el texto igual."""
    vectorizador = TfidfVectorizer(tokenizer=limpiar, lowercase=False, token_pattern=None)
    matriz = vectorizador.fit_transform(frases_es)
    return vectorizador, matriz

def buscar(frase, vectorizador, matriz, umbral=0.5):
    """Busca la frase conocida más parecida.
    Devuelve (posición, similitud). Si la mejor similitud es menor que el
    umbral, devuelve (None, similitud): es el aviso de "no encontré esa frase"."""
    vector = vectorizador.transform([frase])
    similitudes = cosine_similarity(vector, matriz)[0]
    mejor= int(similitudes.argmax())
    if similitudes[mejor]<umbral:
        return None, float(similitudes[mejor])
    return mejor, float(similitudes[mejor])