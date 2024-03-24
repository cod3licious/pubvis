

// Initializing UI Components
$('.article-search').on('keyup', function(e) {
  var value = e.target.value;

  $.getJSON("/items/search?q=" + encodeURIComponent(value), function( data ) {
    showSearchResults(data);
  });
});


$('.search-results').on('click', function(e) {
  var searchResult = $(e.target).closest('.search-result');
  if (searchResult.length > 0)
  {
    var pbId = searchResult[0].id.match(/article-([A-Za-z0-9.]+)/i)[1];
    hideSearchResults();
    loadArticle(pbId);
  }
});

$('.article .close').on('click', function(e) {
  closeArticle();
});

$('.similar-articles').on('click', function(e) {
  var simArticle = $(e.target).closest('.similar-article');
  if (simArticle && simArticle[0] && simArticle[0].id)
  {
    var pbId = simArticle[0].id.match(/article-([A-Za-z0-9.]+)/)[1];
    var type = simArticle[0].dataset['type'];
    loadArticle(pbId, type);
    $('.similar-article').removeClass('selected');

    $(simArticle).addClass('selected');
  }
});

$('#compare-button').on('click', function(e) {
  showArticleCompare();
});

$('.compare-buttons input[type=button]').on('click', function(e) {
  compareArticle($('textarea')[0].value);
});

$('#recommended-button').on('click', function(e) {
  showRecommendedArticles();
});

$('.article-yes').on('click', function(e) {
  rateArticle(1);
});

$('.article-no').on('click', function(e) {
  rateArticle(-1);
});

$(document.documentElement).on('click', function(e) {
  hideSearchResults();
});

