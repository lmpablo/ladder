$(function(){
  var ctx = $("#ratings");
  var months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  var ratingsToShow = 100;

  function buildMatchRows(result, opponent, opponentID, score, date) {
    var resultClass = result == 'W' ? 'win' : 'loss';
    var daysOfTheWeek = ['Su', 'M', 'T', 'W', 'Th', 'F', 'Sa']
    return '<div class="row align-middle lb-row lb-row-sm text-center right-spacer">' +
      '<div class="columns small-2"><span class="' + resultClass +'">' + result + '</span></div>' +
      '<div class="columns small-4"><a class="lb-link" href="/profile/' + opponentID + '">@' + opponent + '</a></div>' +
      '<div class="columns small-2">' + score +'</div>' +
      '<div class="columns small-4">' + date.getFullYear() + "/" + (date.getMonth() + 1) + "/" + date.getDate() + ' (' +  daysOfTheWeek[date.getDay()] + ')</div>' +
    '</div>'
  }

  function buildMatchUpRows(oppName, oppId, oppPicture, record, lastPlayed, ppg, winPr) {
    return '<div class="row align-middle opponent-card text-center">' +
      '<div class="columns small-1"><img src="' + oppPicture + '" alt=""></div>' +
      '<div class="columns small-2 text-left"><span class="opp-name">@' + oppName + '</span></div>' +
      '<div class="columns small-2"><span class="opp-stat">' + record + '</span><br><span class="opp-stat-label">RECORD</span></div>' +
      '<div class="columns small-3"><span class="opp-stat"><time class="timeago" datetime="'+  lastPlayed.toISOString() + '">' + lastPlayed + '</time></span><br><span class="opp-stat-label">LAST PLAYED</span></div>' +
      '<div class="columns small-2"><span class="opp-stat">' + Number(ppg).toFixed(2) +'</span><br><span class="opp-stat-label">PPG</span></div>' +
      '<div class="columns small-2"><span class="opp-stat">' + Number(winPr * 100).toFixed(0) + '%</span><br><span class="opp-stat-label">WIN PROBABILITY</span></div>' +
    '</div>'
  }

  $.get("/api/v1/players/" + playerID, function(data) {
    var user = data.data;
    $("img#profile-image").attr("src", user.profile_picture);
    $("#profile-name").text("@" + user.slack_name);
    $("#real-name").text(user.real_name);
    $("#profile-rating").text("(" + Number(user.rating).toFixed(0) + ")");

    var numGames = parseInt(user.num_games_played);
    var wins = parseInt(user.num_games_won);
    var losses = numGames - wins;
    var winsPercentage = ((wins / numGames) * 100) - 0.1
    var lossesPercentage = ((losses / numGames) * 100) - 0.1
    $("#match-data .match-counts .win").text(wins);
    $("#match-data .match-counts .loss").text(losses);
    $(".win-bar").css("width", Number(winsPercentage).toFixed(1) + "%")
    $(".lose-bar").css("width", Number(lossesPercentage).toFixed(1) + "%")
  })

  $.get("/api/v1/rankings?top=-1", function(data){
    var rankings = data.data.rankings;
    var userData = ""
    for (var i = 0, len = rankings.length; i < len; i++) {
      var r = rankings[i];
      if (r.player_id == playerID) {
        userData = r;
      }
    }
    if (userData) {
      $("#profile-rank").text("#" + userData.rank);
    }
  });

  $.get("/api/v1/players/" + playerID +"/stats", function(data) {
    var stats = data.data;
    var matchups = data.data.match_ups;
    var $matchups = $("#match-ups");
    console.log(stats)
    $("#ppg").text(Number(stats.ppg).toFixed(2))
    $("#ppg-w").text(Number(stats.win_ppg).toFixed(2))
    $("#ppg-l").text(Number(stats.lose_ppg).toFixed(2))
    $("#apd").text(Number(stats.ppg_diff).toFixed(2))
    $("#apd-w").text(Number(stats.win_ppg_diff).toFixed(2))
    $("#apd-l").text(Number(stats.lose_ppg_diff).toFixed(2))
    $("#curr-streak").text(stats.current_streak.streak + " " + stats.current_streak.type[0].toUpperCase())
    $("#longest-w-streak").text(stats.longest_win_streak + " W")
    $("#longest-l-streak").text(stats.longest_lose_streak + " L")

    for (var i = 0, len = matchups.length; i < len; i++) {
      // buildMatchUpRows(oppName, oppId, oppPicture, record, lastPlayed, ppg, winPr)
      var m = matchups[i];
      var record = m.games_won_against + "-" + m.games_lost_against;
      $matchups.append(buildMatchUpRows(m.opp_slack_name, m.opp_id, m.opp_profile_picture, record, new Date(m.last_played_against), m.ppg_against, m.pr_win_against))
    }
    $("time.timeago").timeago();
  })

  $.get("/api/v1/players/" + playerID + "/matches?sort=-1&limit=10", function(data) {
    var matches = data.data.matches;
    var matchHistoryDiv = $("#match-history")
    for (var i = 0, len = matches.length; i < len; i++) {
      var match = matches[i];
      matchHistoryDiv.append(buildMatchRows(match.result, match.opponent_name, match.opponent, match.scores, new Date(match.timestamp)))
    }
  });


  (function buildGraph() {
    $.get("/api/v1/players/" + playerID + "/ratings?sort=descending&top=" + ratingsToShow, function(data) {
      // the ratings come in newest -> oldest order, limited to the top N most recent
      // rankings
      var ratingsData = data.data.ratings;
      var numRatings = ratingsData.length;
      var previousDate = "";
      var matchNum = 1;
      var ratings = ratingsData.map(function(el, index) {
        return el.rating.toFixed(2);
      });
      var dates = ratingsData.reverse().map(function(el, index) {
        var date = new Date(el.timestamp);
        var d = months[(date.getMonth() + 1)] + " " + date.getDate() + ", " + date.getFullYear()
        if (d == previousDate) {
          matchNum += 1
        } else {
          matchNum = 1
        }
        previousDate = d;
        return d + (matchNum > 1 ? " (Match #" + matchNum + ')' : '');
      });

      $('#num-games-ratings').text(numRatings < ratingsToShow ? numRatings : ratingsToShow);
      $('#start-date-ratings').text(dates[0]);
      $('#end-date-ratings').text(dates[dates.length - 1]);

      var myChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'Rating',
                data: ratings.reverse(),
                borderWidth: 1,
                borderColor: "#FF4F00",
                backgroundColor: 'rgba(255, 79, 0, 0.5)'
            }]
        },
        options: {
          scales: {
            yAxes: [{
              ticks: {
                  beginAtZero: false
              }
            }],
            xAxes: [{
              display: false,
              autoSkip: true
            }]
          },
          legend: {
            display: false
          }
        }
      });
    });
  })();
})
