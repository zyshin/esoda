/*!
 * Main logic for ESODA front end
 */

$(function () {
  'use strict';

  // TODO: Initialize autocomplete etc.
  Storage.prototype.setObj = function (key, obj) {
    return this.setItem(key, JSON.stringify(obj))
  };
  Storage.prototype.getObj = function (key) {
    return JSON.parse(this.getItem(key))
  };
  function setCookie(cname, cvalue, exdays) {
    var d = new Date();
    d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
    var expires = "expires=" + d.toUTCString();
    document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
  }

  function getCookie(cname) {
    var name = cname + "=";
    var decodedCookie = decodeURIComponent(document.cookie);
    var ca = decodedCookie.split(';');
    for (var i = 0; i < ca.length; i++) {
      var c = ca[i];
      while (c.charAt(0) === ' ') {
        c = c.substring(1);
      }
      if (c.indexOf(name) === 0) {
        return c.substring(name.length, c.length);
      }
    }
    return "";
  }

  function insertHistory(history, val) {
    if (history.length > 0) {
      history = history.filter(function (item) {
        return item !== val;
      });
    }
    history.unshift(val);
    if (history.length > 5) history.pop();
    return history;
  }

  window.clearHistory = function () {
    if (("localStorage" in window) && window.localStorage !== null) {
      localStorage.setObj("history", []);
    } else {
      setCookie("history", "[]", 365);
    }
  };

  function storeHistory() {
    var history;
    if (("localStorage" in window) && window.localStorage !== null) {
      history = localStorage.getObj("history");
      history = insertHistory(history, $("#SearchBox").val());
      localStorage.setObj("history", history);
    } else {
      history = JSON.parse(getCookie("history"));
      history = insertHistory(history, $("#SearchBox").val());
      setCookie("history", JSON.stringify(history), 365);
    }
  }

  function readHistory() {
    var history;
    if (("localStorage" in window) && window.localStorage !== null) {
      history = localStorage.getObj("history");
      if (history === null) {
        history = [];
        localStorage.setObj("history", history);
      }
    } else {
      history = JSON.parse(getCookie("history"));
      if (history === "") {
        history = [];
        setCookie("history", JSON.stringify(history), 365);
      }
    }

    defaultList = $.map(history, function (value) {
      return {label: value, desc: "", category: "最近搜过"};
    });
  }

  /*--------Testing code---------*/
  var defList = [
    {label: "主谓", desc: "value increase", value: "value increase", category: "用法示例"},
    {label: "修饰", desc: "high impact", value: "high impact", category: "用法示例"},
    {label: "动宾", desc: "open program", value: "open program", category: "用法示例"}
  ];
  /*--------Testing code---------*/

  var defaultList = [];
  readHistory();
  defaultList = defaultList.concat(defList);
  /*
   var defaultList = [];
   $.getJSON( "search.php", "", function(data, status, xhr) {
   defaultList = data;
   });
   */

  var auto = 0;
  $.widget("custom.catcomplete", $.ui.autocomplete, {
    _create: function () {
      this._super();
      this.widget().menu("option", "items", "> :not(.ui-autocomplete-category)");
    },
    _renderMenu: function (ul, items) {
      var that = this, currentCategory = "";
      $.each(items, function (index, item) {
        var li;
        if (item.category !== currentCategory) {
          ul.append("<li class='ui-autocomplete-category'>" + item.category + "</li>");
          currentCategory = item.category;
        }
        li = that._renderItemData(ul, item);
        if (item.category) {
          li.attr("aria-label", item.category + " : " + item.label);
        }
      });
      if ($("#SearchBox").innerWidth() < 420){
        ul.append("<li class='ui-autocomplete-category ui-autocomplete-warnings'>" +
        "<a href=\"\" id=\"ClearHistory\" onclick=\"window.clearHistory()\">清除搜索历史</a></div></li>");
      }
      else {
        ul.append("<li class='ui-autocomplete-category ui-autocomplete-warnings'>" +
          "<div class=\"inline\">按“回车”发起检索</div>" +
          "<div class=\"pull-right\">" +
          "<a href=\"\" id=\"ClearHistory\" onclick=\"window.clearHistory()\">清除搜索历史" +
          "<span class=\"glyphicon glyphicon-time\"></span></a></div></li>");
      }
    },
    _renderItem: function (ul, item) {
      return $("<li>")
        .append("<div><span class=\"ui-autocomplete-label\">" + item.label + "</span>" +
          "&nbsp;&nbsp;<span class=\"ui-autocomplete-desc\">" + item.desc + "</span></div>")
        .appendTo(ul);
    },
    _resizeMenu: function () {
      this.menu.element.outerWidth($(".ui-autocomplete-input").outerWidth());
    },
    _closeOnClickOutside: function (event) {
      if (!this._isEventTargetInWidget(event)) {
        this.close();
        if ($("#SearchBox").val().trim().length === 0) {
          $("#SearchBox").val('');
        }
      }
    }
  });

  function split(val) {
    return val.split(/\s+/);
  }

  function extractLast(term) {
    return split(term).pop();
  }

  function extractPrefix(term) {
    return term.replace("<strong>", "").replace("</strong>", "");
  }

  var cache = {};
  $("#SearchBox").catcomplete({
    minLength: 0,
    delay: 150,
    source: function (request, response) {

      var term = extractLast(request.term);
      if (term.length < 1) {
        response(defaultList);
        return;
      }

      if (term in cache) {
        response(cache[term]);
        return;
      }

      $.getJSON("/suggest/", {term: term}, function (data, status, xhr) {
        var show = [];
        var reg_term = term.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
        var matcher = new RegExp("^" + reg_term, "i");
        // As experimented, the items in *data* are references through getData method,
        // so that there's a new array needed for showing.
        data.suggest.forEach(function (item) {
          show.push(
            {
              label: item.label.replace(matcher, "<strong>" + item.label.match(matcher) + "</strong>"),
              desc: item.desc,
              category: item.category
            });
        });
        cache[term] = show;
        response(show);
      });
    },
    search: function () {
      if (this.value.length === 0) {
        return true;
      }
      var term = extractLast(this.value);
      if (term.length < 1) {
        return false;
      }
    },
    focus: function (event, ui) {
      if (event.keyCode === $.ui.keyCode.UP || event.keyCode === $.ui.keyCode.DOWN) this.value = extractPrefix(ui.item.value);
      return false;
    },
    select: function (event, ui) {
      var terms = split(this.value);
      terms.pop();
      terms.push(extractPrefix(ui.item.value));

      // this.value = terms.join(" ");
      if (event.keyCode !== 13) this.value = terms.join(" ");  // if Enter not press

      if (event.keyCode !== $.ui.keyCode.TAB) {
        $("#SearchForm").submit();
      }
      else
        this.value = extractPrefix(ui.item.value);

      return false;

      /*
       this.value = ui.item.value;
       $( "#SearchForm" ).submit();
       return false;
       */
    }
  });

    // .focus(function () {
    //   setTimeout(function(){
    //     if (this.value == "")
    //       $(this).catcomplete("search", "");
    //   }, 250);
    // });

  $('#SearchForm').submit(function () {
    if ($("#SearchBox").val().trim().length === 0) {
      return false;
    }
    else {
      storeHistory();
    }
  });

  $.clickHeart = function (e) {
    e.preventDefault();
    $(e.target).toggleClass("glyphicon-heart-empty");
    $(e.target).toggleClass("glyphicon-heart");
  };

  $("#AddBookmark").click(function (e) {
    e.preventDefault();
    var bookmarkUrl = window.location.href;
    var bookmarkTitle = document.title;

    if ("addToHomescreen" in window && addToHomescreen.isCompatible) { // Mobile browsers
      addToHomescreen({autostart: false, startDelay: 0}).show(true);
    } else if (window.sidebar && window.sidebar.addPanel) { // Firefox <=22
      window.sidebar.addPanel(document.title, window.location.href, '');
    } else if ((window.sidebar && /Firefox/i.test(navigator.userAgent))
      || (window.opera && window.print)) { // Firefox 23+ and Opera <=14
      $(this).attr({
        href: bookmarkUrl,
        title: bookmarkTitle,
        rel: "sidebar"
      }).off(e);
      return true;
    } else if (window.external && ("AddFavorite" in window.external)) { // For IE Favorite
      window.external.AddFavorite(bookmarkUrl, bookmarkTitle);
    } else { // for other browsers which does not support (Chrome/Safari/Opera15+)
      alert("您的浏览器不支持该操作。\n请按 " +
        (navigator.userAgent.toLowerCase().indexOf('mac') !== -1 ? 'Command/Cmd' : 'CTRL') +
        "+D 添加收藏。");
    }
    return false;
  });

  $('.share-a').click(function (e) {
    e.preventDefault();
  });

  $('.wechat-share').popover();
  $('.wechat-share').on('shown.bs.popover', function () {
    $('.wechat-qr').qrcode({render: 'canvas', width: 100, height: 100, text: window.location.href});
  });

  // $(window).resize(function () {
  //   if(auto == 1) {
  //     $('#SearchBox').catcomplete('search');
  //   }
  // });

  // $(window).mousewheel(function() {
  //   $('#SearchBox').catcomplete('search').fixed();
  // });

  $('#SearchBox').on('click', function (e) {
    e.stopPropagation();
    $('.jumbotron').css("padding-top", "64px");
    $('.jumbotron').css("transition","250ms");
    auto = 1;
    setTimeout(function(){
      $('#SearchBox').catcomplete('search');
    }, 250);
  });

  $('.input-group-btn').on('click', function (e) {
    e.stopPropagation();
  });

  $(window).on('click', function (e){
    $('.jumbotron').css("padding-top", "150px");
    auto = 0;
  });
});
