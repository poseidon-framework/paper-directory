import requests
from jinja2 import Template

# get metadata using CrossRef API
def get_paper_title(doi):
    url = f"https://api.crossref.org/works/{doi}"
    response = requests.get(url)
    if response.status_code == 200:
        metadata = response.json()
        return metadata['message']['title'][0]  # Extracting the paper title
    return None

# fetch package info from Poseidon API
def fetch_poseidon_packages(archive_name):
    url = f"https://server.poseidon-adna.org/packages?archive={archive_name}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("serverResponse", {}).get("packageInfo", [])
    return []

# parse the package description
def clean_description(description):
    return description.split('.')[0] + '.'  # Remove the part after the first full stop

# check if a title description
def check_paper_in_archive(paper_title, package_info_list):
    for package in package_info_list:
        cleaned_description = clean_description(package['description'])
        if paper_title.lower() in cleaned_description.lower():
            return True  # Paper title matches the cleaned description
    return False

# Preprocess DOIs 
def preprocess_doi(doi):
    # Remove 'https://doi.org/' prefix
    return doi.replace("https://doi.org/", "").strip()

# generate HTML from inline template
def generate_html(papers, output_file='index.html'):
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Paper Directory</title>
        <style>
            table { width: 100%; border-collapse: collapse; }
            th, td { padding: 8px; border: 1px solid #ddd; text-align: left; }
            th { background-color: #f2f2f2; }
        </style>
    </head>
    <body>
        <h1>Paper Directory</h1>
        <table>
            <tr>
                <th>DOI</th>
                <th>Title</th>
                <th>Community Archive</th>
                <th>AADR Archive</th>
                <th>Minotaur Archive</th>
            </tr>
            {% for paper in papers %}
            <tr>
                <td>{{ paper.doi }}</td>
                <td>{{ paper.title }}</td>
                <td>{{ '✔' if paper.community_archive else '✘' }}</td>
                <td>{{ '✔' if paper.aadr_archive else '✘' }}</td>
                <td>{{ '✔' if paper.minotaur_archive else '✘' }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """
    
    template = Template(html_template)
    rendered_html = template.render(papers=papers)
    with open(output_file, 'w') as file:
        file.write(rendered_html)

# Processing DOIs
dois = [preprocess_doi(doi) for doi in open('list.txt').read().splitlines()]
papers = []

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

# Processing DOIs and check if they are in archives
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
        papers.append(paper)

# Sorting papers by title 
papers.sort(key=lambda x: x['title'])

# Generate the HTML table
generate_html(papers)

