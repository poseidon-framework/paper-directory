library(magrittr)

# read janno file
pca_raw <- janno::read_janno("~/agora/community-archive", validate = F)
pma_raw <- janno::read_janno("~/agora/minotaur-archive", validate = F)
paa_raw <- janno::read_janno("~/agora/aadr-archive", validate = F) %>%
  dplyr::filter(grepl("v62", source_file))

# read dois from bibtex
pca_bibkey_doi_raw <- purrr::map_dfr(list.files(
  "~/agora/community-archive", pattern = "\\.bib$",
  full.names = T, recursive = T),
  function(bib_path) { bib2df::bib2df(bib_path) %>% dplyr::select(BIBTEXKEY, DOI) })
pma_bibkey_doi_raw <- purrr::map_dfr(list.files(
  "~/agora/minotaur-archive", pattern = "\\.bib$",
  full.names = T, recursive = T),
  function(bib_path) { bib2df::bib2df(bib_path) %>% dplyr::select(BIBTEXKEY, DOI) })
paa_bibkey_doi_raw <- purrr::map_dfr(list.files(
  "~/agora/aadr-archive", pattern = "\\.bib$",
  full.names = T, recursive = T),
  function(bib_path) { bib2df::bib2df(bib_path) %>% dplyr::select(BIBTEXKEY, DOI) })

# create a lookup tables for bibkeys to dois
clean_bibkey_doi_table <- function(x) {
  x %>%
    dplyr::transmute(
      bibkey = BIBTEXKEY,
      doi = DOI %>% tolower %>% gsub("https://doi.org/", "", .)
    ) %>%
    dplyr::filter(doi != "") %>%
    dplyr::distinct()
}

pca_bibkey_doi <- pca_bibkey_doi_raw %>% create_bibkey_doi_table
pma_bibkey_doi <- pma_bibkey_doi_raw %>% create_bibkey_doi_table
paa_bibkey_doi <- paa_bibkey_doi_raw %>% create_bibkey_doi_table

paa_bibkey_doi_corrected <- paa_bibkey_doi %>%
  dplyr::filter(!(bibkey == "SkoglundNature2016" & doi == "10.1016/j.cub.2018.02.051"))

# get nr of aDNA samples per DOI
get_samples_per_doi <- function(x, bibkey_doi_table) {
  x %>%
    dplyr::filter(Date_Type != "modern") %>%
    dplyr::mutate(bibkey = purrr::map_chr(Publication, \(x) x[[1]])) %>%
    dplyr::left_join(bibkey_doi_table, by = "bibkey") %>%
    dplyr::group_by(doi) %>%
    dplyr::summarise(n = dplyr::n()) %>%
    dplyr::filter(!is.na(doi))
}

pca_samples_per_doi <- get_samples_per_doi(pca_raw, pca_bibkey_doi) %>%
  dplyr::rename(nPCA = n)
pma_samples_per_doi <- get_samples_per_doi(pma_raw, pma_bibkey_doi) %>%
  dplyr::rename(nPMA = n)
paa_samples_per_doi <- get_samples_per_doi(paa_raw, paa_bibkey_doi_corrected) %>%
  dplyr::rename(nPAA = n)

# compare across archives
# pma is so small, it can be ignored here
dplyr::full_join(
  pca_samples_per_doi,
  paa_samples_per_doi,
  by = "doi" 
) %>% View()

# combine information
samples_per_doi <- dplyr::full_join(
  pca_samples_per_doi,
  paa_samples_per_doi,
  by = "doi" 
) %>%
  dplyr::transmute(
    doi,
    # give preference to PCA, only use PAA when PCA doesn't have a paper
    n = dplyr::case_when(
      is.na(nPCA) ~ nPAA,
      .default = nPCA
    )
  )

# update list.csv
empty_list <- readr::read_csv("~/agora/paper-directory/list.csv")

filled_list <- empty_list %>%
  dplyr::mutate(doi_low = tolower(doi)) %>%
  dplyr::left_join(
    samples_per_doi, by = c("doi_low" = "doi")
  ) %>%
  dplyr::transmute(
    doi,
    nr_adna_samples = n
  )

readr::write_csv(filled_list, file = "~/agora/paper-directory/list.csv")

