mobileclient = {
    nearbyStations: '[]',
    setNearbyStations: function(data) {
        this.nearbyStations = data;
        nearby_stations_available();
    },
    getNearbyStations: function() {
        return this.nearbyStations;
    },
    scanNow: function() {
        console.log('scanNow');
        $.ajax({'type': 'GET', 'url': 'http://localhost:4999/scan', 'success': function(data) {
            mobileclient.setNearbyStations(data.data);
        }, 'dataType': 'json'});
    },
    shareUrl: function(url) {
        console.log('sharing url: '+url);
    },
    createShortcut: function(url, title) {
        console.log('shortcut url: '+url+' title: '+title);
    }
};
