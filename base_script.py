import json
import requests
import sys
from datetime import datetime
import os
import requests
from jinja2 import Template
from collections import defaultdict
from datetime import datetime

def load_supplementary_metadata():
    """Loads supplementary metadata from supplementary.json."""
    supplementary_file = "supplementary.json"
    if os.path.exists(supplementary_file):
        try:
            with open(supplementary_file, "r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError:
            sys.stderr.write("ERROR: Failed to parse supplementary.json. Using default values.\n")
            return {}
    return {}

SUPPLEMENTARY_METADATA = load_supplementary_metadata()

def get_crossref_metadata(doi, index, total):
    print(f"({index + 1} / {total}) Gathering metadata for {doi}")

    #Initialize with supplementary.json 
    metadata = SUPPLEMENTARY_METADATA.get(doi, {})
    metadata = {
        "title": metadata.get("title"),
        "year": metadata.get("year"),
        "journal": metadata.get("journal"),
        "date": metadata.get("date"),
        "first_author": metadata.get("first author"),
        "doi_link": f"https://doi.org/{doi}",
    }

    #Query CrossRef to fill missing values
    url = f"https://api.crossref.org/works/{doi}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json().get("message", {})

        if metadata["title"] is None:
            metadata["title"] = data.get("title", [None])[0]

        if metadata["year"] is None:
            year_data = data.get("published-print", data.get("published-online", {})).get("date-parts", [[None]])
            metadata["year"] = year_data[0][0] if isinstance(year_data[0][0], int) else None

        if metadata["journal"] is None:
           container_titles = data.get("container-title", [])
           metadata["journal"] = container_titles[0] if container_titles else None

        if metadata["date"] is None:
            raw_date = data.get("created", {}).get("date-time", None)
            if raw_date:
                try:
                    metadata["date"] = datetime.strptime(raw_date, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")
                except ValueError:
                    pass

        if metadata["first_author"] is None:
            first_author_field = data.get("author", [{}])[0]
            first = first_author_field.get("given") or ""
            last = first_author_field.get("family") or ""
            metadata["first_author"] = first + " " + last

    else:
        sys.stderr.write(f"WARNING: CrossRef failed to fetch metadata for {doi}\n")

    #Fallback defaults
    metadata = {k: (v if v else get_default_value(k)) for k, v in metadata.items()}

    return metadata

def get_default_value(field):
    """Returns default values for missing metadata fields."""
    defaults = {
        "title": "No Title Available",
        "year": 0,
        "journal": "No Journal",
        "date": "0000-00-00",
        "first_author": "N/A",
    }
    return defaults.get(field, "N/A")

# Fetch bibliography from Poseidon 
def fetch_poseidon_bibliography(archive_name):
    print(f"Fetching DOI data from {archive_name}...")
    url = f"http://server.poseidon-adna.org:3000/bibliography?archive={archive_name}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("serverResponse", {}).get("bibEntries", [])
    return []

# Load all Poseidon bibliography data into a dictionary 
def load_poseidon_doi_map():
    archives = ["community-archive", "minotaur-archive", "aadr-archive"]
    poseidon_doi_map = defaultdict(set)
    for archive in archives:
        entries = fetch_poseidon_bibliography(archive)
        for entry in entries:
            doi = entry.get("bibDoi")
            if doi:
                poseidon_doi_map[doi.lower()].add(archive)
    return poseidon_doi_map

# Preprocess DOIs
def preprocess_doi(doi):
    return doi.replace("https://doi.org/", "").strip().lower()

# Check for duplicate DOIs 
def check_for_duplicates(dois):
    seen = set()
    unique_dois = []
    duplicates = []

    for doi in dois:
        if doi in seen:
            duplicates.append(doi)  # Store duplicate for logging
        else:
            seen.add(doi)
            unique_dois.append(doi)  # Keep only unique DOIs

    if duplicates:
        print("\n WARNING: Duplicate DOIs found and removed:")
        for duplicate in duplicates:
            print(f"- {duplicate}")
        print("\nProceeding with a cleaned DOI list.\n")

    return unique_dois  # Return unique dois

# Generate docs/index.html
def generate_html(papers, output_file="docs/index.html"):
    print("Updating docs/index.html...")
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
            select, input { margin: 5px; padding: 5px; }
        </style>
        <script>
            function filterTable() {
                let input = document.getElementById("searchInput").value.toLowerCase();
                let communityFilter = document.getElementById("communityFilter").value;
                let aadrFilter = document.getElementById("aadrFilter").value;
                let minotaurFilter = document.getElementById("minotaurFilter").value;

                let table = document.getElementById("paperTable");
                let rows = table.getElementsByTagName("tr");

                let nrRows = 0;
                for (let i = 1; i < rows.length; i++) {
                    let titleCell = rows[i].getElementsByTagName("td")[1]; // Title column
                    let authorCell = rows[i].getElementsByTagName("td")[4]; // Author column
                    let communityCell = rows[i].getElementsByTagName("td")[6]; // Community Archive column
                    let aadrCell = rows[i].getElementsByTagName("td")[7]; // AADR Archive column
                    let minotaurCell = rows[i].getElementsByTagName("td")[8]; // Minotaur Archive column

                    if (titleCell && authorCell && communityCell && aadrCell && minotaurCell) {
                        let titleText = titleCell.textContent.toLowerCase();
                        let authorText = authorCell.textContent.toLowerCase();
                        let communityText = communityCell.textContent.trim();
                        let aadrText = aadrCell.textContent.trim();
                        let minotaurText = minotaurCell.textContent.trim();

                        // Apply search filter (title or author must match)
                        let matchesSearch = titleText.includes(input) || authorText.includes(input);

                        // Apply archive filters using logical AND
                        let matchesFilters =
                            (communityFilter === "all" || (communityFilter === "✔" && communityText === "✔") || (communityFilter === "✘" && communityText === "✘")) &&
                            (aadrFilter === "all" || (aadrFilter === "✔" && aadrText === "✔") || (aadrFilter === "✘" && aadrText === "✘")) &&
                            (minotaurFilter === "all" || (minotaurFilter === "✔" && minotaurText === "✔") || (minotaurFilter === "✘" && minotaurText === "✘"));

                        // Show or hide row based on both search and filter conditions
                        rows[i].style.display = (matchesSearch && matchesFilters) ? "" : "none";
                        nrRows += matchesSearch && matchesFilters;
                    }
                    let nrRowsSpan = document.getElementById("nrRows");
                    nrRowsSpan.innerText = nrRows;
                }
            }

            function resetFilters() {
                document.getElementById('searchInput').value = "";
                document.getElementById('communityFilter').value = 'all';
                document.getElementById('aadrFilter').value = 'all';
                document.getElementById('minotaurFilter').value = 'all';
                filterTable();
            }

            window.addEventListener('load', function() {
                resetFilters();
            });

        </script>
    </head>
    <body>
        <h1>Paper Directory</h1>
        <p>A list of ancient DNA papers, and their availability in Poseidon and AADR archives. Please see <a href="https://github.com/poseidon-framework/paper-directory">our README on github for instructions how to add to this list.</a></p>
        
        <div>
            <label for="searchInput">Search Title or Author:</label>
            <input type="text" id="searchInput" onkeyup="filterTable()" placeholder="Type to search...">
            
            <label for="communityFilter">Community Archive:</label>
            <select id="communityFilter" onchange="filterTable()">
                <option value="all">All</option>
                <option value="✔">✔</option>
                <option value="✘">✘</option>
            </select>
            <label for="aadrFilter">AADR Archive:</label>
            <select id="aadrFilter" onchange="filterTable()">
                <option value="all">All</option>
                <option value="✔">✔</option>
                <option value="✘">✘</option>
            </select>
            <label for="minotaurFilter">Minotaur Archive:</label>
            <select id="minotaurFilter" onchange="filterTable()">
                <option value="all">All</option>
                <option value="✔">✔</option>
                <option value="✘">✘</option>
            </select>
            <button onclick="resetFilters()">Reset Filters</button>
        </div>

        <p><span id="nrRows">?</span> papers selected</p>

        <table id="paperTable">
            <tr>
                <th>DOI</th>
                <th>Title</th>
                <th>Year</th>
                <th>Journal</th>
                <th>First Author</th>
                <th>Publication Date</th>
                <th>Community Archive</th>
                <th>AADR Archive</th>
                <th>Minotaur Archive</th>
            </tr>
            {% for paper in papers %}
            <tr>
                <td><a href="{{ paper.doi_link }}" target="_blank">{{ paper.doi }}</a></td>
                <td>{{ paper.title }}</td>
                <td>{{ paper.year }}</td>
                <td>{{ paper.journal }}</td>
                <td>{{ paper.first_author }}</td>
                <td>{{ paper.date }}</td>
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
    with open(output_file, "w") as file:
        file.write(rendered_html)
    print("docs/index.html successfully updated!")

# Main Execution 
dois = [preprocess_doi(doi) for doi in open("list.txt").read().splitlines()]

print(f"Processing {len(dois)} DOIs...")

# Check for duplicates and get a unique list
dois = check_for_duplicates(dois)

# Get CrossRef metadata
metadata_map = {doi: get_crossref_metadata(doi, index, len(dois)) for index, doi in enumerate(dois)}

# Get Poseidon DOI availability
poseidon_doi_map = load_poseidon_doi_map()

# Create structured paper data
papers = [{"doi": doi, **metadata_map[doi], "archives": poseidon_doi_map.get(doi, set())} for doi in dois]

# Sort papers by publication date (YYYY-MM-DD)
papers.sort(key=lambda x: x["date"], reverse=True)

# Generate HTML report
generate_html(papers)

