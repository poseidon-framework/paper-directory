# This script reads the current list and outputs a new list to standard out with duplicates removed. It doesn't change the order

dois = []
for doi in open("../list.txt"):
    if doi not in dois:
        dois.append(doi)
        print(doi, end="")
