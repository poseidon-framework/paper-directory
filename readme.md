## What does this script do?
This script reads a list of DOIs from `list.csv`, fetches metadata from **CrossRef API**, and checks if those papers exist in **Poseidon Archives** (`community-archive`, `aadr-archive`, `minotaur-archive`). It then generates an **HTML table (`index.html`)**.

Every time `list.csv` is updated and a commit is pushed, this script runs and updates `index.html` on GitHub Pages.

---

## Technical Requirements
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
