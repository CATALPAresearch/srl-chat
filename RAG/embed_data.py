import os
import pandas as pd
import numpy as np
import requests
import psycopg2
import ast
import pgvector
import math
from psycopg2.extras import execute_values
from pgvector.psycopg2 import register_vector


BASE_URL = os.getenv("EMBEDDING_URL", "https://api-inference.huggingface.co/pipeline/feature-extraction/")
API_KEY = os.getenv("EMBEDDING_TOKEN", "")
MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
connection_string  = f"postgresql://user:pw@localhost:5432/vector"

api_url = f"{BASE_URL}{MODEL}"
headers = {"Authorization": f"Bearer {API_KEY}"}


def query(texts):
    response = requests.post(api_url, headers=headers, json={"inputs": texts, "options": {"wait_for_model": True}})
    return response.json()


def get_embeddings(text_to_embed):
    response = query(text_to_embed)
    return response


# df = pd.read_csv('strategies.csv')
# df.head()
#
# embeddings = []
# for i in range(len(df.index)):
#     text = df['definitions'][i]
#     embedding = get_embeddings(text)
#     embeddings.append(embedding)
#
# df.insert(2, 'embeddings', embeddings)
# df.to_csv('strategies_and_embeddings.csv', index=False)
# ----
# df_vector = pd.read_csv('strategies_and_embeddings.csv')
# df_vector.head()

conn = psycopg2.connect(connection_string)
cur = conn.cursor()

# cur.execute("CREATE EXTENSION IF NOT EXISTS vector");
# conn.commit()
# register_vector(conn)
# table_create_command = """
# CREATE TABLE embedding (
#             id bigserial primary key,
#             category text,
#             definition text,
#             embedding vector(384)
#             );
#             """
#
# cur.execute(table_create_command)
# cur.close()
# conn.commit()
#
# register_vector(conn)
# cur = conn.cursor()
# # Prepare the list of tuples to insert
# df_vector['embeddings'] = df_vector['embeddings'].apply(ast.literal_eval)
# data_list = [(row['categories'], row['definitions'], np.array(row['embeddings'])) for index, row in df_vector.iterrows()]
#
# # Use execute_values to perform batch insertion
# execute_values(cur, "INSERT INTO embedding (category, definition, embedding) VALUES %s", data_list)
# # Commit after we insert all embeddings
# conn.commit()
#
# cur.execute("SELECT COUNT(*) as cnt FROM embedding;")
# num_records = cur.fetchone()[0]
# print("Number of vector records in table: ", num_records,"\n")
# # Correct output should be 129
#
# # print the first record in the table, for sanity-checking
# cur.execute("SELECT * FROM embedding LIMIT 1;")
# records = cur.fetchall()
# print("First record in table: ", records)

# Question about Timescale we want the model to answer
user_input = "I ask for help in the course discord"


# Helper function: Get top 3 most similar documents from the database
def get_top3_similar_docs(query_embedding, connection):
    embedding_array = np.array(query_embedding)
    # Register pgvector extension
    register_vector(connection)
    cursor = connection.cursor()
    # Get the top 3 most similar documents using the KNN <=> operator
    cursor.execute("SELECT category FROM embedding ORDER BY embedding <=> %s LIMIT 3", (embedding_array,))
    top3_docs = cursor.fetchall()
    return top3_docs


input_embedding = get_embeddings(user_input)
related_docs = get_top3_similar_docs(get_embeddings(user_input), conn)
print(related_docs)
