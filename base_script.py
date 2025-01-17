import requests
from jinja2 import Template
from collections import defaultdict

# Fetch bibliography info from archives
def fetch_poseidon_bibliography(archive_name):
    url = f"http://server.poseidon-adna.org:3000/bibliography?archive={archive_name}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("serverResponse", {}).get("bibEntries", [])
    return []

# Load all bibliographies into a single structure
def load_all_bibliographies():
    archives = ["community-archive", "minotaur-archive", "aadr-archive"]
    archive_doi_map = defaultdict(dict)  # Map DOI to archive set and title
    for archive in archives:
        entries = fetch_poseidon_bibliography(archive)
        for entry in entries:
            doi = entry.get("bibDoi")
            title = entry.get("bibTitle", "No Title Available")
            if doi:  # Ignore entries without DOIs
                if doi.lower() not in archive_doi_map:
                    archive_doi_map[doi.lower()] = {'archives': set(), 'title': title}
                archive_doi_map[doi.lower()]['archives'].add(archive)
    return archive_doi_map

# Preprocess DOIs
def preprocess_doi(doi):
    return doi.replace("https://doi.org/", "").strip().lower()

# Generate HTML into an inline template
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
            select { margin: 5px; }
        </style>
        <script>
            function filterColumn(columnIndex, filterValue) {
                const table = document.getElementById('paperTable');
                const rows = table.getElementsByTagName('tr');
                for (let i = 1; i < rows.length; i++) {
                    const cell = rows[i].getElementsByTagName('td')[columnIndex];
                    if (cell) {
                        const cellText = cell.textContent.trim();
                        rows[i].style.display = (filterValue === 'all' || cellText === filterValue) ? '' : 'none';
                    }
                }
            }
            function resetFilters() {
                const rows = document.getElementById('paperTable').getElementsByTagName('tr');
                for (let i = 1; i < rows.length; i++) {
                    rows[i].style.display = '';
                }
            }
        </script>
    </head>
    <body>
        <h1>Paper Directory</h1>
        <div>
            <label for="communityFilter">Community Archive:</label>
            <select id="communityFilter" onchange="filterColumn(2, this.value)">
                <option value="all">All</option>
                <option value="✔">✔</option>
                <option value="✘">✘</option>
            </select>
            <label for="aadrFilter">AADR Archive:</label>
            <select id="aadrFilter" onchange="filterColumn(3, this.value)">
                <option value="all">All</option>
                <option value="✔">✔</option>
                <option value="✘">✘</option>
            </select>
            <label for="minotaurFilter">Minotaur Archive:</label>
            <select id="minotaurFilter" onchange="filterColumn(4, this.value)">
                <option value="all">All</option>
                <option value="✔">✔</option>
                <option value="✘">✘</option>
            </select>
            <button onclick="resetFilters()">Reset Filters</button>
        </div>
        <table id="paperTable">
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
                <td>{{ '✔' if 'community-archive' in paper.archives else '✘' }}</td>
                <td>{{ '✔' if 'aadr-archive' in paper.archives else '✘' }}</td>
                <td>{{ '✔' if 'minotaur-archive' in paper.archives else '✘' }}</td>
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

# Process input DOIs
dois = [preprocess_doi(doi) for doi in open('list.txt').read().splitlines()]

# Load all bibliography data
archive_doi_map = load_all_bibliographies()

# Check each DOIs
papers = []
for doi in dois:
    data = archive_doi_map.get(doi, {'archives': set(), 'title': 'No Title Available'})
    paper = {
        'doi': doi,
        'title': data['title'],
        'archives': data['archives']
    }
    papers.append(paper)

# Sort papers by DOI
papers.sort(key=lambda x: x['doi'])

# Generate the HTML table
generate_html(papers)

