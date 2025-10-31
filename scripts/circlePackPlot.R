library(magrittr)
library(ggplot2)

#### read data ####

paper_directory_raw <- readr::read_csv("~/agora/paper-directory/docs/paper_directory.csv")

paper_directory <- paper_directory_raw %>%
  dplyr::filter(nr_adna_samples > 0) %>%
  dplyr::mutate(
    type = dplyr::case_when(
      (community_archive | minotaur_archive) & aadr_archive ~ "all",
      (community_archive | minotaur_archive) ~ "PCA or PMA",
      aadr_archive ~ "PAA",
      .default = "none"
    )
  ) %>%
  dplyr::arrange(type) %>%
  dplyr::mutate(
    id = 1:dplyr::n() # after arrange step
  )

#### barplot ####

paper_directory %>%
  dplyr::group_by(year) %>%
  dplyr::summarise(n = sum(nr_adna_samples)) %>%
  ggplot() +
  geom_bar(
    aes(x = year, y = n), stat = "identity"
  ) +
  scale_x_continuous(breaks = 2010:2025)

#### packed-circles plot ####

# arrange papers on grid to release pressure from circleRepelLayout below
grid_pos <- ggpointgrid::arrange_points_on_grid(
  grid_xy = expand_grid(
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
    n = paper_directory$nr_adna_samples * 400
  )
center_and_radius <- packcircles::circleRepelLayout(
  xyz,
  xlim = c(min(xyz$x), max(xyz$x) + 120),
  wrap = FALSE
)$layout
polygons <- packcircles::circleLayoutVertices(center_and_radius)

# assemble plot
p <- ggplot() +
  geom_polygon(
    data = paper_directory %>% dplyr::left_join(polygons, by = "id"),
    mapping = aes(as.Date(x), y, group = id, fill = type),
    linewidth = 0.4
  ) +
  scale_fill_manual(
    values = c(
      "all" = "#5785C1",
      "PAA" = "#CB7A5C",
      "PCA or PMA" = "#FBA82E",
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
    breaks = seq.Date(ymd("2010-01-01"), ymd("2025-12-31"), by = "year"),
    date_labels = "%Y"
  ) +
  theme(
    panel.grid = element_blank(),
    panel.grid.major.x = element_line(colour = "lightgrey", linetype = "dashed"),
    panel.border = element_blank(),
    axis.line.x = element_line(),
    axis.title = element_blank(),
    axis.text.y = element_blank(),
    axis.ticks.y = element_blank(),
    legend.position = c(0.1, 0.8),
    legend.box.background = element_rect(colour = "black")
  )

ggsave(
    "test.png",
    plot = p,
    device = "png",
    scale = 1.8,
    dpi = 300,
    width = 1400, height = 700, units = "px",
    limitsize = F,
    bg = "white"
)

