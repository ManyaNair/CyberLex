import psycopg2
from psycopg2.extras import RealDictCursor
import tika
from tika import parser

def parse_document(file_path):
  """Extract plain text from legal document using Tika"""
  parsed = parser.from_file(file_path)
  return parsed["content"]

def extract_parties(text):
  """Extract party names from document text"""
  # TODO: Implement spaCy 
  return []

def extract_provisions(text):
  """Extract provisions from document text""" 
  # TODO: Implement provision extraction using regex
  return []

def load_document(cursor, doc):
  """Insert extracted document data into database""" 
  parties = extract_parties(doc['text'])
  provisions = extract_provisions(doc['text'])

  # Insert document
  cursor.execute(
    "INSERT INTO documents (type, title, full_text) VALUES (%s, %s, %s) RETURNING id",
    (doc['type'], doc['title'], doc['text'])
  )
  doc_id = cursor.fetchone()['id']
   
  # Insert parties
  for party in parties:
    cursor.execute(
      "INSERT INTO parties (document_id, name, type) VALUES (%s, %s, %s)",
      (doc_id, party['name'], party['type'])
    )
       
  for provision in provisions:
    cursor.execute(
      "INSERT INTO provisions (document_id, type, text) VALUES (%s, %s, %s)",
      (doc_id, provision['type'], provision['text'])
    )

def main():
  conn = psycopg2.connect("dbname=cyberlex user=cyberlex")
  conn.set_session(autocommit=True)
  cur = conn.cursor(cursor_factory=RealDictCursor)
   
  doc = {
    'type': 'Contract', 
    'title': 'Employment Agreement',
    'text': parse_document('employment_contract.pdf')
  }

  load_document(cur, doc)

if __name__ == '__main__':
  main()