var userId = $.cookie("userId") || randomUserId();
var currentArticle = 0;
var searchResultsVisible = false;

function randomUserId()
{
  var timestamp = new Date().getTime();
  var userId = 'u' + timestamp + Math.random();
  $.cookie("userId", userId);
  return userId;
}

function rateArticle(rating)
{
  $('.article-like').addClass('rated');
  $.ajax({
    dataType: "json",
    url: "/ratings",
    method: "post",
    data: JSON.stringify( {
      item_id: currentArticle,
      user_id: userId,
      rating: rating
    }),
    contentType:"application/json; charset=utf-8",
    success: function(data) {
      console.log(data);
    }
  });
}

function renderArticleData(data)
{
  currentArticle = data['item_id'];
  $('.article-search')[0].value = '';
  $('.article').removeClass('recommend-mode');
  $('.article-like').removeClass('rated');
  $('.article').removeClass('compare-mode');
  $(".article-hd").html(data["title"]);
  $(".article-publisher").html(data["publisher"] + ", " + data["pub_year"]);
  $(".article-author").html(data["authors"]);
  $(".article-text").html("<p>" + data["description"].replace(/[\n]/, "</p><p>") + "</p>");
  $(".article-link").html("<a href=\""+data["item_url"]+"\" target=\"_blank\">view original article</a>");
}

function closeArticle()
{
  $('.article').removeClass('visible');
}

function showSearchResults(results)
{
  var html = [];
  for (var i = 0; i < results.length; i++)
  {
    html.push('<div class="search-result result-appear" id="article-' +
      results[i]['item_id'] + '">');

    html.push('<div class="search-result-title">' + results[i]['title'] +
      '</div>');
    html.push('<div class="search-result-authors">' + results[i]['pub_year'] + ', '+
      results[i]['authors'] + '</div>');

    html.push('</div>');
  }

  $('.search-results')[0].innerHTML = html.join('');

  d3.selectAll('.search-result')
    .transition()
    .duration(500)
    .delay(function(d, i) { return i * 100; })
    .style("transform", 'translate(0, 0)');

  d3.selectAll('.search-results')
    .transition()
    .duration(250)
    .style("transform", 'translate(0, 0)');

  searchResultsVisible = true;
};

function hideSearchResults()
{
  if (searchResultsVisible)
  {
    d3.selectAll('.search-results')
      .transition()
      .duration(250)
      .style("transform", 'translate(-100%, 0)');
  }

  searchResultsVisible = false;
};

function loadArticle(item_id, type)
{
  $.getJSON("/items/" + encodeURIComponent(item_id), function( data ) {
    renderArticleData(data)
  });

  if (type != 'compare' && type != 'recommendation')
  {
    setArticleListHeader('Similar articles');
    $.getJSON("/items/" + encodeURIComponent(item_id) + "/similar", function( data ) {
      renderSimilarArticles(data);
      $('.article').addClass('visible');
    });
  }

}

function renderSimilarArticles(results, type)
{
  var type = type || 'similar';
  var html = [];
  for (var i = 0; i < results.length; i++)
  {
    var score = results[i]['score'] ? results[i]['score'].toFixed(1) : 0;
    html.push('<div class="similar-article sa-appear" id="article-' +
      results[i]['item_id'] + '" data-type="' + type + '">');

    if (type != 'recommendation')
    {
      html.push('<div class="similar-article-donut">' + score + '/100</div>');
      html.push('<div class="similar-article-score">' + score + '%</div>');
    }

    html.push('<div class="similar-article-hd">' + results[i]['title'] +
      '</div>');
    html.push('<div class="similar-article-subhd">' + results[i]['pub_year'] + ', '+
      results[i]['authors'] + '</div>');

    html.push('</div>');
  }

  $('.similar-articles-bd')[0].scrollTop = 0;
  $('.similar-articles-bd')[0].innerHTML = html.join('');
  $('.similar-articles-bd').removeClass('compare').removeClass('recommendation');
  $('.similar-articles-bd').addClass(type);

  $('.similar-article-donut').peity('donut', {fill: ["#0099d3", "#ccc"], radius: 30, innerRadius: 25})
};

function compareArticle(text)
{
  if (!text)
  {
    alert('Enter an abstract to find related articles.');
    return;
  }
  $.ajax({
    dataType: "json",
    url: "/items/similar",
    method: "post",
    data: JSON.stringify( {q: text}),
    contentType:"application/json; charset=utf-8",
    success: function(data) {
      renderSimilarArticles(data, 'compare');
    }
  });
}

function showArticleCompare()
{
  $('textarea')[0].value = '';
  renderSimilarArticles([], 'compare');
  setArticleListHeader('Search results');
  $('.article').addClass('visible').addClass('compare-mode').removeClass("recommend-mode");
}

function setArticleListHeader(header)
{
  $('.similar-articles-hd').html(header);
}

function showRecommendedArticles()
{
  setArticleListHeader('Recommended articles');
  $('.article').addClass('visible').addClass("recommend-mode");
  $('.similar-articles-bd')[0].innerHTML = '<span class="loading">loading...</span>';
  $.ajax({
    dataType: "json",
    url: "/users/" + userId + "/recommendations",
    method: "get",
    contentType:"application/json; charset=utf-8",
    success: function(data) {
      renderSimilarArticles(data, 'recommendation');
    }
  });

}
