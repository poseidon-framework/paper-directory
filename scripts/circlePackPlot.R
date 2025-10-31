library(magrittr)
library(ggplot2)

hu <- readr::read_csv("~/agora/paper-directory/docs/paper_directory.csv")

hu %>%
  dplyr::group_by(year) %>%
  dplyr::summarise(n = sum(nr_adna_samples)) %>%
  ggplot() +
  geom_bar(
    aes(x = year, y = n), stat = "identity"
  )

hu <- hu %>%
  dplyr::filter(nr_adna_samples > 0) %>%
  dplyr::mutate(
    id = 1:dplyr::n(),
    type = dplyr::case_when(
      (community_archive | minotaur_archive) & aadr_archive ~ "all",
      (community_archive | minotaur_archive) ~ "PCA or PMA",
      aadr_archive ~ "PAA",
      .default = "none"
    )
  ) %>%
  dplyr::arrange(type)

grid_pos <- ggpointgrid::arrange_points_on_grid(
  grid_xy = expand_grid(
    x = seq(
      min(as.double(hu$publication_date)),
      max(as.double(hu$publication_date)),
      by = 50
    ),
    y = seq(-1000,1000,100)
  ) %>% as.matrix,
  pts_xy = hu %>%
    dplyr::transmute(
      x = as.double(publication_date),
      y = 0
    ) %>% as.matrix()
)

# plot(grid_pos[,1],grid_pos[,2])

xyz <- tibble::tibble(
    x = as.double(hu$publication_date),#grid_pos[,1],
    y = grid_pos[,2],
    n = hu$nr_adna_samples * 350
  )
center_and_radius <- packcircles::circleRepelLayout(
  xyz,
  xlim = c(min(xyz$x), max(xyz$x) + 110),
  wrap = FALSE
)$layout
polygons <- packcircles::circleLayoutVertices(center_and_radius)

p <- ggplot() +
  geom_polygon(
    data = hu %>% dplyr::left_join(polygons, by = "id"),
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
  guides(fill = guide_legend(title = "Archives")) +
  geom_text(
    data = hu %>% dplyr::bind_cols(
        center_and_radius %>% dplyr::transmute(x_center = x, y_center = y)
      ) %>% dplyr::filter(nr_adna_samples > 160),
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
    date_breaks = "1 year", date_labels = "%Y"
  ) +
  theme(
    panel.grid = element_blank(),
    panel.grid.major.x = element_line(colour = "lightgrey"),
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
    width = 1400, height = 800, units = "px",
    limitsize = F,
    bg = "white"
)

