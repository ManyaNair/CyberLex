CREATE TABLE documents (
  id SERIAL PRIMARY KEY,
  type TEXT NOT NULL,
  title TEXT NOT NULL,
  full_text TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE parties (
  id SERIAL PRIMARY KEY,
  document_id INTEGER REFERENCES documents(id),
  name TEXT NOT NULL,
  type TEXT NOT NULL,
  address TEXT
);

CREATE TABLE provisions (
  id SERIAL PRIMARY KEY,
  document_id INTEGER REFERENCES documents(id),
  type TEXT NOT NULL,
  text TEXT NOT NULL,
  page_num INTEGER  
);

CREATE TABLE citations (
  id SERIAL PRIMARY KEY,
  document_id INTEGER REFERENCES documents(id),
  citation_text TEXT NOT NULL,
  cited_doc_id INTEGER REFERENCES documents(id)
);

CREATE INDEX idx_documents_full_text ON documents USING GIN (to_tsvector('english', full_text));
CREATE INDEX idx_provisions_text ON provisions USING GIN (to_tsvector('english', text));