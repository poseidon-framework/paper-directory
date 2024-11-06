from flask import Flask, render_template_string, request
import requests

app = Flask(__name__)

# Function to get metadata using CrossRef API
def get_paper_title(doi):
    url = f"https://api.crossref.org/works/{doi}"
    response = requests.get(url)
    if response.status_code == 200:
        metadata = response.json()
        return metadata['message']['title'][0]  # Extracting the paper title
    return None

# Function to fetch package info from Poseidon API
def fetch_poseidon_packages(archive_name):
    url = f"https://server.poseidon-adna.org/packages?archive={archive_name}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("serverResponse", {}).get("packageInfo", [])
    return []

# Parse the package description
def clean_description(description):
    return description.split('.')[0] + '.'  # Remove the part after the first full stop

# Check if a paper title is in the archive
def check_paper_in_archive(paper_title, package_info_list):
    for package in package_info_list:
        cleaned_description = clean_description(package['description'])
        if paper_title.lower() in cleaned_description.lower():
            return True  # Paper title matches the cleaned description
    return False

# Preprocess DOIs to ensure they are in the correct format
def preprocess_doi(doi):
    return doi.replace("https://doi.org/", "").strip()

# Main route for displaying and processing the form
@app.route('/', methods=['GET', 'POST'])
def index():
    result = []
    if request.method == 'POST':
        # Get DOIs from the form and preprocess them
        raw_dois = request.form['dois']
        dois = [preprocess_doi(doi) for doi in raw_dois.split(',')]
        
        # Archive names
        archives = {
            'community': 'community-archive',
            'minotaur': 'minotaur-archive',
            'aadr': 'aadr-archive'
        }
        
        # Fetch package info for all archives
        package_info_by_archive = {
            archive: fetch_poseidon_packages(archives[archive])
            for archive in archives
        }
        
        # Process each DOI
        for doi in dois:
            paper_title = get_paper_title(doi)
            if paper_title:
                paper = {
                    'doi': doi,
                    'title': paper_title,
                    'community_archive': check_paper_in_archive(paper_title, package_info_by_archive['community']),
                    'aadr_archive': check_paper_in_archive(paper_title, package_info_by_archive['aadr']),
                    'minotaur_archive': check_paper_in_archive(paper_title, package_info_by_archive['minotaur'])
                }
                result.append(paper)
    
    # HTML template for rendering the form and results
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Paper Directory Check</title>
        <style>
            table { width: 100%; border-collapse: collapse; }
            th, td { padding: 8px; border: 1px solid #ddd; text-align: left; }
            th { background-color: #f2f2f2; }
        </style>
    </head>
    <body>
        <h1>Paper Directory Check</h1>
        <form method="POST">
            <label for="dois">Enter DOIs (comma-separated):</label><br>
            <input type="text" id="dois" name="dois" style="width: 100%; padding: 8px;"><br><br>
            <button type="submit">Check</button>
        </form>

        {% if result %}
        <h2>Results:</h2>
        <table>
            <tr>
                <th>DOI</th>
                <th>Title</th>
                <th>Community Archive</th>
                <th>AADR Archive</th>
                <th>Minotaur Archive</th>
            </tr>
            {% for paper in result %}
            <tr>
                <td>{{ paper.doi }}</td>
                <td>{{ paper.title }}</td>
                <td>{{ '✔' if paper.community_archive else '✘' }}</td>
                <td>{{ '✔' if paper.aadr_archive else '✘' }}</td>
                <td>{{ '✔' if paper.minotaur_archive else '✘' }}</td>
            </tr>
            {% endfor %}
        </table>
        {% endif %}
    </body>
    </html>
    """
    return render_template_string(html_template, result=result)

if __name__ == '__main__':
    app.run(debug=True)

