from flask import Flask, request, jsonify, render_template
from sentence_transformers import SentenceTransformer
import numpy as np
import spacy
import io

app = Flask(__name__)

nlp = spacy.load("en_core_web_sm")
embedder = SentenceTransformer('all-MiniLM-L6-v2')  

# In-memory storage
document_store = {
    'text': None,
    'sentences': [],
    'embeddings': None,
    'entities': None
}


def extract_text(file, filename):
    """Extract text from uploaded file based on extension"""
    ext = filename.rsplit('.', 1)[-1].lower()
    
    if ext == 'pdf':
        import fitz  # PyMuPDF
        pdf = fitz.open(stream=file.read(), filetype="pdf")
        text = ""
        for page in pdf:
            text += page.get_text()
        pdf.close()
        return text
    
    elif ext in ('doc', 'docx'):
        from docx import Document
        doc = Document(io.BytesIO(file.read()))
        return "\n".join([para.text for para in doc.paragraphs])
    
    elif ext == 'txt':
        return file.read().decode('utf-8')
    
    else:
        raise ValueError(f"Unsupported file type: {ext}")


@app.route("/")
def index():
    """Serve the web interface"""
    return render_template('index.html')


@app.route("/upload", methods=["POST"])
def upload():
    """Handle file upload"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    
    if not file.filename:
        return jsonify({'error': 'No file selected'}), 400

    try:
        # Parse document text
        text = extract_text(file, file.filename)
        
        if not text or not text.strip():
            return jsonify({'error': 'Could not extract text from document'}), 400

        # Extract sentences and entities
        doc = nlp(text)
        sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
        entities = [{"text": ent.text, "label": ent.label_} for ent in doc.ents]
        
        # Create embeddings for all sentences
        embeddings = embedder.encode(sentences, convert_to_numpy=True)
        
        # Store everything
        document_store['text'] = text
        document_store['sentences'] = sentences
        document_store['embeddings'] = embeddings
        document_store['entities'] = entities

        return jsonify({
            'message': 'File uploaded and processed successfully',
            'sentences_indexed': len(sentences)
        })
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to process file: {str(e)}'}), 500


@app.route("/query", methods=["POST"])
def query():
    """Handle natural language query with semantic search"""
    data = request.json
    if not data or "query" not in data:
        return jsonify({'error': 'No query provided'}), 400

    query_text = data["query"]
    sentences = document_store.get('sentences')
    embeddings = document_store.get('embeddings')
    entities = document_store.get('entities')

    if not sentences or embeddings is None:
        return jsonify({'error': 'No document uploaded'}), 400

    query_embedding = embedder.encode([query_text], convert_to_numpy=True)[0]
    
    # Calculate cosine similarity with all sentences
    similarities = np.dot(embeddings, query_embedding) / (
        np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_embedding)
    )
    
    # Get top 5 result
    top_k = min(5, len(sentences))
    top_indices = np.argsort(similarities)[::-1][:top_k]
    
    min_similarity = 0.25
    results = []
    for idx in top_indices:
        if similarities[idx] >= min_similarity:
            sent = sentences[idx]
            results.append({
                "text": sent,
                "score": float(similarities[idx]),
                "entities": get_entities(sent, entities)
            })

    return jsonify({"excerpts": results})


def get_entities(text, entities):
    """Get entities within a sentence"""
    return [ent for ent in entities if ent['text'] in text]


if __name__ == "__main__":
    app.run(debug=True)