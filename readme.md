

## 💡 What does this script do?
This script reads a list of DOIs from `list.txt`, fetches metadata from **CrossRef API**, and checks if those papers exist in **Poseidon Archives** (`community-archive`, `aadr-archive`, `minotaur-archive`). It then generates an **HTML table (`index.html`)** displaying:

✔ Paper title  
✔ Publication year & exact date  
✔ First author’s name  
✔ Journal name  
✔ Availability in Poseidon archives (✔ or ✘)  
✔ A **search bar** for filtering by title  
✔ **Dropdown filters** for the archives  

Every time `list.txt` is updated and a commit is pushed, this script runs and updates `index.html` on GitHub Pages.

---

## ⚙️ Technical Requirements
- **Python Version:** Python 3.x  
- **Required Libraries:**  
  ```bash
  pip install requests Jinja2
  ```
- **Files:**  
  - `list.txt` → List of DOIs (one per line)  
  - `base_script.py` → The main script  
  - `index.html` → The generated output file  

---

## 🔍 How the Functions Work

### 1️⃣ `get_crossref_metadata(doi, index, total)`
Fetches metadata from CrossRef API.  
Extracts **title, year, journal, date, first author’s name**.  
Formats publication date into **YYYY-MM-DD**.  
Prints **progress updates** like:  
   ```
   (1 / 100) Querying metadata for 10.1002/ajpa.23312
   ```
   
### 2️⃣ `fetch_poseidon_bibliography(archive_name)`
Calls Poseidon API to check available DOIs for a given archive.  
Extracts **DOI list** from `community-archive`, `aadr-archive`, and `minotaur-archive`.  
Prints **status messages** while fetching:  
   ```
   Fetching DOI data from community-archive...
   ```

### 3️⃣ `load_poseidon_doi_map()`
Collects all available DOIs from **all Poseidon archives**.  
Stores data in a dictionary mapping **DOIs → available archives**.

### 4️⃣ `preprocess_doi(doi)`
Cleans up DOI format by removing extra spaces & "https://doi.org/".

### 5️⃣ `check_for_duplicates(dois)`
Checks `list.txt` for duplicate DOIs.  
If duplicates are found, it **prints a warning**:  
   ```
   WARNING: Duplicate DOIs found:
   - 10.1002/ajpa.23312
   ```

### 6️⃣ `generate_html(papers, output_file)`
Creates **index.html** using a **Jinja2 template**.  
Adds search bar to filter by **title**.  
Adds dropdown filters to show/hide papers based on Poseidon archive availability.  
Formats clickable DOI links like this:  
   ```
   <a href="https://doi.org/10.1002/ajpa.23312">10.1002/ajpa.23312</a>
   ```
Prints progress while updating:  
   ```
   Updating index.html...
   index.html successfully updated!
   ```

---

## 🚀 How to Run the Script
1. Add **DOIs** to `list.txt` (one per line).  
2. Run the script:  
   ```bash
   python base_script.py
   ```
3. Open `index.html` to see the results!  

---

This is a **fully automated workflow** that updates the table and deploys it to **GitHub Pages** whenever `input.txt` changes.

**GitHub Actions Workflow** runs everything behind the scenes. No manual updates needed!


## Testing locally

To run the script locally, you can try `python3 base_script.py`. Likely you will be required to first install libraries `requests` and `jinja2`. You can do that by creating a virtual environment, for example:

```{bash}
python3 -m venv ~/venv/paper-directory
source ~/venvs/paper-directory/bin/activate
python3 -m pip install requests
python3 -m pip install jinja2
```

Then `python3 base_script.py` should generate the page.

You can then run a test server:

`python3 -m http.server --directory docs 8000`

and open `http://localhost:8000` in your browser.
