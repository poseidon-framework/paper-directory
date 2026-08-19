const width = 1400;
const height = 300;

// chart selector

d3.select("#chartMode").on("change", function () {
  const showBars = this.value === "bars";
  d3.select("#chart")
    .style("display", showBars ? "none" : "block");
  d3.select("#barChart")
    .style("display", showBars ? "block" : "none");
});

// bubble chart

const margin = { left: 50, right: 50, top: 20, bottom: 40 };

const innerWidth  = width  - margin.left - margin.right;
const innerHeight = height - margin.top  - margin.bottom;

const svg = d3.select("#chart")
  .attr("width", width)
  .attr("height", height)
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("preserveAspectRatio", "xMidYMid meet")
  .style("width", "100%")
  .style("height", "auto");

const g = svg.append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);

const tooltip = d3.select(".tooltip");

d3.csv("paper_directory.csv", d3.autoType).then(data => {

  data.forEach(d => {
    d.date = new Date(d.publication_date);
    d.community_archive = d.community_archive === true || d.community_archive === "True";
    d.aadr_archive = d.aadr_archive === true || d.aadr_archive === "True";
    d.minotaur_archive = d.minotaur_archive === true || d.minotaur_archive === "True";
  });

  const x = d3.scaleTime()
    .domain(d3.extent(data, d => d.date))
    .range([0, innerWidth]);

  const r = d3.scaleSqrt()
    .domain([0, d3.max(data, d => d.nr_adna_samples)])
    .range([4, 30]);

  const nodes = data.map(d => ({
    ...d,
    radius: r(d.nr_adna_samples),
    x: x(d.date),
    y: innerHeight / 2
  }));

  const simulation = d3.forceSimulation(nodes)
    .force("x", d3.forceX(d => x(d.date)).strength(1))
    .force("y", d3.forceY(innerHeight / 2).strength(0.05))
    .force("collide", d3.forceCollide(d => d.radius + 1));

  const circles = g.selectAll("circle")
    .data(nodes)
    .enter()
    .append("circle")
    .attr("r", d => d.radius)
    .attr("stroke", "#c2c7d0")

    .on("mouseover", (event, d) => {
      tooltip
        .style("opacity", 1)
        .html(
          `<b>${d.title}</b><br>
           ${d.first_author}<br>
           ${d.journal} (${d.year})<br>
           aDNA samples: ${d.nr_adna_samples}`
        );
    })

    .on("mousemove", event => {
      tooltip
        .style("left", (event.pageX + 10) + "px")
        .style("top", (event.pageY + 10) + "px");
    })

    .on("mouseout", () => {
      tooltip.style("opacity", 0);
    });

  simulation.on("tick", () => {
    circles
      .attr("cx", d => d.x)
      .attr("cy", d => d.y);
  });

  function updateColors(mode) {
    circles.attr("fill", d => {
      if (mode === "none") return "#1c212c";
      return d[mode] ? "#f4900c" : "#1c212c";
    });
  }

  d3.select("#colorMode").on("change", function () {
    updateColors(this.value);
  });

  const axis = g.append("g")
    .attr("transform", `translate(0,${innerHeight})`)
    .call(d3.axisBottom(x));

  const zoom = d3.zoom()
    .scaleExtent([0.5, 10])
    .on("zoom", event => {
      const zx = event.transform.rescaleX(x);

      axis.call(d3.axisBottom(zx));

      simulation.force(
        "x",
        d3.forceX(d => zx(d.date)).strength(1)
      );

      simulation.alpha(0.5).restart();
    });

  updateColors("none");
  svg.call(zoom);

});

// bar chart

const barMargin = { left: 60, right: 50, top: 20, bottom: 40 };

const barInnerWidth = width - barMargin.left - barMargin.right;
const barInnerHeight = height - barMargin.top - barMargin.bottom;

const barSvg = d3.select("#barChart")
  .attr("width", width)
  .attr("height", height)
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("preserveAspectRatio", "xMidYMid meet")
  .style("width", "100%")
  .style("height", "auto");

const barG = barSvg.append("g")
  .attr(
    "transform",
    `translate(${barMargin.left},${barMargin.top})`
  );

d3.csv("paper_directory.csv", d3.autoType).then(barData => {

  barData.forEach(d => {
    d.year = +d.year;
    d.nr_adna_samples = +d.nr_adna_samples || 0;
    d.community_archive = d.community_archive === true || d.community_archive === "True";
    d.aadr_archive = d.aadr_archive === true || d.aadr_archive === "True";
    d.minotaur_archive = d.minotaur_archive === true || d.minotaur_archive === "True";
  });

  // exclude entries without a valid publication year
  barData = barData.filter(d =>
    Number.isFinite(d.year) && d.year > 0
  );

  function renderBarChart(archiveMode) {
    // redraw the chart whenever the selected archive changes
    barG.selectAll("*").remove();

    if (barData.length === 0) { return; }

    const totalsByYear = d3.rollup(
      barData,
      papers => {
        const total = d3.sum(
          papers,
          d => d.nr_adna_samples
        );
        const archived = archiveMode === "none"
          ? 0
          : d3.sum(
              papers,
              d => d[archiveMode]
                ? d.nr_adna_samples
                : 0
            );
        return {
          total,
          archived,
          notArchived: total - archived
        };
      },
      d => d.year
    );

    const minYear = d3.min(barData, d => d.year);
    const maxYear = d3.max(barData, d => d.year);

    // include years with no published samples
    const yearlyData = d3
      .range(minYear, maxYear + 1)
      .map(year => {
        const totals = totalsByYear.get(year) || {
          total: 0,
          archived: 0,
          notArchived: 0
        };
        return {
          year,
          ...totals
        };
      });

    const x = d3.scaleBand()
      .domain(yearlyData.map(d => d.year))
      .range([0, barInnerWidth])
      .padding(0.15);

    const y = d3.scaleLinear()
      .domain([
        0,
        d3.max(yearlyData, d => d.total) || 1
      ])
      .nice()
      .range([barInnerHeight, 0]);

    const stackedData = d3.stack()
      .keys(["archived", "notArchived"])(yearlyData);

    // avoid showing too many year labels
    const tickStep = Math.max(
      1,
      Math.ceil(yearlyData.length / 15)
    );

    const tickYears = yearlyData
      .filter((d, i) =>
        i % tickStep === 0 ||
        i === yearlyData.length - 1
      )
      .map(d => d.year);

    barG.append("g")
      .attr(
        "transform",
        `translate(0,${barInnerHeight})`
      )
      .call(
        d3.axisBottom(x)
          .tickValues(tickYears)
          .tickFormat(d3.format("d"))
      );

    barG.append("g")
      .call(d3.axisLeft(y));

    const series = barG.selectAll(".bar-series")
      .data(stackedData)
      .enter()
      .append("g")
      .attr("class", "bar-series")
      .attr("fill", d =>
        d.key === "archived"
          ? "#f4900c"
          : "#1c212c"
      );

    series.selectAll("rect")
      .data(d => d.map(value => ({
        ...value,
        seriesKey: d.key
      })))
      .enter()
      .append("rect")
      .attr("x", d => x(d.data.year))
      .attr("y", d => y(d[1]))
      .attr("width", x.bandwidth())
      .attr("height", d => y(d[0]) - y(d[1]))
      .attr("stroke", "#c2c7d0")
      .on("mouseover", (event, d) => {
        tooltip
          .style("opacity", 1)
          .html(
            `<b>${d.data.year}</b><br>
             Total samples: ${d.data.total}<br>
             In selected archive: ${d.data.archived}<br>
             Not in selected archive: ${d.data.notArchived}`
          );
      })
      .on("mousemove", event => {
        tooltip
          .style("left", (event.pageX + 10) + "px")
          .style("top", (event.pageY + 10) + "px");
      })
      .on("mouseout", () => {
        tooltip.style("opacity", 0);
      });

    barG.append("text")
      .attr("transform", "rotate(-90)")
      .attr("x", -barInnerHeight / 2)
      .attr("y", -45)
      .attr("text-anchor", "middle")
      .attr("font-size", 12)
      .text("Published ancient genomes");
  }

  renderBarChart(
    d3.select("#colorMode").property("value")
  );

  d3.select("#colorMode")
    .on("change.barChart", function () {
      renderBarChart(this.value);
    });
});
