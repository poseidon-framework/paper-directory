library(magrittr)
library(ggplot2)

#### read data ####

paper_directory_raw <- readr::read_csv("~/agora/paper-directory/docs/paper_directory.csv")

# fix one entry where the PCA is missing a correct DOI entry
# can be removed eventually
paper_directory_raw$community_archive[paper_directory_raw$doi == "10.1038/s41586-024-08418-5"] <- TRUE

paper_directory <- paper_directory_raw %>%
  dplyr::filter(nr_adna_samples > 0) %>%
  dplyr::mutate(
    type = dplyr::case_when(
      # (community_archive | minotaur_archive) & aadr_archive ~ "all",
      (community_archive | minotaur_archive) ~ "PCA or PMA",
      aadr_archive ~ "PAA",
      .default = "none"
    ) %>%
      factor(levels = c("PCA or PMA", "PAA", "none"))
  ) %>%
  dplyr::arrange(type) %>%
  dplyr::mutate(
    id = 1:dplyr::n() # after arrange step
  )

#### barplot ####

p_bar <- paper_directory %>%
  dplyr::group_by(year) %>%
  dplyr::summarise(n = sum(nr_adna_samples)) %>%
  ggplot() +
  geom_col(aes(x = year, y = n)) +
  geom_text(
    aes(
      x = year, y = n,
      label = dplyr::case_when(
        n < 10 ~ as.character(n),
        #n >= 10 ~ paste0("≈", round(n, -1)))
        n >= 10 ~ paste0(round(n, -1))
      )
    ),
    vjust = -0.25, size = 3
  ) +
  scale_x_continuous(breaks = 2010:2025) +
  theme_bw() +
  theme(axis.title.x = element_blank()) +
  ylab("# of published ancient individuals")

ggsave(
  "barplot.png",
  plot = p_bar,
  device = "png",
  scale = 0.4,
  dpi = 300,
  width = 500, height = 220, units = "mm",
  limitsize = F,
  bg = "white"
)

#### packed-circles plot ####

# arrange papers on grid to release pressure from circleRepelLayout below
grid_pos <- ggpointgrid::arrange_points_on_grid(
  grid_xy = expand.grid(
    x = seq(
      min(as.double(paper_directory$publication_date)),
      max(as.double(paper_directory$publication_date)),
      by = 100
    ),
    y = seq(-1000,1000,50)
  ) %>% as.matrix,
  pts_xy = paper_directory %>%
    dplyr::transmute(
      x = as.double(publication_date),
      y = 0
    ) %>% as.matrix()
)

# plot(grid_pos[,1],grid_pos[,2])

# create and arrange circles
xyz <- tibble::tibble(
    x = as.double(paper_directory$publication_date), # grid_pos[,1],
    y = grid_pos[,2],
    n = paper_directory$nr_adna_samples * 350
  )
center_and_radius <- packcircles::circleRepelLayout(
  xyz,
  xlim = c(min(xyz$x), max(xyz$x) + 120),
  wrap = FALSE
)$layout
polygons <- packcircles::circleLayoutVertices(center_and_radius)

# assemble plot
p_no_legend <- ggplot() +
  geom_polygon(
    data = paper_directory %>% dplyr::left_join(polygons, by = "id"),
    mapping = aes(as.Date(x), y, group = id),
    linewidth = 0.4, fill = "#D3D4D8"
  ) +
  geom_text(
    data = paper_directory %>% dplyr::bind_cols(
      center_and_radius %>% dplyr::transmute(x_center = x, y_center = y)
    ) %>% dplyr::filter(nr_adna_samples > 150),
    mapping = aes(
      x = as.Date(x_center),
      y = y_center,
      label = paste(
        stringr::str_extract(first_author, "\\s([-\\w]+)$") %>%
          stringr::str_replace_all("-", "-\n"),
        year,
        sep = "\n"
      )
    ),
    colour="black", size = 1.9
  ) +
  coord_fixed() +
  theme_bw() +
  scale_x_date(
    breaks = seq.Date(lubridate::ymd("2010-01-01"), lubridate::ymd("2025-12-31"), by = "year"),
    date_labels = "%Y"
  ) +
  theme(
    panel.grid = element_blank(),
    panel.grid.major.x = element_line(colour = "black", linetype = "dashed", linewidth = 0.1),
    panel.border = element_blank(),
    axis.line.x = element_line(),
    axis.title = element_blank(),
    axis.text.y = element_blank(),
    axis.ticks.y = element_blank()
  )

ggsave(
  "no_legend.png",
  plot = p_no_legend,
  device = "png",
  scale = 1.7,
  dpi = 300,
  width = 1400, height = 730, units = "px",
  limitsize = F,
  bg = "white"
)

p <- ggplot() +
  geom_polygon(
    data = paper_directory %>% dplyr::left_join(polygons, by = "id"),
    mapping = aes(as.Date(x), y, group = id, fill = type),
    linewidth = 0.4
  ) +
  scale_fill_manual(
    values = c(
      #"PCA or PMA" = "#5785C1",
      "PCA or PMA" = "#00b2ff",
      "PAA" = "#ffa800",
      "none" = "#D3D4D8"
    )
  ) +
  guides(fill = guide_legend(title = "in Archives")) +
  geom_text(
    data = paper_directory %>% dplyr::bind_cols(
        center_and_radius %>% dplyr::transmute(x_center = x, y_center = y)
      ) %>% dplyr::filter(nr_adna_samples > 150),
    mapping = aes(
      x = as.Date(x_center),
      y = y_center,
      label = paste(
        stringr::str_extract(first_author, "\\s([-\\w]+)$") %>%
          stringr::str_replace_all("-", "-\n"),
        year,
        sep = "\n"
      )
    ),
    colour="black", size = 1.9
  ) +
  coord_fixed() +
  theme_bw() +
  scale_x_date(
    #date_breaks = "1 year",
    breaks = seq.Date(lubridate::ymd("2010-01-01"), lubridate::ymd("2025-12-31"), by = "year"),
    date_labels = "%Y"
  ) +
  theme(
    panel.grid = element_blank(),
    panel.grid.major.x = element_line(colour = "black", linetype = "dashed", linewidth = 0.1),
    panel.border = element_blank(),
    axis.line.x = element_line(),
    axis.title = element_blank(),
    axis.text.y = element_blank(),
    axis.ticks.y = element_blank(),
    legend.position = c(0.1, 0.2),
    legend.box.background = element_rect(colour = "black")
  )

ggsave(
    "test.png",
    plot = p,
    device = "png",
    scale = 1.7,
    dpi = 300,
    width = 1400, height = 730, units = "px",
    limitsize = F,
    bg = "white"
)

