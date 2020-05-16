const btn=document.getElementById("btn1");
const input_place=document.getElementById("place");
const input_days=document.getElementById("days");
const mapDiv=document.getElementById("mapDiv");
const map=document.getElementById("map");
const tbody=document.getElementById('tbody');
const tableDiv=document.getElementById("tableDiv");
const loading=document.getElementById("loading");
let mymap;
// Display Places
const displayPlaces=(places)=>{
    tableDiv.style.display="block"
    tbody.innerHTML="";
    places.forEach(ele=>{
        const tr=document.createElement("tr")
        tr.innerHTML=`
        <td>${ele.day}</td>
        <td>${ele.title}</td>
        <td>${ele.coordinates[0]}</td>
        <td>${ele.coordinates[1]}</td>
        `
        tbody.appendChild(tr)
    })
}


// Plot Map
const plotMap=(places)=>{
    mapDiv.style.display="block"
    // Access Token
    let accessToken="pk.eyJ1IjoiamF5cGFqamkiLCJhIjoiY2thNnpuaW85MDR6OTJwbXpiajhtaXdhZiJ9.uW0aB84Ow8lWrqmiaPORMw"
    // Maps
    if(mymap!==undefined){
        mymap.remove()
    }
    mymap = L.map('map').setView(places[0].coordinates, 15);
    // Tile
    L.tileLayer(`https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token=${accessToken}`, {
        attribution: `Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, <a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>`,
        maxZoom: 18,
        id: 'mapbox/streets-v11',
        tileSize: 512,
        zoomOffset: -1,
        accessToken: accessToken
}).addTo(mymap);

places.forEach(ele=>{
    let marker=L.marker(ele.coordinates).addTo(mymap)
    marker.on('mouseover', function(e) { 
        tooltipPopup = L.popup({ offset: L.point(0, -50)});
                tooltipPopup.setContent(`Day:${ele.day}-${ele.title}`);
                tooltipPopup.setLatLng(e.target.getLatLng());
                tooltipPopup.openOn(mymap);
        });
    
        marker.on('mouseout', function(e) { 
            mymap.closePopup(tooltipPopup);
        });
    })

    // Sorting places on basis of day of visit
    places.sort((a,b)=>a.day - b.day)

    // End loading 
    loading.style.display="none"
    // Call to display the itinary table
    displayPlaces(places)
}


const formatData=(data)=>{
    
    let places=[];
    const {day_of_travel,latitude,longitude,title} = data 
    for(var i=0;i<latitude.length;i++){
        places.push({
            day:day_of_travel[i],
            coordinates:[latitude[i],longitude[i]],
            title:title[i]
        })
    }

    plotMap(places)

}

const getResponse=async(data)=>{
    const formData = new FormData();
    formData.append('days',data.days);
    formData.append("location",data.place)

    const url="https://touristbot-jd.herokuapp.com//generate";
    const config={
        method:"POST",
        body:formData
    }
    try{
        const response = await fetch(url,config)
        const data=await response.json()
        formatData(data)
    }
    catch(err){
        loading.style.display="none";
        alert("Sorry could not process your request...")
        console.log(err)
    }
}

const TakeInput=(e)=>{
    e.preventDefault()

    // Clear the already rendered data
    map.innerHTML=""
    mapDiv.style.display="none"
    tbody.innerHTML=""
    tableDiv.style.display="none"
    // Show Loading
    loading.style.display="block";
    
    if(input_days.value!=="" && input_place.value!==""){
        getResponse({place:input_place.value,days:input_days.value})
    }
    else{
        loading.style.display="none"
        alert("Plese Provide all details...")
    }
}

btn.addEventListener("click",TakeInput)