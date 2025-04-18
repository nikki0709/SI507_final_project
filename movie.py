import pandas as pd
import json
import os
import json
import networkx as nx

# File paths
imdb_path = '/Users/jialuyuan/Desktop/SI507/final_project/imdb_top_1000.csv'
netflix_path = '/Users/jialuyuan/Desktop/SI507/final_project/netflix_titles.csv'

# Load datasets
imdb_df = pd.read_csv(imdb_path)
netflix_df = pd.read_csv(netflix_path)

# ----------------------------
# IMDb Data Cleaning
# ----------------------------

# Fill missing values
imdb_df[['Director', 'Star1', 'Star2', 'Star3', 'Star4', 'Genre']] = imdb_df[
    ['Director', 'Star1', 'Star2', 'Star3', 'Star4', 'Genre']
].fillna('')

# Combine cast into list
imdb_df['cast'] = imdb_df[['Star1', 'Star2', 'Star3', 'Star4']].values.tolist()
imdb_df['cast'] = imdb_df['cast'].apply(lambda x: [i.strip() for i in x if i.strip() != ''])

# Clean and split genres
imdb_df['genres'] = imdb_df['Genre'].apply(lambda x: [g.strip().lower() for g in x.split(',')])

# Clean title and director
imdb_df['title'] = imdb_df['Series_Title'].str.strip()
imdb_df['director'] = imdb_df['Director'].str.strip()

# Select cleaned fields
imdb_cleaned = imdb_df[['title', 'Released_Year', 'genres', 'director', 'cast']]
imdb_cleaned.rename(columns={'Released_Year': 'release_year'}, inplace=True)

# ----------------------------
# Netflix Data Cleaning
# ----------------------------

# Fill missing values
netflix_df[['director', 'cast', 'listed_in']] = netflix_df[['director', 'cast', 'listed_in']].fillna('')

# Clean and split cast
netflix_df['cast'] = netflix_df['cast'].apply(lambda x: [i.strip() for i in x.split(',') if i.strip() != ''])

# Clean and split genres
netflix_df['genres'] = netflix_df['listed_in'].apply(lambda x: [g.strip().lower() for g in x.split(',') if g.strip() != ''])

# Clean title and director
netflix_df['title'] = netflix_df['title'].str.strip()
netflix_df['director'] = netflix_df['director'].str.strip()

# Select cleaned fields
netflix_cleaned = netflix_df[['title', 'release_year', 'genres', 'director', 'cast']]

# ----------------------------
# Caching Data
# ----------------------------

# Convert to list of dictionaries
imdb_records = imdb_cleaned.to_dict(orient='records')
netflix_records = netflix_cleaned.to_dict(orient='records')

# Create cache directory
cache_dir = 'cache'
os.makedirs(cache_dir, exist_ok=True)

# Write to JSON files
with open(os.path.join(cache_dir, 'imdb_cache.json'), 'w') as f:
    json.dump(imdb_records, f, indent=2)

with open(os.path.join(cache_dir, 'netflix_cache.json'), 'w') as f:
    json.dump(netflix_records, f, indent=2)

print("✅ Cleaned data from IMDb and Netflix has been cached.")


# ----------------------------
# Graph Construction
# ----------------------------

# Load cleaned data from cache
with open('cache/imdb_cache.json', 'r') as f:
    imdb_data = json.load(f)

with open('cache/netflix_cache.json', 'r') as f:
    netflix_data = json.load(f)

# Create an empty graph
G = nx.Graph()

# Helper to create a unique node name
def get_node_key(item):
    return f"{item['title'].strip()} ({item['release_year']})"

# Add IMDb nodes
for item in imdb_data:
    key = get_node_key(item)
    G.add_node(key, source='IMDb', genres=item['genres'], director=item['director'], cast=item['cast'])

# Add Netflix nodes
for item in netflix_data:
    key = get_node_key(item)
    G.add_node(key, source='Netflix', genres=item['genres'], director=item['director'], cast=item['cast'])

# Create edges based on shared director or shared cast
nodes = list(G.nodes(data=True))
for i in range(len(nodes)):
    for j in range(i+1, len(nodes)):
        key1, data1 = nodes[i]
        key2, data2 = nodes[j]

        if key1 == key2:
            continue

        # Check shared director
        if data1['director'] and data1['director'] == data2['director']:
            G.add_edge(key1, key2, reason='director')

        # Check shared cast (at least one actor in common)
        shared_cast = set(data1['cast']) & set(data2['cast'])
        if shared_cast:
            G.add_edge(key1, key2, reason='actor', shared_cast=list(shared_cast))

print("✅ Graph built successfully.")
print(f"Total nodes: {G.number_of_nodes()}")
print(f"Total edges: {G.number_of_edges()}")


# ----------------------------
# CLI Interface Starts Here
# ----------------------------

# Load graph from previous step
def load_graph():
    with open('cache/imdb_cache.json') as f:
        imdb_data = json.load(f)
    with open('cache/netflix_cache.json') as f:
        netflix_data = json.load(f)

    G = nx.Graph()
    
    def get_node_key(item):
        return f"{item['title'].strip()} ({item['release_year']})"

    # Add IMDb nodes
    for item in imdb_data:
        key = get_node_key(item)
        G.add_node(key, source='IMDb', genres=item['genres'], director=item['director'], cast=item['cast'])

    # Add Netflix nodes
    for item in netflix_data:
        key = get_node_key(item)
        G.add_node(key, source='Netflix', genres=item['genres'], director=item['director'], cast=item['cast'])

    # Add edges
    nodes = list(G.nodes(data=True))
    for i in range(len(nodes)):
        for j in range(i+1, len(nodes)):
            key1, data1 = nodes[i]
            key2, data2 = nodes[j]

            if key1 == key2:
                continue

            if data1['director'] and data1['director'] == data2['director']:
                G.add_edge(key1, key2, reason='director')

            shared_cast = set(data1['cast']) & set(data2['cast'])
            if shared_cast:
                G.add_edge(key1, key2, reason='actor', shared_cast=list(shared_cast))

    return G

# CLI Feature 1: Find shortest path
def find_shortest_path(G):
    start = input("Enter the first title: ").strip()
    end = input("Enter the second title: ").strip()

    try:
        path = nx.shortest_path(G, source=start, target=end)
        print("\nShortest path:")
        for i, node in enumerate(path):
            print(f"{i+1}. {node}")
    except nx.NetworkXNoPath:
        print("No path found between those titles.")
    except nx.NodeNotFound:
        print("One or both titles not found. Check the format (e.g. 'The Godfather (1972)').")

# CLI Feature 2: Recommend similar titles
def recommend_similar(G):
    title = input("Enter a title: ").strip()
    if title in G:
        neighbors = list(G.neighbors(title))
        if neighbors:
            print(f"\nTitles connected to {title}:")
            for t in neighbors:
                print(f"- {t}")
        else:
            print("No direct connections found.")
    else:
        print("Title not found.")

# CLI Feature 3: List IMDb titles available on Netflix
def list_imdb_on_netflix(G):
    print("\nIMDb Top Rated Titles on Netflix:")
    for node, data in G.nodes(data=True):
        if data.get('source') == 'IMDb':
            # Check if there's a node with same title and year in Netflix
            for neighbor in G.neighbors(node):
                if G.nodes[neighbor].get('source') == 'Netflix':
                    print(f"- {node}")
                    break

# CLI Feature 4: Show most connected titles in the graph
def most_connected_titles(G, top_n=10):
    print(f"\nTop {top_n} Most Connected Titles:")
    degrees = sorted(G.degree, key=lambda x: x[1], reverse=True)[:top_n]
    for title, degree in degrees:
        print(f"{title} — {degree} connections")

# CLI Main Menu
def main():
    G = load_graph()
    print("🎬 Movie Graph Explorer 🎬")

    while True:
        print("\nOptions:")
        print("1. Find shortest path between two titles")
        print("2. Recommend similar titles")
        print("3. List IMDb Top Movies on Netflix")
        print("4. Show most connected titles")
        print("5. Exit")

        choice = input("Choose an option (1–5): ").strip()

        if choice == '1':
            find_shortest_path(G)
        elif choice == '2':
            recommend_similar(G)
        elif choice == '3':
            list_imdb_on_netflix(G)
        elif choice == '4':
            most_connected_titles(G)
        elif choice == '5':
            print("Goodbye 👋")
            break
        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    main()
