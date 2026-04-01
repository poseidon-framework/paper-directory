const width = 1400;
const height = 300;
const margin = {left:50,right:50,top:20,bottom:40};

const svg = d3.select("svg");
const g = svg.append("g");

const tooltip = d3.select(".tooltip");

d3.csv("paper_directory.csv", d3.autoType).then(data => {

  data.forEach(d => d.date = new Date(d.publication_date));
  data.forEach(d => {
    d.community_archive = d.community_archive === "True";
    d.aadr_archive = d.aadr_archive === "True";
    d.minotaur_archive = d.minotaur_archive === "True";
  });

  const x = d3.scaleTime()
    .domain(d3.extent(data, d => d.date))
    .range([margin.left, width - margin.right]);

  const r = d3.scaleSqrt()
    .domain([0, d3.max(data, d => d.nr_adna_samples)])
    .range([4, 30]);

  const nodes = data.map(d => ({
    ...d,
    radius: r(d.nr_adna_samples),
    x: x(d.date),
    y: height/2
  }));

  const simulation = d3.forceSimulation(nodes)
    .force("x", d3.forceX(d => x(d.date)).strength(1))
    .force("y", d3.forceY(height/2).strength(0.05))
    .force("collide", d3.forceCollide(d => d.radius + 1));

  const circles = g.selectAll("circle")
    .data(nodes)
    .enter()
    .append("circle")
    .attr("r", d => d.radius)
    .attr("stroke", d => "#c2c7d0")

    .on("mouseover", (event,d) => {
      tooltip.style("opacity",1)
        .html(
          "<b>" + d.title + "</b><br>" +
          d.first_author + "<br>" +
          d.journal + " (" + d.year + ")<br>" +
          "aDNA samples: " + d.nr_adna_samples
        );
    })

    .on("mousemove", (event) => {
      tooltip
        .style("left", (event.pageX+10)+"px")
        .style("top", (event.pageY+10)+"px");
    })

    .on("mouseout", () => {
      tooltip.style("opacity",0);
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
  
  d3.select("#colorMode").on("change", function() {
    updateColors(this.value);
  });

  const axis = g.append("g")
    .attr("transform", `translate(0,${height-margin.bottom})`)
    .call(d3.axisBottom(x));

  const zoom = d3.zoom()
    .scaleExtent([0.5, 10])
    .on("zoom", (event) => {
      const zx = event.transform.rescaleX(x);
      axis.call(d3.axisBottom(zx));
      simulation.force(
        "x",
        d3.forceX(d => zx(d.date)).strength(1)
      );
      simulation.alpha(0.5).restart();
    });

  updateColors("community_archive");
  svg.call(zoom);

});
