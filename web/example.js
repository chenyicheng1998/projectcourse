'use strict';

// Load the map
// const map = L.map('map').setView([1.35019, 103.994003], 4, ); //set view in Singapore Lat+Lon
const earth = new WE.map('earth');
earth.setView([1.35019, 103.994003], 4, {animate: true, duration: 0.5});

// L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
//   attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
// }).addTo(map);
WE.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(earth);

const port = 3001;

let currentAirportMarkers = [];
let templateAirportMarkers = [];
let routeAirportMarkers = [];
let polygon = [];
let prevAirportPosition = [];
let clickedAirportPosition = [];


async function create_player(player) {
  let response = await fetch(
      `http://127.0.0.1:${port}/create_player/` + player);
  let data = await response.json();
  console.log(
      `add player: ${data.player}, number_of_play = ${data.number_of_play}`);
  let number_of_play = data.number_of_play;
  let player_id = data.player_id;
  return {player_id, number_of_play};
}

async function get_current_airport(player, number_of_play) {
  let response = await fetch(
      `http://127.0.0.1:${port}/get_current_airport/` + player + `/` +
      number_of_play);
  let data = await response.json();
  let current_airport_ident = data.airport_ident;

  response = await fetch(`http://127.0.0.1:${port}/get_current_airport_info/` +
      current_airport_ident);
  let current_airport_data = await response.json();
  current_airport_data = current_airport_data[0];
  // console.log('HERE');
  // console.log(current_airport_data);
  return current_airport_data;
}

async function get_near_airport_data(current_airport_data) {
  let response = await fetch(`http://127.0.0.1:${port}/get_near_airport_data/` +
      current_airport_data.ident);
  let near_airport_data = await response.json();
  return near_airport_data;
}

async function refresh_new_marker(player_id, player, number_of_play) {
  // 1. delete old markers
  templateAirportMarkers.forEach(marker => {
    // if (marker.element.parentNode) {
    //   marker.element.parentNode.removeChild(marker.element);
    // }
    marker.removeFrom(earth);
  });
  templateAirportMarkers.length = 0;

  // 2. get current airport
  let current_airport_data = await get_current_airport(player, number_of_play);

  // 3. find airports near current airport
  let near_airport_data = await get_near_airport_data(current_airport_data);

  // 4. add and show markers. Also add matadata
  //         ident: near_airport_data[i].ident,
  //         name: near_airport_data[i].name,
  for (let i = 0; i < near_airport_data.length; i++) {
    templateAirportMarkers.push(WE.marker([
          near_airport_data[i].latitude_deg,
          near_airport_data[i].longitude_deg],
        ).addTo(earth)
    );
    templateAirportMarkers[i].bindPopup(near_airport_data[i].name).closePopup();
    templateAirportMarkers[i].metadata = {
      name: near_airport_data[i].name,
      ident: near_airport_data[i].ident,
      distance: near_airport_data[i].distance,
    };
  }

  // 5. set the view center to current airport
  // earth.setView([9.35019, 93.994003], 4, {animate: true,duration: 0.5});

  // 6. add markers event listener
  // templateAirportMarkers.on('click', function(e) {
  //   console.log(`You clicked on marker at ${e.latlng.lat}, ${e.latlng.lng}`);
  // });
  for (let i = 0; i < templateAirportMarkers.length; i++) {
    templateAirportMarkers[i].element.addEventListener('click', async () => {
      // CLICKED!
      let next_airport_ident = templateAirportMarkers[i].metadata.ident;
      let current_airport_ident = current_airport_data.ident;
      let distance = templateAirportMarkers[i].metadata.distance;

      let weather_condition = ""
      try {
          let response = await fetch(`http://127.0.0.1:${port}/get_weather/` + next_airport_ident);
          let weatherData = await response.json();
          console.log(weatherData)
          const city_name = weatherData['name']
          weather_condition = weatherData['weather'][0]['main']
          const temperature = weatherData['main']['temp']

          document.getElementById("weather").innerHTML = `Weather at ${city_name}: ${weather_condition}, ${temperature}°C`;
      }
      catch (e){
        console.log(e)
        weather_condition = 'Clear'
        document.getElementById("weather").innerHTML = `Cannot get weather, but just fly.`;
      }
      const goodWeather = ['Clear', 'Clouds', 'Rain', 'Drizzle']
      // const badWeather = ['Thunderstorm', 'Snow', 'Mist', 'Smoke', 'Haze', ]

      if(goodWeather.includes(weather_condition)){


                            // 1. update clicked airport, just in player database
                            await fetch(`http://127.0.0.1:${port}/update_clicked_airport/` +
                                next_airport_ident + `/` + player + `/` + number_of_play);

                            // 2. update sequence database
                            let response = await fetch(
                                `http://127.0.0.1:${port}/update_sequence/` + current_airport_ident +
                                `/` +
                                next_airport_ident + `/` + distance);
                            let data = await response.json();
                            let seq_id = data[0]

                            // 3. update player_seq
                            await fetch(
                                `http://127.0.0.1:${port}/update_player_seq/` + player_id + `/` +
                                seq_id);

                            // 4. show clicked marker
                            // 4.1 get clicked airport
                            let clicked_airport_data = await get_current_airport(player, number_of_play);
                            console.log(clicked_airport_data);

                            // 4.2 show the clicked airport
                            // 4.2.1 delete
                            currentAirportMarkers.forEach(marker => {
                              if (marker.element.parentNode) {
                                marker.element.parentNode.removeChild(marker.element);
                              }
                            });
                            currentAirportMarkers.length = 0;
                            // 4.2.2 show
                            currentAirportMarkers.push(WE.marker([clicked_airport_data.latitude_deg, clicked_airport_data.longitude_deg]).
                                addTo(earth).
                                bindPopup(clicked_airport_data.name));

                            // 5. show route marker
                            routeAirportMarkers.push(WE.marker([clicked_airport_data.latitude_deg, clicked_airport_data.longitude_deg]).
                                addTo(earth).
                                bindPopup(clicked_airport_data.name));
                            clickedAirportPosition = [clicked_airport_data.latitude_deg, clicked_airport_data.longitude_deg]
                            console.log(prevAirportPosition)
                            console.log(clickedAirportPosition)
                            polygon.push(WE.polygon([prevAirportPosition, clickedAirportPosition,prevAirportPosition],{
                                color: '#f00',
                                opacity: 1,
                                fillColor: '#f00',
                                fillOpacity: 1,
                                editable: false,
                                weight: 5
                              }).addTo(earth))
                            prevAirportPosition = [clicked_airport_data.latitude_deg, clicked_airport_data.longitude_deg]
                            response = await fetch(
                                `http://127.0.0.1:${port}/check_is_game_finished/` + player_id);

                            let is_game_finished = await response.json();
                            // console.log("!!!is_game_finished: ")
                            // console.log(is_game_finished);


                            if (is_game_finished[0] !== 0 ) {
                              let total_distance = is_game_finished[0];
                                await fetch(`http://127.0.0.1:${port}/insert_ranking_record/` + player_id+`/`+total_distance);
                                //delete the extra points
                                templateAirportMarkers.forEach(marker => {
                                  marker.removeFrom(earth);
                                });
                                templateAirportMarkers.length = 0;

                                // show the ranking table
                                alert ("You Finished the Game!!!");
                                response = await fetch(`http://127.0.0.1:${port}/get_ranking_table`);
                                let ranking_table = await response.json();
                                console.log(ranking_table)


                                let html = "<table border='1' style='border-collapse:collapse;'>";
                                html += "<tr><th>Player ID</th><th>Player</th><th>Total Distance</th></tr>";
                                ranking_table.forEach(row => {
                                  html += `<tr>
                                            <td>${row.player_id}</td>
                                            <td>${row.player}</td>
                                            <td>${row.total_distance}</td>
                                          </tr>`;
                                });
                                html += "</table>";
                                document.getElementById("rankingTable").innerHTML = html;

                            }
                            else{
                              await refresh_new_marker(player_id, player, number_of_play);
                            }
      }
      else{
        alert(`Weather Bad: ${weather_condition}! Cannot landing! Please choose another airport!`)
      }
    });
  }


}

document.addEventListener('DOMContentLoaded', async function() {

// the line container
  // const lines = WE.layerGroup().addTo(map);
// Define the coordinates for the line
// const line = [];

// Show Singapore on the map
  // const marker = L.marker([1.35019, 103.994003]).
  //                 addTo(map).
  //                 bindPopup('Singapore Changi Airport');
  //                 //openPopup();
  // singaporeAirportMarkers.addLayer(marker);
  currentAirportMarkers.push(WE.marker([1.35019, 103.994003]).
      addTo(earth).
      bindPopup('Singapore Changi Airport'));
  routeAirportMarkers.push(WE.marker([1.35019, 103.994003]).
      addTo(earth).
      bindPopup('Singapore Changi Airport'));
  prevAirportPosition = [1.35019, 103.994003];
  // const routeLayerGroup = L.layerGroup().addTo(map);

  //Table for adding players
  async function handleSubmit(event) {
    event.preventDefault();
    let player = document.getElementById('player').value;
    let {player_id, number_of_play} = await create_player(player);
    // alert(
    //     `Welsome! ${player}, this your ${number_of_play} attempt! Your player id: ${player_id}`);

    // Prevent re-submit the form
    form.removeEventListener('submit', handleSubmit);

    //   templateAirportMarkers.clearLayers();
    //   for (let i = 0; i < near_airport_data.length;i++ ) {
    //     // console.log(near_airport_data[i])
    //     const marker = L.marker([near_airport_data[i].latitude_deg, near_airport_data[i].longitude_deg]).
    //       addTo(map).
    //       bindPopup(near_airport_data[i].name);
    //       //openPopup();
    //     templateAirportMarkers.addLayer(marker);
    //   }
    //   map.flyTo([current_airport_data.latitude_deg, current_airport_data.longitude_deg]);
    await refresh_new_marker(player_id, player, number_of_play);
  }

  const form = document.querySelector('form');
  form.addEventListener('submit', handleSubmit);
});



