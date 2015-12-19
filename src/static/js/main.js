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
        active = locations.each(function() {
            $(this).hide().toggle($(this).text().toLowerCase().indexOf(value)>-1 || $(this).val().indexOf(value)>-1);
        }).removeClass('active').filter(':visible').first().addClass('active');
        if (active.is(':first-child')) active.parent().scrollTop(0);
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
    var cansubmit = ($('.p:not(.selected)').length === 0);
    $('#main-submit').prop('disabled', !cansubmit);
    $('#savesettings').toggle(show_settings);
    if (!cansubmit) $('#savesettings').prop('checked', show_settings);
}
function nearby_stations_available() {
    console.log(JSON.parse(mobileclient.getNearbyStations()));
    $('.locating').remove();
    $('.located').addClass('ready');
}
function linkbtn_click(e) {
    e.preventDefault();
    e.stopPropagation();
    $('#linkmodal').remove();
    $('body').append(
        $('<div id="linkmodal">').css({
            'width': 290, 'z-index': 9001, 'padding-bottom': 20, 'position': 'absolute', 'top': '15px', 'left': '50%',
            'margin-left': -145, 'background-color': '#FFFFFF', 'box-shadow': '0px 0px 5px 0px rgba(0,0,0,0.75)', 'text-align': 'center'
        }).append(
            $('<img>').attr('src', '/qr'+$(this).attr('href'))
        ).append(
            $('<strong>').text('https://'+location.host+$(this).attr('href')).css('display', 'block').css('margin-bottom', 15)
        ).append(
            $('<button class="pure-button">').text('close').click(function() {$('#linkmodal').remove();})
        )
    );
}
$(document).ready(function() {
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
            'placeholder': ($(this).parents('.p').attr('name') == 'o') ? 'Enter any location' : 'select destination…'
        }).keyup(keyup_complete).focus(keyup_complete).focus(function() {
            $('.locationinput').not(this).dequeue();
        }).blur(function() {
            $(this).queue(function(n) {
                    $(this).val(''); $(this).parent().find('.location').hide();
                n();
            });
        });
        var buttons = $('<div class="buttons">');/*.append(
            $('<button class="map">')
        );*/
        if ($('body').is('.mobile-client')) {
            buttons.prepend(
                $('<button class="locating">')
            ).prepend(
                $('<button class="located">')
            );
        }
        buttons.insertBefore(this);
    });
    $('button.location').attr('tabIndex', '-1').click(function(e) {
        e.preventDefault();
        $(this).parents('.selector').siblings('form').remove();
        $('<form>').html(
            $('<div class="location">').html($(this).html()).append($('<div class="buttons">').append(
                $('<a class="link">').attr('href', '/'+$(this).parents('.p').attr('name')+$(this).val()).click(linkbtn_click)
            ).append(
                $('<button type="submit" class="reset">')
            ))
        ).insertBefore($(this).parents('.selector'));
        $(this).parents('.p').addClass('selected');
        $('input[type=hidden][name='+$(this).parents('.p').attr('name')+']').val($(this).val());
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
        var f = $(this).parents('.p').removeClass('selected').find('.locationinput').val('').focus();
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
            $('#routeresult').html('<div class="message error">Sorry, an error occured =(</div>');
            if ($(window).width()<568) {
                $('html, body').animate({ scrollTop: $('.parts').offset().top-10 }, 800);
            }
        }, 'dataType': 'html'});
    });
    $('<button class="pure-button" id="editsettings">Edit Settings</button>').insertBefore('#main-submit').click(function(e) {
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
        nearby_stations_available();
    }
    if ($('#routeresult.routeresult').length > 0 && $(window).width()<768 && $('html, body').scrollTop() === 0) {
        $('html, body').delay(300).animate({ scrollTop: $('.parts').offset().top-10 }, 800);
    }
    $('.buttons a.link').each(function() {
        $(this).attr('href', $(this).attr('href').replace('/link', ''));
    }).click(linkbtn_click);
    $('#s select, #s input').change(update_history).click(update_history);
    $('.p[name=d] legend').append($('<button id="swapbtn" class="pure-button">').text('swap').click(function() {
        origin = $('.p[name=o]').is('.selected') ? $('[type=hidden][name=o]').val() : null;
        destination = $('.p[name=d]').is('.selected') ? $('[type=hidden][name=d]').val() : null;
        $('.p[name=d]').find((origin !== null) ? ('button.location[value='+origin+']') : '.reset').click();
        $('.p[name=o]').find((destination !== null) ? ('button.location[value='+destination+']') : '.reset').click();
    }));
});
