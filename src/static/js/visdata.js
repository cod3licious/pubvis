var article_info = null;
var dataset = null;
var loading = {
  dataset: false
};

//Load the data and visualize
$.getJSON( "static/json/item_info.json", function( data ) {
  article_info = data;
  displayGraph();
  $('.preloader').remove();
});

function displayGraph()
{
  // Checking if data need to be loaded
  if (!dataset && !loading.dataset)
  {
    loading.dataset = true;
    $.getJSON( "static/json/xyc.json", function( data ) {
      dataset = data;
      loading.dataset = false;
      displayGraph();
    });
  }

  if (!dataset || !article_info)
  {
    return;
  }
  $('.map svg').remove();

  //Width and height
  var w = $( window ).width();
  var h = $( window ).height();

  //Padding
  // var left_padding = 20;
  // var right_padding = 20;
  // var top_padding = 20;
  // var bottom_padding = 20;

  //Key function
  var key = function(d) {
    return d["item_id"];
  };

  //Create scale functions
  var xScale = d3.scale.linear()
  .domain([d3.min(dataset, function(d) { return d["x"]; }), d3.max(dataset, function(d) { return d["x"]; })])
  .range([50, w-50]);

  var yScale = d3.scale.linear()
  .domain([d3.min(dataset, function(d) { return d["y"]; }), d3.max(dataset, function(d) { return d["y"]; })])
  .range([h - 120, 70]);

  //Create SVG element
  var svg = d3.select("body").select(".map")
    .append("svg")
    .attr("width", w)
    .attr("height", h)
    .append("g");
    // .call(d3.behavior.zoom().x(xScale).y(yScale).size([w,h]).scaleExtent([0.1, 15]).on("zoom", zoom));

  svg.append("rect")
    .attr("class", "overlay")
    .attr("width", w)
    .attr("height", h);

  //Add the data points
  var circles = svg.selectAll("circle")
    .data(dataset, key)
    .enter()
    .append("circle")
    .attr("cx", function(d) {
      return xScale(d["x"]);
    })
    .attr("cy", function(d) {
      return yScale(d["y"]);
    })
    .attr("r", 4)
    .attr("fill", function(d) {
      return d["color"];
    })
    .attr("stroke", "black")
    .attr("stroke-width", 0.1)
    .attr("opacity", 0.4);
    //.attr("transform", transform);

  function zoom() {
    circles.attr("transform", transform);
  }

  function transform(d) {
    return "translate(" + xScale(d["x"]) + "," + yScale(d["y"]) + ")";
  }

  //Include mouseover effects
  circles.on("mouseover", function(d) {
    //Update the tooltip position and value
    d3.select("#tooltip")
      .select("#title")
      .text(article_info[d["item_id"]]["title"]);
    d3.select("#tooltip")
      .select("#description")
      .text(article_info[d["item_id"]]["authors"]);
    d3.select("#tooltip")
      .select("#journal")
      .text(article_info[d["item_id"]]["publisher"]+" ("+article_info[d["item_id"]]["pub_year"]+")");

    //Show the tooltip
    d3.select("#tooltip").classed("visible", true);
  })
  .on("mouseout", function() {
    //Hide the tooltip
    d3.select("#tooltip").classed("visible", false);
  })
  .on("click", function(d) {
    //go to the document's page
    //window.location = "/article/"+d['item_id'];
    loadArticle(d['item_id']);
  });
}
