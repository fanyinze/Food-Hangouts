// Create an array of object which includes U of T buildings location info
// Recommend to use a database and serve the info to the site. For details, go to Lesson 7 - Window Shopping Part1

function myFunc(vars) {
    return vars
}

// Map initialization
var map;

// Create a new blank array for all the listing markers.
var markers = [];

function googleError() {
	alert("Could not load Google Map. Please check console for details.");
}

function initMap() {
  // Create the style array, mapstyle available at https://snazzymaps.com/style/47/nature
  var styledMapType = new google.maps.StyledMapType(
  [
      {
          "featureType": "landscape",
          "stylers": [
              {
                  "hue": "#FFA800"
              },
              {
                  "saturation": 0
              },
              {
                  "lightness": 0
              },
              {
                  "gamma": 1
              }
          ]
      },
      {
          "featureType": "road.highway",
          "stylers": [
              {
                  "hue": "#53FF00"
              },
              {
                  "saturation": -73
              },
              {
                  "lightness": 40
              },
              {
                  "gamma": 1
              }
          ]
      },
      {
          "featureType": "road.arterial",
          "stylers": [
              {
                  "hue": "#FBFF00"
              },
              {
                  "saturation": 0
              },
              {
                  "lightness": 0
              },
              {
                  "gamma": 1
              }
          ]
      },
      {
          "featureType": "road.local",
          "stylers": [
              {
                  "hue": "#00FFFD"
              },
              {
                  "saturation": 0
              },
              {
                  "lightness": 30
              },
              {
                  "gamma": 1
              }
          ]
      },
      {
          "featureType": "water",
          "stylers": [
              {
                  "hue": "#00BFFF"
              },
              {
                  "saturation": 6
              },
              {
                  "lightness": 8
              },
              {
                  "gamma": 1
              }
          ]
      },
      {
          "featureType": "poi",
          "stylers": [
              {
                  "hue": "#679714"
              },
              {
                  "saturation": 33.4
              },
              {
                  "lightness": -25.4
              },
              {
                  "gamma": 1
              }
          ]
      }
  ],
  {name: "Styled Map"});

  // Constructor creates a new map - only center and zoom are required.
  // Create a map instance, need to specify where to put the map and which part of the world to show
  map = new google.maps.Map(document.getElementById("map"), {
    center: {lat: 43.7629, lng: -79.3957},
    zoom: 12, // How much detail need to show, maximum 21
    mapTypeControlOptions: {
      mapTypeIds: ['roadmap', 'satellite', 'hybrid', 'terrain',
              'styled_map']
    }
  });

  //Associate the styled map with the MapTypeId and set it to display.
  map.mapTypes.set('styled_map', styledMapType);
  map.setMapTypeId('styled_map');
  ko.applyBindings(new ViewModel());
}

var Building = function(data){
  //Since this data isn't refreshed dynamically/interactively, we can set these values to be static
  var self = this;
  self.title = ko.observable(data.title);
  self.location = ko.observable(data.location);
  self.address_street = data.address_street;
  self.address_city = data.address_city;
  self.address_postal = data.address_postal;
};

//View Model
var ViewModel = function() {
  var self = this;
  self.buildingList = ko.observableArray([]);
  var bounds = new google.maps.LatLngBounds();
  Model.forEach(function(item){
    self.buildingList.push(new Building(item));
  });

  // Set the current location by clicking list
	self.currentBuilding = ko.observable(self.buildingList()[0]);

	self.setBuilding = function(clickedBuilding) {
		self.currentBuilding(clickedBuilding);
    for (var i = 0; i < markers.length; i++) {
			if (clickedBuilding.title() == markers[i].title) {
        markers[i].setMap(map);
        bounds.extend(markers[i].position);
				populateInfoWindow(markers[i], largeInfowindow);
			}
      else{
        markers[i].setMap(map);
      }
		}
	};

  // Filtering functions
  self.userInput = ko.observable('');

  self.filterMarker = ko.computed(function() {
    var result = self.userInput().toLowerCase();
    for (var i = 0; i < self.buildingList().length; i++) {
      if (self.buildingList()[i].title().toLowerCase().indexOf(result) > -1) {
        for (var j = 0; j < markers.length; j++) {
          if (self.buildingList()[i].title() == markers[j].title) {
            markers[j].setMap(map);
          }
        }
      }else {
        for (var k = 0; k < markers.length; k++) {
          if (self.buildingList()[i].title() == markers[k].title) {
					  markers[k].setMap(null);
         }
       }
     }
   }
   if (!result){
     for (var n = 0; n < markers.length; n++) {
        markers[n].setMap(map);
      }
      return self.buildingList();
   } else {
     return ko.utils.arrayFilter(self.buildingList(), function(item) {
       return item.title().toLowerCase().indexOf(result) > -1;
 			});
		}
 });

  var largeInfowindow = new google.maps.InfoWindow();

  // Style the markers a bit. This will be our listing marker icon.
  var defaultIcon = makeMarkerIcon('0091ff');

  // Create a "highlighted location" marker color for when the user
  // mouses over the marker.
  var highlightedIcon = makeMarkerIcon('FFFF24');

  //function that handles infowindow population when marker get clicked
  var infoMarkerClick = function() {
    populateInfoWindow(this, largeInfowindow);
  };

  //function that handles animation when mouse is on the marker
  var animationMarkerClick = function() {
    this.setIcon(defaultIcon);
    if (this.getAnimation() !== null) {
      this.setAnimation(null);
    } else {
      this.setAnimation(google.maps.Animation.BOUNCE);
    }
  };
  //function that stops animation when mouse is removed from marker
  var animationStopMarkerClick = function() {
    this.setIcon(defaultIcon);
    if (this.getAnimation() !== null) {
      this.setAnimation(null);
    }
  };

  // The following group uses the location array to create an array of markers on initialize.
  for (var i = 0; i < Model.length; i++) {
    // Get the position from the location array.
    var position = Model[i].location;
    var title = Model[i].title;
    var address_street = Model[i].address_street;
    var address_city = Model[i].address_city;
    var address_postal =Model[i].address_postal;
    // Create a marker per location, and put into markers array.
     var marker = new google.maps.Marker({
      position: position,
      map: map,
      title: title,
      address_street: address_street,
      address_city: address_city,
      address_postal: address_postal,
      animation: google.maps.Animation.DROP,
      icon: defaultIcon,
      id: i
    });


    // Push the marker to our array of markers.
    markers.push(marker);
    // Create an onclick event to open an infowindow at each marker.
    marker.addListener('click', infoMarkerClick);

    //Set marker animation when mouse points on marker
    //marker.addListener('click', animationMarkerClick);

    //Stop animation when mouse moves away from marker
    marker.addListener('mouseout', animationStopMarkerClick);
  }

  if (markers.length>0) {
    for(i=0;i<markers.length;i++) {
       bounds.extend(markers[i].getPosition());
        }
     map.fitBounds(bounds);
    }
  else{
     map.setCenter({lat: 43.7629, lng: -79.3957});
  }

  // This function takes in a COLOR, and then creates a new marker
  // icon of that color. The icon will be 21 px wide by 34 high, have an origin
  // of 0, 0 and be anchored at 10, 34).
  function makeMarkerIcon(markerColor) {
    var markerImage = new google.maps.MarkerImage(
      'http://chart.googleapis.com/chart?chst=d_map_spin&chld=1.15|0|'+ markerColor +
      '|40|_|%E2%80%A2',
      new google.maps.Size(21, 34),
      new google.maps.Point(0, 0),
      new google.maps.Point(10, 34),
      new google.maps.Size(21,34));
    return markerImage;
  }

  // Function that makes a marker bounce once only
  function markerBounce(marker) {
		if (marker.getAnimation() !== null) {
			marker.setAnimation(null);
		} else {
		    marker.setIcon(defaultIcon);
			marker.setAnimation(google.maps.Animation.BOUNCE);
			setTimeout(function() {
				marker.setAnimation(null);
			}, 700);
		}
	}

  // This function populates the infowindow when the marker is clicked. We'll only allow
  // one infowindow which will open at the marker that is clicked, and populate based
  // on that markers position.
  function populateInfoWindow(marker, infowindow) {
    // Check to make sure the infowindow is not already opened on this marker.
        if (infowindow.marker != marker) {
          infowindow.marker = marker;
          // Make sure the marker property is cleared if the infowindow is closed.
          infowindow.addListener('closeclick', function() {
            infowindow.marker = null;
          });

          //Setup loading indicator when the marker gets clicked
          //infowindow.open(map, marker);

        // Create a new streetview object, get image based on closest location to marker
        var streetViewService = new google.maps.StreetViewService();
        // Within radius of 50 meters of marker
        var radius = 50;
        // In case the status is OK, which means the pano was found, compute the
        // position of the streetview image, then calculate the heading, then get a
        // panorama from that and set the options
        function getStreetView(data, status) {
          if (status == google.maps.StreetViewStatus.OK) {
            var nearStreetViewLocation = data.location.latLng;
            var heading = google.maps.geometry.spherical.computeHeading(
              nearStreetViewLocation, marker.position);
            console.log(marker.address_city)
              infowindow.setContent('<div style="font-weight: bold;">' + marker.title + '</div>' +
                                    '<div style="font-style: italic;">' + marker.address_street + '</br>' + marker.address_city + '</br>' + marker.address_postal + '</div>' +
                                    '<div id="pano"></div>');

            var panoramaOptions = {
              position: nearStreetViewLocation,
              pov: {
                heading: heading,
                pitch: 15
              }
            };
            var panorama = new google.maps.StreetViewPanorama(
              document.getElementById('pano'), panoramaOptions);
          } else {
            infowindow.setContent('<div>Name: ' + marker.title + '</div>' + '<div>Building Info: ' + '</div>' +
              '<div>No Street View Found</div>');
          }
        }
            // Use streetview service to get the closest streetview image within
            // 50 meters of the markers position
            streetViewService.getPanoramaByLocation(marker.position, radius, getStreetView);
            // Open the infowindow on the correct marker.
            markerBounce(marker);
            infowindow.open(map, marker);
            // Clear error handling timer
          }
      }


  // This function will loop through the markers array and display them all.
  //Code from Udacity course gettng star with api
  self.showListings = function(){
    var bounds = new google.maps.LatLngBounds();
    // Extend the boundaries of the map for each marker and display the marker
    for (var i = 0; i < markers.length; i++) {
      markers[i].setMap(map);
      bounds.extend(markers[i].position);
    }
    map.fitBounds(bounds);
    if (map.getZoom() > 15) {
    map.setZoom(15);
    }
  };

  // This function will loop through the listings and hide them all.
  //Code from Udacity course gettng star with api
  self.hideListings = function() {
    for (var i = 0; i < markers.length; i++) {
      markers[i].setMap(null);
    }
  };
};
