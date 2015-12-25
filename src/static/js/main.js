show_settings = false;
function keyup_complete(e) {
    var locations = $(this).parent().find('.location');
    var active = $(this).parent().find('.location').filter('.active');
    if (e.which == 40) {
        var nexts = active.nextAll(':visible');
        if (nexts.length) {
            active.removeClass('active');
            active = nexts.first().addClass('active');
            if (active.offset().top+active.outerHeight() > active.parent().parent().offset().top+active.parent().parent().height()) {
                active[0].scrollIntoView(false);
            }
        }
    } else if (e.which == 38) {
        var prevs = active.prevAll(':visible');
        if (prevs.length) {
            active.removeClass('active');
            active = prevs.first().addClass('active');
            if (active.offset().top < active.parent().parent().offset().top) {
                active[0].scrollIntoView(true);
            }
        }
    } else if (e.which == 13) {
        active.click();
    } else {
        if (e.which == 27) {
            $(this).val('').keyup();
        }

        var value = $(this).val().toLowerCase();
        locations.filter(':not(.user, .locating)').each(function() {
            $(this).hide().toggle($(this).text().toLowerCase().indexOf(value)>-1 || $(this).val().indexOf(value)>-1);
        });
        toggle_user_location(locations.filter('.user'), value);
        active = locations.removeClass('active').filter(':visible').first().addClass('active');
        if (active.is(':first-child')) active.parent().scrollTop(0);
    }
}
function toggle_user_location(location, name) {
    location.hide();
    if (name.match(/^[0-9]+:[0-9]+:[0-9]+$/)) {
        pos = name.split(':');
        if ((pos[0].length > 1 && pos[0][0] == '0') ||
            (pos[1].length > 1 && pos[1][0] == '0') ||
            (pos[2].length > 1 && pos[2][0] == '0')) return;
        var level = parseInt(pos[0]);
        var x = parseInt(pos[1]);
        var y = parseInt(pos[2]);
        if (level < 0 || level >= levels || x < 0 || x >= width || y < 0 || y >= height) return;
        location.val(name);
        location.find('span').text('…');
        location.find('small').text(name);
        $.ajax({'type': 'GET', 'url': '/n'+String(level)+':'+String(x)+':'+String(y), 'success': function(data) {
            $('.location[value="'+String(data.name)+'"] span').text(data.title);
        }, 'dataType': 'json'});
        location.show();
    }
}
function update_history() {
    var qs = '';
    if ($('#s').is(':visible')) {
        qs = $('#mainform').serialize().replace('&ajax=1', '');
    } else {
        if ($('.p[name=o]').is('.selected')) qs += 'o='+$('[type=hidden][name=o]').val();
        if ($('.p[name=d]').is('.selected')) qs += (qs.length?'&':'')+'d='+$('[type=hidden][name=d]').val();
    }
    window.history.replaceState(qs, document.title, '/'+(qs.length?'?':'')+qs);
}
function point_set() {
    var qs = [];
    if ($('.p[name=o]').is('.selected')) qs.push('o='+$('[type=hidden][name=o]').val());
    if ($('.p[name=d]').is('.selected')) qs.push('d='+$('[type=hidden][name=d]').val());
    update_history();
    var cansubmit = ($('.p:not(.selected), .p.locating').length === 0);
    $('#main-submit').prop('disabled', !cansubmit);
    $('#savesettings').toggle(show_settings);
    if (!cansubmit) $('#savesettings').prop('checked', show_settings);
}
function nearby_stations_available() {
    console.log(JSON.parse(mobileclient.getNearbyStations()));
    if ($('.p.locating').length > 0) {
        $.ajax({
            type: "POST",
            url: '/locate',
            data: { stations: mobileclient.getNearbyStations() },
            dataType: 'json',
            success: function(data) {
                if (data === null) {
                    $('.p.locating').find('.locating .reset').click();
                    return;
                }
                current_location = data;
                set_position();
                $('.p.locating').each(function() {
                    var location = $(this).find('button.user');
                    location.val(current_location.name);
                    location.find('span').text(current_location.title);
                    location.find('small').text(current_location.name);
                    location.click();
                });
                toggle_user_location($('.p[name=d]').find('button.user'), origin);
            },
        });
    }
}
function linkbtn_click(e) {
    e.preventDefault();
    e.stopPropagation();
    $('#linkmodal').remove();
    $('body').append(
        $('<div id="linkmodal">').data('title', $(this).parents('.location').find('span').text()).append(
            $('<img>').attr('src', '/qr'+$(this).attr('href'))
        ).append(
            $('<strong>').text('https://'+location.host+$(this).attr('href')).css('display', 'block').css('margin-bottom', 15)
        ).append(
            $('<button class="pure-button">').text($('#main').attr('data-locale-close')).click(function() {$('#linkmodal').remove();})
        )
    );
    if ($(this).parents('.p').is('[name=d]') &&
          typeof mobileclient !== "undefined" && typeof mobileclient.createShortcut !== "undefined") {
        $('<button class="pure-button">').text($('#main').attr('data-locale-shortcut')).click(function() {
            mobileclient.createShortcut($(this).siblings('strong').text(), $(this).parent().data('title'));
        }).insertBefore($('#linkmodal button:last-child'));
        $('<br>').insertBefore($('#linkmodal button:last-child'));
    }
    if (typeof mobileclient !== "undefined") {
        $('<button class="pure-button">').text($('#main').attr('data-locale-share')).click(function() {
            mobileclient.shareUrl($(this).siblings('strong').text());
        }).insertBefore($('#linkmodal button:last-child'));
    }
}
function set_position() {
    $('circle.pos').remove();
    // <circle class="pos" r="5" cx="{{ 0-routepart.minx+20 }}" cy="{{ 0-routepart.miny+20 }}" />
    $('.path').each(function() {
        var map = $(this).find('.map');
        if (map.attr('data-level') == String(current_position.level)) {
            $('<circle class="pos" r="5" />').attr({
                'cx': current_position.x+parseInt(map.find('image').attr('x')),
                'cy': current_position.y+parseInt(map.find('image').attr('y'))
            }).insertBefore(map.find('.connections'));
        }
        $(this).html($(this).html());
    });
    $('.mapinput .pos').remove();
    $('<div class="pos">').css({
        left: current_position.x,
        top: current_position.y
    }).appendTo('.mapinput .poscontainer').attr('data-level', current_position.level);
    $('.mapinput .pos').each(function() {
        $(this).toggle($(this).parent().siblings('img[data-level='+String($(this).attr('data-level'))+']:visible').length > 0);
    });

    $('.maplevelselect.poswait').removeClass('poswait').find('button[data-level='+String(current_position.level)+']').click();
    $('.mapinput.poswait').removeClass('poswait').scrollLeft(current_position.x-$('.mapinput').width()/2).scrollTop(current_position.y-$('.mapinput').height()/2);
}
$(document).ready(function() {
    wifilocate = ($('body').attr('data-wifilocate') == '1');
    levels = parseInt($('body').attr('data-levels'));
    width = parseInt($('body').attr('data-w'));
    height = parseInt($('body').attr('data-h'));
    $('body').addClass('yesscript');
    $('.location.c').remove();
    $('.noscript').remove();
    $('.p .selector').each(function() {
        if ($(this).find('.autocomplete-list').length === 0) {
            $('.autocomplete-list').clone().appendTo($(this));
        }
    });
    $('.autocomplete-list').mousedown(function() {
        $('.locationinput').queue(function() {});
    }).mouseup(function() {
        $('.locationinput').dequeue();
    }).each(function() {
        var name = $(this).parent().attr('name');
        $('<input type="text" class="locationinput pure-u-1" autocomplete="off">').insertBefore(this).attr({
            'placeholder': $('#main').attr('data-locale-input-'+$(this).parents('.p').attr('name'))
        }).keyup(keyup_complete).focus(keyup_complete).focus(function() {
            $('.locationinput').not(this).dequeue();
        }).blur(function() {
            $(this).queue(function(n) {
                    $(this).val(''); $(this).parent().find('.location').hide();
                n();
            });
        });
        var buttons = $('<div class="buttons">').append(
            $('<button class="map">')
        );
        if (typeof mobileclient !== "undefined") {
            buttons.prepend(
                $('<button>').addClass(wifilocate ? 'locate' : 'nolocate')
            );
        }
        buttons.insertBefore(this);

        $('<button type="submit" class="location user">').attr('name', $(this).parents('.p').attr('name')).append(
            $('<span>')
        ).append(
            $('<small>')
        ).appendTo($(this).find('form'));
        $('<button type="submit" class="location locating">').attr('name', $(this).parents('.p').attr('name')).attr('value', 'locating').append(
            $('<span>').text($('#main').attr('data-locale-locating'))
        ).appendTo($(this).find('form'));

        var mapinput = $('<div class="mapinput">').hide().insertBefore(this);
        var levelselect = $('<div class="maplevelselect">').hide().insertBefore(this);
        levelselect.append($('<button class="pure-button pure-button-danger abort">').text('×'));
        for (var i=0;i<parseInt($('body').attr('data-levels'));i++) {
            levelselect.append($('<button class="pure-button">').attr('data-level', i).text(i));
            mapinput.append($('<img>').attr('src', '/static/img/levels/'+$('body').attr('data-name')+'/level'+String(i)+'.jpg').attr('data-level', i).hide());
        }
        mapinput.append($('<div class="poscontainer">'));
        levelselect.find('button[data-level=0]').click();
    });
    $('.nolocate').attr('title', $('#main').attr('data-locale-nolocate')).click(function() {
        alert($('#main').attr('data-locale-nolocate'));
    });
    $('.locate').click(function() {
        $(this).parents('.p').find('.locating').click();
    });
    $('button.map').click(function() {
        $(this).parents('.p').find('.locationinput, .buttons').blur().hide();
        var mapinput = $(this).parents('.p').find('.mapinput, .maplevelselect').toggleClass('poswait', true).show();
        mapinput.parent().find('button[data-level=0]').click();
        mapinput.scrollTop((parseInt($('body').attr('data-h'))-mapinput.height())/2);
        mapinput.scrollLeft((parseInt($('body').attr('data-w'))-mapinput.width())/2);
    });
    $('.mapinput img').click(function(e) {
        level = parseInt($(this).attr('data-level'));
        x = e.offsetX;
        y = e.offsetY;
        name = String(level)+':'+String(x)+':'+String(y);

        var mapinput = $(this).parents('.mapinput');
        mapinput.hide();
        mapinput.parent().find('.locationinput, .buttons').show().focus();

        var location = $(this).parents('.p').find('button.user');
        location.val(name);
        location.find('span').text('…');
        location.find('small').text(name);
        location.click();
        $.ajax({'type': 'GET', 'url': '/n'+String(level)+':'+String(x)+':'+String(y), 'success': function(data) {
            $('.location[value="'+String(data.name)+'"] span').text(data.title);
        }, 'dataType': 'json'});
    });
    $('.maplevelselect button[data-level]').click(function() {
        var mapinput = $(this).parents('.p').find('.mapinput');
        mapinput.find('button').removeClass('pure-button-active');
        mapinput.find('img').hide();
        mapinput.parent().find('button[data-level='+$(this).attr('data-level')+']').addClass('pure-button-active');
        mapinput.find('img[data-level='+$(this).attr('data-level')+']').show();
        mapinput.find('.pos').toggle(mapinput.find('.pos').attr('data-level') == $(this).attr('data-level'));
    });
    $('.maplevelselect button.abort').click(function() {
        var mapinput = $(this).parents('.p').find('.mapinput');
        mapinput.hide();
        mapinput.siblings('.maplevelselect').hide();
        mapinput.parent().find('.locationinput, .buttons').show().focus();
    });
    $('button.location').attr('tabIndex', '-1').click(function(e) {
        e.preventDefault();
        $(this).parents('.selector').siblings('form').remove();
        $('<form>').html(
            $('<div class="location">').toggleClass('locating', $(this).is('.locating')).html($(this).html()).attr('value', $(this).val()).append($('<div class="buttons">').append(
                $(this).is(':not(.locating)') ? $('<a class="link">').attr('href', '/'+$(this).parents('.p').attr('name')+$(this).val()).click(linkbtn_click) : null
            ).append(
                $('<button type="submit" class="reset">')
            ))
        ).insertBefore($(this).parents('.selector'));
        $(this).parents('.p').addClass('selected').toggleClass('locating', $(this).is('.locating'));
        if (!$(this).is('.locating')) {
            $('input[type=hidden][name='+$(this).parents('.p').attr('name')+']').val($(this).val());
        } else {
            mobileclient.scanNow();
        }
        point_set();
        if ($('.locationinput:visible').first().focus().length && $(window).width()<568) {
            $('html, body').animate({ scrollTop: $('.locationinput:visible').first().parents('fieldset').offset().top-5 }, 300);
        }
    }).mouseover(function(e) {
        $(this).addClass('active').siblings('.active').removeClass('active');
    });
    $('.p').on('click', '.location .reset', function(e) {
        e.preventDefault();
        $(this).parents('.p').find('.location').hide();
        var f = $(this).parents('.p').removeClass('selected').removeClass('locating').find('.locationinput').val('').focus();
        if ($(window).width()<568) {
            $('html, body').animate({ scrollTop: f.offset().top-5 }, 300);
        }
        $('input[type=hidden][name='+$(this).parents('.p').attr('name')+']').val('');
        $(this).parents('form').remove();
        $('.locationinput').not(this).dequeue();
        point_set();
    });
    $('#s').hide();
    $('#mainform').append($('<input type="hidden" name="ajax" value="1">')).submit(function(e) {
        e.preventDefault();
        update_history();
        $('#routeresult').html('<div style="text-align:center;padding-top:15px;"><img src="/static/img/load.gif"></div>');
        $.ajax({'type': 'POST', 'url': $(this).attr('action'), 'data': $(this).serialize(), 'success': function(data) {
            var html = $(data);
            var hbefore = $('body').height();
            var sbefore = $('html, body').scrollTop();
            $('#s').hide();
            $('html, body').scrollTop(sbefore-(hbefore-$('body').height()));
            $('#editsettings').show();
            $('#savesettings').hide();
            $('#settingsdesc').show().html(html.first().html());
            $('#routeresult').html(html.last().html()).addClass('routeresult');
            if ($(window).width()<568) {
                $('html, body').animate({ scrollTop: $('.parts').offset().top-10 }, 800);
            }
        }, 'error': function() {
            $('#routeresult').html($('<div class="message error">').text($('#main').attr('data-locale-error')));
            if ($(window).width()<568) {
                $('html, body').animate({ scrollTop: $('.parts').offset().top-10 }, 800);
            }
        }, 'dataType': 'html'});
    });
    $('<button class="pure-button" id="editsettings">').text($('#main').attr('data-locale-edit-s')).insertBefore('#main-submit').click(function(e) {
        e.preventDefault();
        show_settings = true;
        $('#s').show();
        $('#settingsdesc').hide();
        $(this).hide();
        point_set();
    });
    $('.locationinput:visible').first().focus();
    point_set();
    if (typeof mobileclient !== "undefined") {
        if (wifilocate) {
            $('.p:not(.selected)').first().find('.locate').click();
        }
        nearby_stations_available();
    }
    if ($('#routeresult.routeresult').length > 0 && $(window).width()<768 && $('html, body').scrollTop() === 0) {
        $('html, body').delay(300).animate({ scrollTop: $('.parts').offset().top-10 }, 800);
    }
    $('.buttons a.link').each(function() {
        $(this).attr('href', $(this).attr('href').replace('/link', ''));
    }).click(linkbtn_click);
    $('#s select, #s input').change(update_history).click(update_history);
    $('.p[name=d] legend').append($('<button id="swapbtn" class="pure-button">').text($('#main').attr('data-locale-swap')).click(function() {
        origin = $('.p[name=o]').is('.selected') ? $('[type=hidden][name=o]').val() : null;
        destination = $('.p[name=d]').is('.selected') ? $('[type=hidden][name=d]').val() : null;
        if (origin !== null) toggle_user_location($('.p[name=d]').find('button.user'), origin);
        if (destination !== null) toggle_user_location($('.p[name=o]').find('button.user'), destination);
        $('.p[name=d]').find((origin !== null) ? ('button.location[value="'+origin+'"]') : '.reset').click();
        $('.p[name=o]').find((destination !== null) ? ('button.location[value="'+destination+'"]') : '.reset').click();
    }));
});
