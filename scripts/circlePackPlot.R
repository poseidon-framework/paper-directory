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
      community_archive & aadr_archive ~ "both",
      community_archive ~ "PCA",
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
      by = 100
    ),
    y = seq(-1000,1000,50)
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
    n = hu$nr_adna_samples * 200
  )
center_and_radius <- packcircles::circleRepelLayout(
  xyz,
  xlim = range(xyz$x),# ylim = c(0,3000),
  wrap = FALSE
)$layout
polygons <- packcircles::circleLayoutVertices(center_and_radius)

flu <- hu %>%
  dplyr::bind_cols(
    center_and_radius %>%
      dplyr::transmute(x_center = x, y_center = y)
  ) %>%
  dplyr::left_join(
    polygons,
    by = "id"
  )

flu %>%
  ggplot() +
  geom_polygon(
    mapping = aes(as.Date(x), y, group = id, fill = type),
    colour="black"
  ) +
  geom_text(
    mapping = aes(x = as.Date(x_center), y = y_center, label = nr_adna_samples),
    colour="black", size = 3
  ) +
  coord_fixed() +
  theme_bw()

